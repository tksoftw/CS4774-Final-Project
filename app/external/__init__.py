def __init__(self, school_id: str = "1074", testing: bool = False):
    self.UniversityId = str(school_id)

    folder = "SchoolID_" + self.UniversityId
    if not os.path.exists(folder):
        os.mkdir(folder)

    # Create a session with browser-like headers to avoid 403 blocks
    self.session = requests.Session()
    self.session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.ratemyprofessors.com/",
        "Connection": "keep-alive",
    })

    # Load professors (limited pages if testing=True)
    self.professors = self.scrape_professors(testing=testing)
