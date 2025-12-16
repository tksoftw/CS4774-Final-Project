"""Course data loading and indexing."""

import json
import time
from pathlib import Path
from typing import Optional
from app.config import get_settings
from app.course_clusters import get_course_clusters
from app.services.sis_service import SISService
from app.data.scrapers.tcf_scraper import scrape_course, BASE_URL  # Import the function
from app.data.vector_store import VectorStore


class CourseLoader:
    """Loads course data from SIS API and indexes into vector store."""
    
    def __init__(self):
        self.settings = get_settings()
        self.sis_service = SISService()
        self.vector_store = VectorStore()
        
        # Ensure data directory exists
        self.data_dir = Path(self.settings.data_dir) / "courses"
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def load_courses(
        self,
        term: str = "1252",
        subjects: Optional[list[str]] = None,
        force_refresh: bool = False,
    ) -> int:
        """Load courses from SIS API and index them.
        
        Args:
            term: Academic term code
            subjects: List of subjects to load (default: CS-related)
            force_refresh: Force re-fetch from API
            
        Returns:
            Number of courses indexed
        """
        cache_file = self.data_dir / f"courses_{term}.json"
        
        # Try to load from cache
        if not force_refresh and cache_file.exists():
            with open(cache_file, "r") as f:
                courses = json.load(f)
        else:
            # Fetch from API
            courses = self._fetch_courses(term, subjects)
            
            # Cache the results
            with open(cache_file, "w") as f:
                json.dump(courses, f, indent=4)
        
        # Index courses
        return self._index_courses(courses)
    
    def _fetch_courses(
        self,
        term: str,
        subjects: Optional[list[str]] = None,
    ) -> list[dict]:
        """Fetch courses from SIS API.
        
        Args:
            term: Academic term code
            subjects: List of subject codes
            
        Returns:
            List of course dictionaries
        """
        if subjects is None:
            subjects = ["CS", "DSA", "STAT", "MATH", "STS"]
        
        all_courses = []
        total_subjects = len(subjects)
        start_time = time.time()
        
        print(f"\n{'='*50}")
        print(f"FETCHING COURSES FROM SIS API")
        print(f"{'='*50}")
        print(f"Subjects to fetch: {', '.join(subjects)}")
        print(f"Term: {term}")
        print()
        
        for idx, subject in enumerate(subjects, 1):
            subject_start = time.time()
            subject_courses = 0
            page = 1
            
            print(f"[{idx}/{total_subjects}] Fetching {subject}...", end=" ", flush=True)
            
            while True:
                try:
                    response = self.sis_service.search_courses_sync(
                        subject=subject,
                        term=term,
                        page=page,
                    )
                    # Handle both list and dict response formats
                    classes = self.sis_service._get_classes_list(response)
                    
                    if not classes:
                        break
                    
                    all_courses.extend(classes)
                    subject_courses += len(classes)
                    page += 1
                    
                    # Safety limit
                    if page > 20:
                        break
                        
                except Exception as e:
                    print(f"Error: {e}")
                    break
            
            elapsed = time.time() - subject_start
            print(f"{subject_courses} sections ({elapsed:.1f}s)")
        
        total_time = time.time() - start_time
        print(f"\nFetched {len(all_courses)} total sections in {total_time:.1f}s")
        
        return all_courses
    
    def _fetch_hooslist_descriptions(self, courses: list[dict]) -> dict:
        """Fetch descriptions from Hooslist for unique courses.
        
        Args:
            courses: List of course dictionaries
            
        Returns:
            Dictionary mapping "SUBJECT_CATALOG" to description info
        """
        # Get unique course identifiers
        unique_courses = {}
        for course in courses:
            key = f"{course.get('subject', '')}_{course.get('catalog_nbr', '')}"
            if key not in unique_courses:
                unique_courses[key] = {
                    "subject": course.get("subject", ""),
                    "catalog_nbr": course.get("catalog_nbr", ""),
                }
        
        print(f"\n{'='*50}")
        print(f"FETCHING DESCRIPTIONS FROM HOOSLIST")
        print(f"{'='*50}")
        print(f"Unique courses to fetch: {len(unique_courses)}")
        print()
        
        descriptions = {}
        total = len(unique_courses)
        start_time = time.time()
        
        for idx, (key, info) in enumerate(unique_courses.items(), 1):
            subject = info["subject"]
            catalog_nbr = info["catalog_nbr"]
            
            if idx % 20 == 0 or idx == total:
                elapsed = time.time() - start_time
                rate = idx / elapsed if elapsed > 0 else 0
                eta = (total - idx) / rate if rate > 0 else 0
                print(f"  [{idx}/{total}] Fetching descriptions... ({elapsed:.1f}s elapsed, ETA: {eta:.0f}s)", flush=True)
            
            desc_info = self.sis_service.get_course_description(subject, catalog_nbr)
            descriptions[key] = desc_info
        
        # Count how many had descriptions
        with_desc = sum(1 for d in descriptions.values() if d.get("description"))
        with_prereq = sum(1 for d in descriptions.values() if d.get("prerequisites"))
        
        total_time = time.time() - start_time
        print(f"\nFetched {len(descriptions)} descriptions in {total_time:.1f}s")
        print(f"  - With descriptions: {with_desc}")
        print(f"  - With prerequisites: {with_prereq}")
        
        return descriptions
    
    def _fetch_tcf_reviews(self, courses: list[dict]) -> dict:
        """Fetch reviews from TheCourseForum for unique courses.
        
        Args:
            courses: List of course dictionaries
            
        Returns:
            Dictionary mapping "SUBJECT_CATALOG" to reviews list
        """
        # Get unique course identifiers
        unique_courses = {}
        for course in courses:
            key = f"{course.get('subject', '')}_{course.get('catalog_nbr', '')}"
            if key not in unique_courses:
                unique_courses[key] = {
                    "subject": course.get("subject", ""),
                    "catalog_nbr": course.get("catalog_nbr", ""),
                }
        
        print(f"\n{'='*50}")
        print(f"FETCHING REVIEWS FROM THECOURSEFORUM")
        print(f"{'='*50}")
        print(f"Unique courses to fetch: {len(unique_courses)}")
        print()
        
        reviews_map = {}
        total = len(unique_courses)
        start_time = time.time()
        successful = 0
        failed = 0
        
        for idx, (key, info) in enumerate(unique_courses.items(), 1):
            subject = info["subject"]
            catalog_nbr = info["catalog_nbr"]
            
            if idx % 10 == 0 or idx == total:
                elapsed = time.time() - start_time
                rate = idx / elapsed if elapsed > 0 else 0
                eta = (total - idx) / rate if rate > 0 else 0
                print(f"  [{idx}/{total}] Fetching reviews... ({elapsed:.1f}s elapsed, ETA: {eta:.0f}s, ✓{successful} ✗{failed})", flush=True)
            
            try:
                # Build the course URL
                course_url = f"{BASE_URL}/{subject}/{catalog_nbr}/"
                reviews = scrape_course(course_url)
                reviews_map[key] = reviews
                if reviews:
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"\n  Warning: Failed to fetch reviews for {subject} {catalog_nbr}: {e}")
                reviews_map[key] = []
                failed += 1
        
        total_time = time.time() - start_time
        print(f"\nFetched reviews for {len(reviews_map)} courses in {total_time:.1f}s")
        print(f"  - Successful: {successful}")
        print(f"  - Not found/Failed: {failed}")
        
        return reviews_map
    
    def _index_courses(self, courses: list[dict]) -> int:
        """Index courses into vector store.
        
        Args:
            courses: List of course dictionaries
            
        Returns:
            Number of courses indexed
        """
        # First, fetch descriptions from Hooslist
        hooslist_descriptions = self._fetch_hooslist_descriptions(courses)
        
        # Then, fetch reviews from TheCourseForum
        tcf_reviews = self._fetch_tcf_reviews(courses)
        
        print(f"\n{'='*50}")
        print(f"INDEXING COURSES INTO VECTOR DATABASE")
        print(f"{'='*50}")
        
        # Clear existing data
        print("Clearing existing index...", end=" ", flush=True)
        self.vector_store.clear()
        print("Done")
        
        # Convert to documents
        print("Preparing documents...", end=" ", flush=True)
        documents = []
        metadatas = []
        ids = []
        
        seen = set()
        
        for i, course in enumerate(courses):
            course_id = f"{course.get('subject', '')}_{course.get('catalog_nbr', '')}_{course.get('class_nbr', '')}"
            
            if course_id in seen:
                continue
            seen.add(course_id)
            
            # Get Hooslist description for this course
            desc_key = f"{course.get('subject', '')}_{course.get('catalog_nbr', '')}"
            hooslist_info = hooslist_descriptions.get(desc_key, {})
            
            # Get TCF reviews for this course
            all_reviews = tcf_reviews.get(desc_key, [])
            
            # Filter reviews to only include instructors teaching this specific section
            section_instructors = course.get("instructors", [])
            section_instructor_names = set()
            
            for inst in section_instructors:
                name = inst.get("name", "").strip()
                if name:
                    # Store both original and normalized versions for better matching
                    section_instructor_names.add(name.lower())
                    # Also try last name only for partial matches
                    parts = name.split()
                    if len(parts) >= 2:
                        section_instructor_names.add(parts[-1].lower())
            
            # Match reviews to section instructors
            matched_reviews = []
            for review in all_reviews:
                review_instructor = review.get("instructor_name", "").strip()
                if not review_instructor:
                    continue
                    
                review_lower = review_instructor.lower()
                
                # Try exact match first
                if review_lower in section_instructor_names:
                    matched_reviews.append(review)
                    continue
                
                # Try last name match
                review_parts = review_instructor.split()
                if len(review_parts) >= 2:
                    review_last = review_parts[-1].lower()
                    if review_last in section_instructor_names:
                        matched_reviews.append(review)
            
            # Create document text - use SIS service method and append reviews
            base_doc = self.sis_service.get_course_document(course, hooslist_info)
            doc_text = self._append_reviews_to_document(base_doc, matched_reviews)
            
            # Create metadata
            course_code = f"{course.get('subject', '')} {course.get('catalog_nbr', '')}"
            clusters = get_course_clusters(course_code)

            metadata = {
                "subject": course.get("subject", ""),
                "catalog_number": course.get("catalog_nbr", ""),
                "title": course.get("descr", ""),
                "class_number": str(course.get("class_nbr", "")),
                "has_description": bool(hooslist_info.get("description")),
                "has_prerequisites": bool(hooslist_info.get("prerequisites")),
<<<<<<< Updated upstream
                "has_reviews": len(matched_reviews) > 0,
                "review_count": len(matched_reviews),
=======
                "clusters": ",".join(clusters) if clusters else "",
                "course_code": course_code,
>>>>>>> Stashed changes
            }
            
            documents.append(doc_text)
            metadatas.append(metadata)
            ids.append(course_id)
        
        print(f"{len(documents)} unique courses")
        
        # Batch add to vector store with progress
        batch_size = 50  # Smaller batches for better progress updates
        total_batches = (len(documents) + batch_size - 1) // batch_size
        start_time = time.time()
        
        print(f"\nGenerating embeddings and indexing ({total_batches} batches):")
        print(f"  [Estimated time: ~{total_batches * 2}-{total_batches * 4} seconds]")
        print()
        
        for batch_num, i in enumerate(range(0, len(documents), batch_size), 1):
            batch_start = time.time()
            batch_docs = documents[i:i + batch_size]
            batch_meta = metadatas[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            
            progress = (batch_num / total_batches) * 100
            docs_done = min(i + batch_size, len(documents))
            
            print(f"  Batch {batch_num}/{total_batches} [{progress:5.1f}%] - {docs_done}/{len(documents)} docs...", end=" ", flush=True)
            
            self.vector_store.add_documents(
                documents=batch_docs,
                metadatas=batch_meta,
                ids=batch_ids,
            )
            
            batch_time = time.time() - batch_start
            elapsed = time.time() - start_time
            remaining_batches = total_batches - batch_num
            eta = (elapsed / batch_num) * remaining_batches if batch_num > 0 else 0
            
            print(f"Done ({batch_time:.1f}s) | ETA: {eta:.0f}s")
        
        total_time = time.time() - start_time
        print(f"\n{'='*50}")
        print(f"INDEXING COMPLETE!")
        print(f"  - Indexed: {len(documents)} courses")
        print(f"  - Time: {total_time:.1f} seconds")
        print(f"{'='*50}\n")
        
        return len(documents)
    
    def _append_reviews_to_document(self, base_doc: str, reviews: list[dict]) -> str:
        """Append TCF review data to existing course document.
        
        Args:
            base_doc: Base document from SIS service
            reviews: Review data from TheCourseForum
            
        Returns:
            Document with reviews appended
        """
        if not reviews:
            return base_doc + "\n\nReviews: No review data available on TheCourseForum."
        
        review_parts = [f"\n\nReviews ({len(reviews)} instructors):"]
        
        for review in reviews:
            instructor = review.get("instructor_name", "Unknown")
            rating = review.get("rating")
            difficulty = review.get("difficulty")
            gpa = review.get("gpa")
            
            review_text = f"  {instructor}"
            
            # Only add metrics if they exist and aren't "—"
            if rating and rating != "—":
                review_text += f" | Rating: {rating}/5"
            if difficulty and difficulty != "—":
                review_text += f" | Difficulty: {difficulty}/5"
            if gpa and gpa != "—":
                review_text += f" | Avg GPA: {gpa}"
            
            # If no metrics were added, note that
            if review_text == f"  {instructor}":
                review_text += " | No ratings available"
            
            review_parts.append(review_text)
        
        return base_doc + "\n".join(review_parts)
    
    def get_status(self) -> dict:
        """Get current indexing status.
        
        Returns:
            Status dictionary with counts
        """
        return {
            "indexed_count": self.vector_store.count(),
            "cache_files": list(self.data_dir.glob("*.json")),
        }