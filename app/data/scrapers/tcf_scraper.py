import requests
from bs4 import BeautifulSoup

BASE_URL = "https://thecourseforum.com/course"


HEADERS = {
    "User-Agent": "UVA-Course-Advising-Project/1.0 (academic use)"
}

def fetch_course_page(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

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
    last_taught = safe_text(li.find("p", id="recency"))

    return {
        "instructor_name": name,
        "profile_url": profile_url,
        "rating": rating if rating else None,
        "difficulty": difficulty if difficulty else None,
        "gpa": gpa if gpa else None,
        "last_taught": last_taught,
    }

def scrape_course(course_url: str):
    soup = fetch_course_page(course_url)
    instructors = []

    for li in get_instructor_cards(soup):
        data = parse_instructor(li)
        if data["instructor_name"]:
            instructors.append(data)

    return instructors

