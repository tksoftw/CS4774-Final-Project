from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional


class RMPReviewsStore:
    """
    Stores all reviews in ONE JSONL file and keeps an index for quick retrieval by tid.

    Files:
      - <base>.jsonl  : append-only, one JSON object per line
      - <base>_index.json : maps tid -> {"offsets": [byte_offsets], "count": int}

    NOTE: offsets list can grow large if you store many reviews.
    For most class projects this is totally fine.
    """

    def __init__(self, base_path: str):
        # base_path WITHOUT extension, e.g. app/data/cache/rmp_reviews_1277
        self.jsonl_path = base_path + ".jsonl"
        self.index_path = base_path + "_index.json"

        os.makedirs(os.path.dirname(self.jsonl_path), exist_ok=True)

        if os.path.exists(self.index_path):
            with open(self.index_path, "r", encoding="utf-8") as f:
                self.index: Dict[str, Dict[str, Any]] = json.load(f)
        else:
            self.index = {}

    def _save_index(self) -> None:
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(self.index, f, ensure_ascii=False)

    def has_reviews(self, tid: int) -> bool:
        return str(tid) in self.index and self.index[str(tid)].get("count", 0) > 0

    def append_reviews(self, tid: int, reviews: List[Dict[str, Any]]) -> None:
        """
        Append reviews for a professor to the JSONL file and update index.
        Each stored line includes tid so the JSONL file is self-contained.
        """
        tid_key = str(tid)
        entry = self.index.get(tid_key) or {"offsets": [], "count": 0}

        # open in binary so byte offsets are accurate
        with open(self.jsonl_path, "ab") as f:
            for r in reviews:
                # include tid in each record
                record = {"tid": tid, **r}
                line = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")

                offset = f.tell()
                f.write(line)

                entry["offsets"].append(offset)
                entry["count"] += 1

        self.index[tid_key] = entry
        self._save_index()

    def get_reviews_for_professor(self, tid: int, limit: int = 200) -> List[Dict[str, Any]]:
        """
        Read reviews for professor tid using stored byte offsets.
        """
        tid_key = str(tid)
        entry = self.index.get(tid_key)
        if not entry:
            return []

        offsets: List[int] = entry.get("offsets", [])
        if not offsets:
            return []

        out: List[Dict[str, Any]] = []
        with open(self.jsonl_path, "rb") as f:
            for off in offsets[:limit]:
                f.seek(off)
                line = f.readline()
                if not line:
                    continue
                try:
                    obj = json.loads(line.decode("utf-8"))
                except Exception:
                    continue
                # strip tid if you don’t want it in the returned review
                obj.pop("tid", None)
                out.append(obj)

        return out
