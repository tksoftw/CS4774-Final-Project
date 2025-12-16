"""Document builder for RAG course documents.

Combines data from multiple sources (SIS, Hooslist, TCF, RMP) into 
unified text documents for vector embedding and retrieval.
"""

from typing import Optional
from app.config import get_settings, get_course_clusters, get_cluster_description, CLUSTER_WEIGHTS
from app.data.sources.sis_api import SISApi
from app.data.stores.rmp_reviews_loader import get_rmp_loader


class DocumentBuilder:
    """Builds text documents for RAG from course data."""
    
    def __init__(self):
        self.settings = get_settings()
        self.sis_api = SISApi()
    
    def build_document(
        self,
        course: dict,
        hooslist_info: Optional[dict] = None,
        reviews: Optional[list[dict]] = None,
        include_rmp: bool = True,
    ) -> str:
        """Build a complete course document for RAG indexing.
        
        Combines course info, description, and reviews with weighted field repetition
        to control semantic similarity.
        
        Args:
            course: Course dictionary from SIS API
            hooslist_info: Optional dict with 'description' and 'prerequisites' from Hooslist
            reviews: Optional list of instructor review dictionaries from TCF
            include_rmp: Whether to include RateMyProfessor reviews
            
        Returns:
            Formatted text document for embedding
        """
        # Get embedding weights from config
        desc_w = self.settings.embed_weight_description
        title_w = self.settings.embed_weight_title
        prereq_w = self.settings.embed_weight_prerequisites
        subject_w = self.settings.embed_weight_subject
        cluster_w = self.settings.embed_weight_cluster
        
        parts = []
        
        # Subject (weight controlled)
        subject = course.get('subject', '')
        catalog_nbr = course.get('catalog_nbr', '')
        subject_line = f"Subject: {subject} {catalog_nbr}"
        parts.extend([subject_line] * subject_w)
        
        # Title (weight controlled)
        title = course.get('descr', '')
        if title:
            title_line = f"Title: {title}"
            parts.extend([title_line] * title_w)
        
        # Description (weight controlled - most important)
        description = self._get_description(course, hooslist_info)
        if description:
            desc_line = f"Description: {description}"
            parts.extend([desc_line] * desc_w)
        
        # Prerequisites (weight controlled)
        prerequisites = ""
        if hooslist_info and hooslist_info.get("prerequisites"):
            prerequisites = hooslist_info['prerequisites']
        if prerequisites:
            prereq_line = f"Prerequisites: {prerequisites}"
            parts.extend([prereq_line] * prereq_w)
        
        # Course Clusters (weight controlled + per-cluster weights)
        course_code = f"{subject} {catalog_nbr}"
        clusters = get_course_clusters(course_code)
        if clusters:
            for cluster in clusters:
                desc = get_cluster_description(cluster)
                # Apply both base cluster weight AND per-cluster weight multiplier
                cluster_multiplier = CLUSTER_WEIGHTS.get(cluster, 1)
                total_weight = cluster_w * cluster_multiplier
                for _ in range(total_weight):
                    parts.append(f"Cluster: {cluster} - {desc}")
        
        # Credits (not weighted)
        if course.get("units"):
            parts.append(f"Credits: {course.get('units', '')}")
        
        # Enrollment (not weighted)
        if course.get("enrollment_total") is not None:
            parts.append(f"Enrollment: {course.get('enrollment_total', 0)}/{course.get('class_capacity', 0)}")
        
        # Instructor (not weighted)
        instructors = course.get("instructors", [])
        if instructors:
            inst_names = [inst.get("name", "Staff") for inst in instructors]
            parts.append(f"Instructor: {', '.join(inst_names)}")
        
        # Schedule - days and times (not weighted)
        meetings = course.get("meetings", [])
        if meetings:
            schedule_parts = []
            for meeting in meetings:
                days = meeting.get("days", "")
                start_time = meeting.get("start_time", "")
                end_time = meeting.get("end_time", "")
                
                if days and start_time:
                    start_fmt = self.sis_api.format_time(start_time)
                    end_fmt = self.sis_api.format_time(end_time) if end_time else ""
                    if end_fmt:
                        schedule_parts.append(f"{days} {start_fmt}-{end_fmt}")
                    else:
                        schedule_parts.append(f"{days} {start_fmt}")
            
            if schedule_parts:
                parts.append(f"Schedule: {'; '.join(schedule_parts)}")
        
        # Build base document
        base_doc = "\n".join(parts)
        
        # Append TCF reviews if available
        doc_with_tcf = self._append_reviews(base_doc, reviews)
        
        # Append RMP reviews for this semester's instructors
        if include_rmp:
            doc_with_tcf = self._append_rmp_reviews(doc_with_tcf, course)
        
        return doc_with_tcf
    
    def _get_description(self, course: dict, hooslist_info: Optional[dict]) -> str:
        """Get course description from available sources.
        
        Args:
            course: Course dictionary from SIS
            hooslist_info: Optional Hooslist info
            
        Returns:
            Description string
        """
        if hooslist_info and hooslist_info.get("description"):
            return hooslist_info['description']
        elif course.get("crse_descr"):
            return course.get('crse_descr', '')
        return ""
    
    def _append_reviews(self, base_doc: str, reviews: Optional[list[dict]]) -> str:
        """Append TCF review data to document.
        
        Args:
            base_doc: Base document text
            reviews: List of review dictionaries from TheCourseForum
            
        Returns:
            Document with reviews appended
        """
        if not reviews:
            return base_doc + "\n\nTCF Reviews: No review data available."
        
        review_parts = [f"\n\nTCF Reviews ({len(reviews)} instructors):"]
        
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
    
    def _append_rmp_reviews(self, base_doc: str, course: dict) -> str:
        """Append RateMyProfessor reviews for this semester's instructors.
        
        Args:
            base_doc: Base document text
            course: Course dictionary from SIS (with 'instructors' list)
            
        Returns:
            Document with RMP reviews appended
        """
        rmp_loader = get_rmp_loader()
        instructors = course.get("instructors", [])
        
        if not instructors:
            return base_doc
        
        subject = course.get("subject", "")
        catalog_nbr = course.get("catalog_nbr", "")
        course_code = f"{subject} {catalog_nbr}"
        
        rmp_parts = []
        
        for inst in instructors:
            inst_name = inst.get("name", "").strip()
            if not inst_name or inst_name.lower() == "staff":
                continue
            
            # Get RMP reviews for this instructor + course
            reviews = rmp_loader.get_reviews_for_course_instructor(
                course_code, inst_name, limit=5
            )
            
            if not reviews:
                continue
            
            # Get summary stats
            summary = rmp_loader.summarize_reviews(reviews, inst_name)
            
            # Format for document
            inst_section = f"\n  {inst_name} (RateMyProfessor):"
            
            if summary["avg_clarity"]:
                inst_section += f"\n    - Clarity: {summary['avg_clarity']}/5"
            if summary["avg_helpful"]:
                inst_section += f"\n    - Helpful: {summary['avg_helpful']}/5"
            if summary["avg_difficulty"]:
                inst_section += f"\n    - Difficulty: {summary['avg_difficulty']}/5"
            if summary["would_take_again_pct"] is not None:
                inst_section += f"\n    - Would Take Again: {summary['would_take_again_pct']}%"
            
            # Add sample comments (truncated)
            if summary["sample_comments"]:
                inst_section += "\n    - Sample reviews:"
                for comment in summary["sample_comments"][:2]:
                    truncated = comment[:150] + "..." if len(comment) > 150 else comment
                    inst_section += f"\n      * \"{truncated}\""
            
            rmp_parts.append(inst_section)
        
        if not rmp_parts:
            return base_doc
        
        return base_doc + f"\n\nRateMyProfessor Reviews:" + "".join(rmp_parts)
    
    def build_metadata(
        self,
        course: dict,
        hooslist_info: Optional[dict] = None,
        reviews: Optional[list[dict]] = None,
    ) -> dict:
        """Build metadata for a course document.
        
        Args:
            course: Course dictionary from SIS
            hooslist_info: Optional Hooslist info
            reviews: Optional list of reviews
            
        Returns:
            Metadata dictionary for vector store
        """
        subject = course.get("subject", "")
        catalog_number = course.get("catalog_nbr", "")
        course_code = f"{subject} {catalog_number}"
        clusters = get_course_clusters(course_code)
        
        return {
            "subject": subject,
            "catalog_number": catalog_number,
            "title": course.get("descr", ""),
            "class_number": str(course.get("class_nbr", "")),
            "has_description": bool(hooslist_info and hooslist_info.get("description")),
            "has_prerequisites": bool(hooslist_info and hooslist_info.get("prerequisites")),
            "has_reviews": bool(reviews),
            "review_count": len(reviews) if reviews else 0,
            "clusters": ",".join(clusters) if clusters else "",
            "course_code": course_code,
        }
    
    def match_reviews_to_instructors(
        self,
        course: dict,
        all_reviews: list[dict],
    ) -> list[dict]:
        """Match reviews to the instructors of a specific course section.
        
        Args:
            course: Course dictionary from SIS (with 'instructors' list)
            all_reviews: All reviews for the course from TCF
            
        Returns:
            Reviews matching the course's instructors
        """
        section_instructors = course.get("instructors", [])
        section_names = set()
        
        for inst in section_instructors:
            name = inst.get("name", "").strip()
            if name:
                section_names.add(name.lower())
                # Also add last name for partial matching
                parts = name.split()
                if len(parts) >= 2:
                    section_names.add(parts[-1].lower())
        
        matched = []
        for review in all_reviews:
            instructor = review.get("instructor_name", "").strip()
            if not instructor:
                continue
            
            instructor_lower = instructor.lower()
            
            # Try exact match
            if instructor_lower in section_names:
                matched.append(review)
                continue
            
            # Try last name match
            parts = instructor.split()
            if len(parts) >= 2:
                last_name = parts[-1].lower()
                if last_name in section_names:
                    matched.append(review)
        
        return matched

