"""UVA SIS API service for course data."""

import httpx
from typing import Optional
from app.config import get_settings
from app.course_clusters import get_course_clusters, get_cluster_description
from app.models.schemas import Course, Section


class SISService:
    """Service for interacting with UVA SIS API.
    
    API Documentation: https://s23.cs3240.org/sis-api.html
    
    Term codes:
        Format: 1 + [2-digit year] + [semester code]
        Semester codes: 2 = Spring, 6 = Summer, 8 = Fall
        Examples: 1252 = Spring 2025, 1248 = Fall 2024, 1258 = Fall 2025
    """
    
    # Base URL for the class search API
    BASE_URL = "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch"
    
    # URL for getting department mnemonics
    OPTIONS_URL = "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearchOptions"
    
    # Hooslist URL for course descriptions
    HOOSLIST_DESC_URL = "https://hooslist.virginia.edu/ClassSchedule/_GetCourseDescription"
    
    # Common subject codes at UVA
    CS_SUBJECTS = ["CS", "DSA"]
    
    def __init__(self):
        self.settings = get_settings()
        # Enable redirect following for the SIS API
        self.client = httpx.Client(timeout=30.0, follow_redirects=True)
    
    async def search_courses(
        self,
        subject: Optional[str] = None,
        catalog_number: Optional[str] = None,
        term: str = "1252",  # Spring 2025
        page: int = 1,
    ) -> dict:
        """Search for courses using SIS API.
        
        Args:
            subject: Subject code (e.g., "CS")
            catalog_number: Course number (e.g., "4774")
            term: Academic term code (1252 = Spring 2025)
            page: Results page number
            
        Returns:
            Dictionary with course results
        """
        params = {
            "institution": "UVA01",
            "term": term,
            "page": page,
        }
        
        if subject:
            params["subject"] = subject.upper()
        if catalog_number:
            params["catalog_nbr"] = catalog_number
            
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
    
    def search_courses_sync(
        self,
        subject: Optional[str] = None,
        catalog_number: Optional[str] = None,
        keyword: Optional[str] = None,
        instructor: Optional[str] = None,
        term: str = "1252",
        page: int = 1,
    ) -> dict:
        """Synchronous version of course search.
        
        Args:
            subject: Subject code (e.g., "CS")
            catalog_number: Course number (e.g., "4774")
            keyword: Keyword to search in course titles
            instructor: Instructor last name
            term: Academic term code
            page: Results page number
            
        Returns:
            Dictionary with course results
        """
        params = {
            "institution": "UVA01",
            "term": term,
            "page": page,
        }
        
        if subject:
            params["subject"] = subject.upper()
        if catalog_number:
            params["catalog_nbr"] = catalog_number
        if keyword:
            params["keyword"] = keyword
        if instructor:
            params["instructor_name"] = instructor
        
        # Debug: print the URL being requested
        print(f"[SIS API] Requesting: {self.BASE_URL}")
        print(f"[SIS API] Params: {params}")
        
        response = self.client.get(self.BASE_URL, params=params)
        print(f"[SIS API] Response status: {response.status_code}")
        response.raise_for_status()
        return response.json()
    
    def _get_classes_list(self, api_response) -> list:
        """Extract classes list from API response.
        
        The API can return either:
        - A list of classes directly
        - A dict with a 'classes' key containing the list
        
        Args:
            api_response: Raw API response (list or dict)
            
        Returns:
            List of class dictionaries
        """
        if isinstance(api_response, list):
            return api_response
        elif isinstance(api_response, dict):
            return api_response.get("classes", [])
        return []
    
    def get_course_description(self, subject: str, course_num: str) -> dict:
        """Fetch course description and prerequisites from Hooslist.
        
        Args:
            subject: Subject code (e.g., "CS")
            course_num: Course number (e.g., "4774")
            
        Returns:
            Dictionary with 'description' and 'prerequisites' keys
        """
        try:
            response = self.client.get(
                self.HOOSLIST_DESC_URL,
                params={"subject": subject.upper(), "courseNum": course_num},
            )
            response.raise_for_status()
            
            text = response.text.strip()
            
            # Parse the response - prerequisites are usually on a separate line
            description = ""
            prerequisites = ""
            
            if "Prerequisites:" in text:
                parts = text.split("Prerequisites:", 1)
                description = parts[0].strip()
                prerequisites = parts[1].strip()
            elif "Prerequisite:" in text:
                parts = text.split("Prerequisite:", 1)
                description = parts[0].strip()
                prerequisites = parts[1].strip()
            else:
                description = text
            
            return {
                "description": description,
                "prerequisites": prerequisites,
            }
        except Exception as e:
            print(f"[Hooslist] Error fetching description for {subject} {course_num}: {e}")
            return {"description": "", "prerequisites": ""}
    
    def parse_courses(self, api_response) -> list[Course]:
        """Parse API response into Course objects.
        
        Args:
            api_response: Raw API response
            
        Returns:
            List of Course objects
        """
        courses = []
        seen = set()
        
        for cls in self._get_classes_list(api_response):
            course_id = f"{cls.get('subject', '')} {cls.get('catalog_nbr', '')}"
            
            if course_id in seen:
                continue
            seen.add(course_id)
            
            course = Course(
                subject=cls.get("subject", ""),
                catalog_number=cls.get("catalog_nbr", ""),
                title=cls.get("descr", ""),
                description=cls.get("crse_descr", ""),
                units=cls.get("units", ""),
            )
            courses.append(course)
        
        return courses
    
    def parse_sections(self, api_response) -> list[Section]:
        """Parse API response into Section objects.
        
        Args:
            api_response: Raw API response
            
        Returns:
            List of Section objects
        """
        sections = []
        
        for cls in self._get_classes_list(api_response):
            for meeting in cls.get("meetings", [{}]):
                section = Section(
                    class_number=str(cls.get("class_nbr", "")),
                    section=cls.get("class_section", ""),
                    instructor=self._extract_instructor(cls),
                    days=meeting.get("days", ""),
                    start_time=meeting.get("start_time", ""),
                    end_time=meeting.get("end_time", ""),
                    location=f"{meeting.get('facility_descr', '')}".strip(),
                    enrollment_total=cls.get("enrollment_total"),
                    enrollment_cap=cls.get("class_capacity"),
                    waitlist_total=cls.get("wait_tot"),
                )
                sections.append(section)
        
        return sections
    
    def _extract_instructor(self, cls: dict) -> str:
        """Extract instructor name from class data."""
        instructors = cls.get("instructors", [])
        if instructors:
            return instructors[0].get("name", "Staff")
        return "Staff"
    
    def _format_time(self, time_str: str) -> str:
        """Format time string from SIS API to readable format.
        
        Converts "09.00.00.000000" to "9:00am", "14.30.00.000000" to "2:30pm"
        
        Args:
            time_str: Time string in format "HH.MM.SS.ffffff"
            
        Returns:
            Formatted time string like "9:00am" or "2:30pm"
        """
        if not time_str:
            return ""
        
        try:
            # Parse "HH.MM.SS.ffffff" format
            parts = time_str.split(".")
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            
            # Convert to 12-hour format
            period = "am" if hour < 12 else "pm"
            if hour == 0:
                hour = 12
            elif hour > 12:
                hour -= 12
            
            # Format with or without minutes
            if minute == 0:
                return f"{hour}{period}"
            else:
                return f"{hour}:{minute:02d}{period}"
        except (ValueError, IndexError):
            return time_str  # Return original if parsing fails
    
    def get_course_document(self, cls: dict, hooslist_info: dict = None) -> str:
        """Convert course data to text document for RAG with weighted field repetition.

        Fields are repeated according to their configured weights to control similarity:
        - Description: repeated 3x (most important for semantic similarity)
        - Title: repeated 2x
        - Prerequisites: repeated 2x
        - Subject: repeated 1x
        - Clusters: repeated 2x (groups related courses like AI courses together)
        - Instructor: not included (weight 0)
        - Schedule/Time: not included (weight 0)

        Args:
            cls: Course class dictionary from API
            hooslist_info: Optional dict with 'description' and 'prerequisites' from Hooslist

        Returns:
            Formatted text document with weighted field repetition
        """
        # Get embedding weights from config
        weights = (self.settings.embed_weight_description, self.settings.embed_weight_title,
                  self.settings.embed_weight_prerequisites, self.settings.embed_weight_subject,
                  self.settings.embed_weight_cluster, self.settings.embed_weight_instructor,
                  self.settings.embed_weight_schedule)
        desc_w, title_w, prereq_w, subject_w, cluster_w, instr_w, sched_w = weights

        parts = []

        # Subject (weight controlled)
        subject = cls.get('subject', '')
        catalog_nbr = cls.get('catalog_nbr', '')
        subject_line = f"Subject: {subject} {catalog_nbr}"
        parts.extend([subject_line] * subject_w)

        # Title (weight controlled)
        title = cls.get('descr', '')
        if title:
            title_line = f"Title: {title}"
            parts.extend([title_line] * title_w)

        # Description (weight controlled - most important)
        description = ""
        if hooslist_info and hooslist_info.get("description"):
            description = hooslist_info['description']
        elif cls.get("crse_descr"):
            description = cls.get('crse_descr', '')

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

        # Course Clusters (weight controlled - groups related courses together)
        course_code = f"{subject} {catalog_nbr}"
        clusters = get_course_clusters(course_code)

        if clusters:
            cluster_lines = []
            for cluster in clusters:
                desc = get_cluster_description(cluster)
                cluster_lines.append(f"Cluster: {cluster} - {desc}")
            # Repeat all cluster information according to weight
            for _ in range(cluster_w):
                parts.extend(cluster_lines)

        # Credits (not weighted, just include once)
        if cls.get("units"):
            parts.append(f"Credits: {cls.get('units', '')}")

        # Enrollment (not weighted, just include once)
        if cls.get("enrollment_total") is not None:
            parts.append(f"Enrollment: {cls.get('enrollment_total', 0)}/{cls.get('class_capacity', 0)}")

        return "\n".join(parts)
    
    def fetch_all_cs_courses(self, term: str = "1252") -> list[dict]:
        """Fetch all CS-related courses for indexing.
        
        Args:
            term: Academic term code
            
        Returns:
            List of raw course dictionaries
        """
        all_courses = []
        
        for subject in self.CS_SUBJECTS:
            page = 1
            while True:
                response = self.search_courses_sync(subject=subject, term=term, page=page)
                classes = self._get_classes_list(response)
                
                if not classes:
                    break
                    
                all_courses.extend(classes)
                page += 1
                
                # Safety limit
                if page > 20:
                    break
        
        return all_courses

