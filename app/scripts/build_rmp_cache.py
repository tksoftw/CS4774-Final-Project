"""
Incrementally build the RateMyProfessor course cache.

Safe to run multiple times.
Stops and resumes automatically.
"""

import time
from app.services.ratemyprof_service import RateMyProfessorService


def main():
    # === CONFIG ===
    SCHOOL_ID = "1277"      # UVA
    TESTING = False         # False = full professor list
    MAX_PAGES = 1           # ratings pages per professor (keep small!)
    BATCH_SIZE = 50         # professors processed per run
    SLEEP_BETWEEN_RUNS = 2  # seconds between batches

    print("Starting RateMyProfessor cache builder")
    print(f"School ID: {SCHOOL_ID}")
    print(f"Batch size: {BATCH_SIZE}, Rating pages: {MAX_PAGES}")
    print("Press Ctrl+C to stop safely at any time.\n")

    service = RateMyProfessorService(
        school_id=SCHOOL_ID,
        testing=TESTING,
    )

    try:
        while True:
            course_map = service.get_courses_with_professors(
                max_pages=MAX_PAGES,
                batch_size=BATCH_SIZE,
            )

            print(f"Cache updated. Courses so far: {len(course_map)}")
            print("Sleeping before next batch...\n")
            time.sleep(SLEEP_BETWEEN_RUNS)

    except KeyboardInterrupt:
        print("\nStopped by user. Progress has been saved safely.")


if __name__ == "__main__":
    main()
