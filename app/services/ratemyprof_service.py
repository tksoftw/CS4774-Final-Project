from __future__ import annotations
from app.data.rmp_reviews_store import RMPReviewsStore

import json
import os
import re
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import requests

from app.external.ratemyprof_api import RateMyProfApi


class RateMyProfessorService:
    def __init__(
        self,
        school_id: str,
        testing: bool = True,
        cache_dir: Optional[str] = None,
        reviews_cache_ttl_seconds: int = 60 * 60 * 24 * 30,  # 30 days
    ):
        self.school_id = str(school_id)
        self.testing = testing
        self.reviews_cache_ttl_seconds = reviews_cache_ttl_seconds

        # put cache in app/data/cache by default
        if cache_dir is None:
            cache_dir = os.path.join("app", "data", "cache")
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

        base = os.path.join(self.cache_dir, f"rmp_reviews_{self.school_id}")
        self.reviews_store = RMPReviewsStore(base)

        self._api: Optional[RateMyProfApi] = None

    @property
    def api(self) -> RateMyProfApi:
        if self._api is None:
            self._api = RateMyProfApi(school_id=self.school_id, testing=self.testing)
        return self._api

    # ---------------- Normalization ----------------

    @staticmethod
    def _normalize_course(raw: Any) -> Optional[str]:
        """
        STRICT UVA-style courses only:
          LETTERS (2–4) + 4 digits -> "CS 1110"
        Everything else returns None.
        """
        if not raw or not isinstance(raw, str):
            return None

        s = raw.strip().upper()
        if not s:
            return None

        compact = s.replace(" ", "")

        m = re.match(r"^([A-Z]{2,4})(\d{4})$", compact)
        if not m:
            return None

        return f"{m.group(1)} {m.group(2)}"

    # ---------------- Cache paths ----------------

    def _course_map_path(self, max_pages: int) -> str:
        suffix = "testing" if self.testing else "full"
        return os.path.join(
            self.cache_dir,
            f"rmp_course_map_{self.school_id}_{suffix}_pages{max_pages}.json",
        )

    def _progress_path(self, max_pages: int) -> str:
        suffix = "testing" if self.testing else "full"
        return os.path.join(
            self.cache_dir,
            f"rmp_progress_{self.school_id}_{suffix}_pages{max_pages}.json",
        )

    def _reviews_cache_path(self, tid: int, max_pages: int) -> str:
        """
        Cache per professor. Include max_pages in the filename because it changes completeness.
        """
        suffix = "testing" if self.testing else "full"
        return os.path.join(
            self.reviews_cache_dir,
            f"rmp_reviews_{self.school_id}_{suffix}_tid{tid}_pages{max_pages}.json",
        )

    def _is_file_fresh(self, path: str, ttl_seconds: int) -> bool:
        if not os.path.exists(path):
            return False
        age = time.time() - os.path.getmtime(path)
        return age <= ttl_seconds

    # ---------------- Robust request wrapper ----------------

    def _get_reviews_with_retries(
        self,
        tid: int,
        max_pages: int,
        retries: int = 4,
        backoff: float = 1.6,
    ) -> List[Dict[str, Any]]:
        last_err: Optional[Exception] = None
        for attempt in range(retries):
            try:
                return self.api.create_reviews_list(tid, max_pages=max_pages)
            except (
                requests.Timeout,
                requests.ConnectionError,
                requests.HTTPError,
                RuntimeError,
            ) as e:
                last_err = e
                time.sleep(backoff ** attempt)
        raise last_err  # type: ignore

    # ---------------- NEW: per-professor review caching ----------------

    def get_reviews_for_professor_cached(
        self,
        tid: int,
        max_pages: int = 2,
        uva_only: bool = True,
        force_refresh: bool = False,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """
        Cache reviews for ALL professors into one JSONL file + index.

        - If cached and not force_refresh: return cached (fast).
        - Otherwise fetch from RMP, filter, append to JSONL, and return.
        """
        if not force_refresh and self.reviews_store.has_reviews(tid):
            return self.reviews_store.get_reviews_for_professor(tid, limit=limit)

        reviews = self._get_reviews_with_retries(tid, max_pages=max_pages)

        if uva_only:
            filtered: List[Dict[str, Any]] = []
            for r in reviews:
                norm = self._normalize_course(r.get("rClass"))
                if not norm:
                    continue
                r2 = dict(r)
                r2["rClass"] = norm
                filtered.append(r2)
            reviews = filtered

        # append to the single JSONL store
        professor = self.api.professors.get(tid)
        prof_name = professor.name if professor else "UNKNOWN"

        self.reviews_store.append_reviews(
            tid=tid,
            professor_name=prof_name,
            reviews=reviews,
        )


        return reviews[:limit]


    # ---------------- Course map builder (still available) ----------------

    def build_courses_with_professors_incremental(
        self,
        max_pages: int = 1,
        batch_size: int = 50,
        sleep_between_requests: float = 0.05,
        force_restart: bool = False,
    ) -> Dict[str, List[dict]]:
        course_map_path = self._course_map_path(max_pages)
        progress_path = self._progress_path(max_pages)

        # Load existing cache
        if os.path.exists(course_map_path) and not force_restart:
            with open(course_map_path, "r", encoding="utf-8") as f:
                course_map: Dict[str, List[dict]] = json.load(f)
        else:
            course_map = {}

        # Load progress
        if os.path.exists(progress_path) and not force_restart:
            with open(progress_path, "r", encoding="utf-8") as f:
                progress = json.load(f)
            processed: set[int] = set(progress.get("processed_tids", []))
        else:
            processed = set()

        course_map_dd: Dict[str, List[dict]] = defaultdict(list, course_map)
        professor_items = list(self.api.professors.items())

        # Find next batch
        to_process: List[Tuple[int, Any]] = []
        for tid, prof in professor_items:
            if tid in processed:
                continue
            to_process.append((tid, prof))
            if len(to_process) >= batch_size:
                break

        if not to_process:
            with open(course_map_path, "w", encoding="utf-8") as f:
                json.dump(dict(course_map_dd), f, ensure_ascii=False)
            return dict(course_map_dd)

        for tid, prof in to_process:
            if sleep_between_requests > 0:
                time.sleep(sleep_between_requests)

            try:
                reviews = self.get_reviews_for_professor_cached(
                    tid,
                    max_pages=max_pages,
                    uva_only=True,
                    force_refresh=False,
                )
            except Exception:
                processed.add(tid)
                continue

            seen_courses = set()
            for review in reviews:
                course = review.get("rClass")
                if not course or course in seen_courses:
                    continue
                seen_courses.add(course)

                already = any(
                    p.get("professor_name") == prof.name
                    for p in course_map_dd[course]
                )
                if already:
                    continue

                course_map_dd[course].append(
                    {
                        "professor_name": prof.name,
                        "overall_rating": prof.overall_rating,
                        "num_ratings": prof.num_of_ratings,
                    }
                )

            processed.add(tid)

            # Save mapping + progress
            with open(course_map_path, "w", encoding="utf-8") as f:
                json.dump(dict(course_map_dd), f, ensure_ascii=False)

            with open(progress_path, "w", encoding="utf-8") as f:
                json.dump({"processed_tids": sorted(processed)}, f, ensure_ascii=False)

        return dict(course_map_dd)

    def get_courses_with_professors(
        self,
        max_pages: int = 1,
        batch_size: int = 50,
    ) -> Dict[str, List[dict]]:
        return self.build_courses_with_professors_incremental(
            max_pages=max_pages,
            batch_size=batch_size,
            sleep_between_requests=0.05,
            force_restart=False,
        )

    def get_professors_for_course(
        self,
        course_code: str,
        max_pages: int = 1,
        batch_size: int = 50,
    ) -> List[dict]:
        norm = self._normalize_course(course_code)
        if not norm:
            return []

        mapping = self.get_courses_with_professors(max_pages=max_pages, batch_size=batch_size)
        return mapping.get(norm, [])
