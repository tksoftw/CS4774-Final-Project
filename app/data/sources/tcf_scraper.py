import requests
from bs4 import BeautifulSoup

BASE_URL = "https://thecourseforum.com/course"
API_BASE_URL = "https://thecourseforum.com/api/courses"

HEADERS = {
    "User-Agent": "UVA-Course-Advising-Project/1.0 (academic use)"
}

def fetch_course_page(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

def fetch_course_stats(course_id: int) -> dict:
    """Fetch course statistics from TheCourseForum API.
    
    Args:
        course_id: TheCourseForum course ID
        
    Returns:
        Dictionary with course statistics, or empty dict if not found
    """
    url = f"{API_BASE_URL}/{course_id}/?allstats=&format=json"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Warning: Could not fetch stats for course {course_id}: {e}")
        return {}

def extract_course_id_from_page(soup: BeautifulSoup) -> int:
    """Extract course ID from the course page HTML.
    
    The course ID appears in instructor profile links like /course/15226/605/
    """
    # Look for instructor links in the format /course/{course_id}/{instructor_id}/
    instructor_list = soup.find("ul", class_="instructor-list")
    if instructor_list:
        link = instructor_list.find("a", href=True)
        if link:
            import re
            # Match pattern like /course/15226/605/
            match = re.search(r'/course/(\d+)/\d+/', link['href'])
            if match:
                return int(match.group(1))
    
    # Fallback: try to find it in script tags
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string and '/api/courses/' in script.string:
            import re
            match = re.search(r'/api/courses/(\d+)/', script.string)
            if match:
                return int(match.group(1))
    
    return None

def get_instructor_cards(soup: BeautifulSoup):
    ul = soup.find("ul", class_="instructor-list")
    if not ul:
        return []
    return ul.find_all("li", class_="instructor")

def safe_text(el):
    return el.get_text(strip=True) if el else None

def parse_instructor(li):
    # Name
    name = safe_text(li.find("h3", id="title"))

    # Profile link (contains instructor ID)
    a_tag = li.find("a", href=True)
    profile_url = f"https://thecourseforum.com{a_tag['href']}" if a_tag else None

    # Stats
    rating = safe_text(li.find("p", id="rating"))
    difficulty = safe_text(li.find("p", id="difficulty"))
    gpa = safe_text(li.find("p", id="gpa"))

    return {
        "instructor_name": name,
        "profile_url": profile_url,
        "rating": rating if rating else None,
        "difficulty": difficulty if difficulty else None,
        "gpa": gpa if gpa else None,
    }

def process_course_stats(stats: dict) -> dict:
    """Process raw course stats into a cleaner format with grade distributions.
    
    Args:
        stats: Raw stats dictionary from API
        
    Returns:
        Processed stats with calculated grade percentages
    """
    if not stats:
        return None
    
    # Extract the fields we care about
    processed = {
        "average_rating": stats.get("average_rating"),
        "average_instructor": stats.get("average_instructor"),
        "average_fun": stats.get("average_fun"),
        "average_recommendability": stats.get("average_recommendability"),
        "average_difficulty": stats.get("average_difficulty"),
        "average_hours_per_week": stats.get("average_hours_per_week"),
        "average_amount_reading": stats.get("average_amount_reading"),
        "average_amount_writing": stats.get("average_amount_writing"),
        "average_amount_group": stats.get("average_amount_group"),
        "average_amount_homework": stats.get("average_amount_homework"),
        "average_gpa": stats.get("average_gpa"),
        "total_enrolled": stats.get("total_enrolled", 0),
    }
    
    # Calculate grade distribution percentages
    total = stats.get("total_enrolled", 0)
    if total > 0:
        processed["grade_distribution"] = {
            "A+": round((stats.get("a_plus", 0) / total) * 100, 1),
            "A": round((stats.get("a", 0) / total) * 100, 1),
            "A-": round((stats.get("a_minus", 0) / total) * 100, 1),
            "B+": round((stats.get("b_plus", 0) / total) * 100, 1),
            "B": round((stats.get("b", 0) / total) * 100, 1),
            "B-": round((stats.get("b_minus", 0) / total) * 100, 1),
            "C+": round((stats.get("c_plus", 0) / total) * 100, 1),
            "C": round((stats.get("c", 0) / total) * 100, 1),
            "C-": round((stats.get("c_minus", 0) / total) * 100, 1),
            "D/F/W": round((stats.get("dfw", 0) / total) * 100, 1),
        }
    else:
        processed["grade_distribution"] = None
    
    return processed

def scrape_course(course_url: str):
    """Scrape course reviews and statistics from TheCourseForum.
    
    Automatically appends '/All' to get all historical instructor data.
    Also fetches course-level statistics from the API.
    
    Args:
        course_url: URL like "https://thecourseforum.com/course/CS/4774/" 
                   or just the path portion
    
    Returns:
        Dictionary with:
        - instructors: List of instructor review dictionaries
        - course_stats: Processed course-level statistics
    """
    # Ensure we're using the /All endpoint
    if not course_url.endswith('/'):
        course_url += '/'
    if not course_url.endswith('/All'):
        course_url += 'All'
    
    soup = fetch_course_page(course_url)
    
    # Get instructor reviews
    instructors = []
    for li in get_instructor_cards(soup):
        data = parse_instructor(li)
        if data["instructor_name"]:
            instructors.append(data)
    
    # Try to get course ID and fetch stats
    course_stats = None
    course_id = extract_course_id_from_page(soup)
    if course_id:
        raw_stats = fetch_course_stats(course_id)
        course_stats = process_course_stats(raw_stats)
    
    return {
        "instructors": instructors,
        "course_stats": course_stats,
    }