from __future__ import annotations

import base64
import os
from typing import Any, Dict, List, Optional

import requests

from .professor import Professor


class ProfessorNotFound(Exception):
    def __init__(self, search_argument: str, search_parameter: str = "Name"):
        self.search_argument = search_argument
        self.search_parameter = search_parameter

    def __str__(self) -> str:
        return (
            "Professor not found. "
            f"The search argument '{self.search_argument}' did not match "
            f"any professor's {self.search_parameter}."
        )


def _global_id(type_name: str, legacy_id: str | int) -> str:
    # base64("TypeName-<legacyId>"), e.g., base64("School-1277")
    raw = f"{type_name}-{legacy_id}"
    return base64.b64encode(raw.encode("utf-8")).decode("utf-8")


class RateMyProfApi:
    GRAPHQL_URL = "https://www.ratemyprofessors.com/graphql"

    def __init__(self, school_id: str = "1277", testing: bool = False):
        self.UniversityId = str(school_id)
        self.testing = testing

        folder = "SchoolID_" + self.UniversityId
        if not os.path.exists(folder):
            os.mkdir(folder)

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Content-Type": "application/json",
                "Origin": "https://www.ratemyprofessors.com",
                "Referer": "https://www.ratemyprofessors.com/",
                # common header used by working wrappers
                "Authorization": "Basic dGVzdDp0ZXN0",
            }
        )

        self.school_global_id = _global_id("School", self.UniversityId)

        # dict[int, Professor] keyed by legacyId
        self.professors: Dict[int, Professor] = self.scrape_professors(testing=self.testing)

    def _graphql(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        resp = self.session.post(
            self.GRAPHQL_URL,
            json={"query": query, "variables": variables},
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
        if "errors" in payload and payload["errors"]:
            raise RuntimeError(f"GraphQL errors: {payload['errors']}")
        return payload.get("data", {})

    def scrape_professors(self, testing: bool = False) -> Dict[int, Professor]:
        """
        Fetch ALL professors for the school by paging through GraphQL search results.
        """
        query = """
        query TeacherSearch($query: TeacherSearchQuery!, $after: String) {
          newSearch {
            teachers(query: $query, first: 50, after: $after) {
              edges {
                cursor
                node {
                  legacyId
                  firstName
                  lastName
                  avgRating
                  numRatings
                }
              }
              pageInfo { hasNextPage endCursor }
              resultCount
            }
          }
        }
        """

        teacher_query = {
            "text": "",  # empty text returns all teachers for school
            "schoolID": self.school_global_id,
            "fallback": True,
            "departmentID": None,
        }

        professors: Dict[int, Professor] = {}
        after: Optional[str] = None
        page_count = 0

        while True:
            data = self._graphql(query, {"query": teacher_query, "after": after})
            teachers_block = (data.get("newSearch") or {}).get("teachers") or {}
            edges = teachers_block.get("edges") or []

            for edge in edges:
                node = (edge or {}).get("node") or {}
                legacy_id = node.get("legacyId")
                if legacy_id is None:
                    continue

                tid = int(legacy_id)
                prof = Professor(
                    tid,
                    node.get("firstName", "") or "",
                    node.get("lastName", "") or "",
                    node.get("numRatings", 0) or 0,
                    node.get("avgRating", 0) or 0,
                )
                professors[tid] = prof

            page_info = teachers_block.get("pageInfo") or {}
            if not page_info.get("hasNextPage"):
                break

            after = page_info.get("endCursor")
            page_count += 1

            # Testing mode: only 2 pages (≈100 profs)
            if testing and page_count >= 1:
                break

        return professors

    def create_reviews_list(self, tid: int, max_pages: int = 2) -> List[Dict[str, Any]]:
        """
        Fetch review text + per-review metrics via GraphQL.
        Returns a list of dicts including:
        rClass, rComments, rDate, rEasy (difficulty), rClarity, rHelpful, rWouldTakeAgain
        """

        # Try "rich" query first (fields that often exist)
        rich_query = """
        query TeacherRatings($id: ID!, $after: String) {
        node(id: $id) {
            ... on Teacher {
            ratings(first: 50, after: $after) {
                edges {
                cursor
                node {
                    class
                    comment
                    date
                    difficultyRating
                    clarityRating
                    helpfulRating
                    wouldTakeAgain
                }
                }
                pageInfo { hasNextPage endCursor }
            }
            }
        }
        }
        """

        # Fallback if schema changes again
        minimal_query = """
        query TeacherRatings($id: ID!, $after: String) {
        node(id: $id) {
            ... on Teacher {
            ratings(first: 50, after: $after) {
                edges {
                cursor
                node {
                    class
                    comment
                    date
                    difficultyRating
                    wouldTakeAgain
                }
                }
                pageInfo { hasNextPage endCursor }
            }
            }
        }
        }
        """

        teacher_id = _global_id("Teacher", tid)
        reviews: List[Dict[str, Any]] = []
        after: Optional[str] = None
        page_count = 0

        # pick which query works once per professor
        query_to_use = rich_query
        tried_fallback = False

        while True:
            try:
                data = self._graphql(query_to_use, {"id": teacher_id, "after": after})
            except RuntimeError as e:
                # If the rich query fails due to unknown fields, fallback to minimal
                if (not tried_fallback) and ("Cannot query field" in str(e)):
                    query_to_use = minimal_query
                    tried_fallback = True
                    continue
                raise

            node = data.get("node") or {}
            ratings = node.get("ratings") or {}
            edges = ratings.get("edges") or []

            for edge in edges:
                r = (edge or {}).get("node") or {}
                reviews.append({
                    "rClass": r.get("class") or "",
                    "rComments": r.get("comment") or "",
                    "rDate": r.get("date"),
                    "rEasy": r.get("difficultyRating"),
                    "rClarity": r.get("clarityRating"),   # may be None if fallback query
                    "rHelpful": r.get("helpfulRating"),   # may be None if fallback query
                    "rWouldTakeAgain": r.get("wouldTakeAgain"),
                })

            page_info = ratings.get("pageInfo") or {}
            if not page_info.get("hasNextPage"):
                break

            after = page_info.get("endCursor")
            page_count += 1
            if page_count >= max_pages:
                break

        return reviews


    def get_professor_by_last_name(self, last_name: str) -> Professor:
        last_name = last_name.lower().strip()
        for prof in self.professors.values():
            if prof.last_name.lower() == last_name:
                return prof
        raise ProfessorNotFound(last_name, "Last Name")


if __name__ == "__main__":
    api = RateMyProfApi("1277", testing=False)
    print(f"Loaded professors: {len(api.professors)}")
    for i, p in enumerate(api.professors.values()):
        print(p.name, p.overall_rating, p.num_of_ratings)
        if i >= 4:
            break
