"""UVA SIS API service for course data."""

import httpx
from typing import Optional
from app.config import get_settings
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
    
    def get_course_document(self, cls: dict) -> str:
        """Convert course data to text document for RAG.
        
        Args:
            cls: Course class dictionary from API
            
        Returns:
            Formatted text document
        """
        parts = [
            f"Course: {cls.get('subject', '')} {cls.get('catalog_nbr', '')}",
            f"Title: {cls.get('descr', '')}",
        ]
        
        if cls.get("crse_descr"):
            parts.append(f"Description: {cls.get('crse_descr', '')}")
        
        if cls.get("units"):
            parts.append(f"Credits: {cls.get('units', '')}")
        
        # Add section info
        meetings = cls.get("meetings", [])
        if meetings:
            meeting = meetings[0]
            if meeting.get("days"):
                parts.append(f"Days: {meeting.get('days', '')}")
            if meeting.get("start_time") and meeting.get("end_time"):
                parts.append(f"Time: {meeting.get('start_time', '')} - {meeting.get('end_time', '')}")
            if meeting.get("facility_descr"):
                parts.append(f"Location: {meeting.get('facility_descr', '')}")
        
        # Add instructor
        instructor = self._extract_instructor(cls)
        if instructor:
            parts.append(f"Instructor: {instructor}")
        
        # Add enrollment
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

