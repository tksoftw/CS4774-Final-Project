class Professor:
    def __init__(
        self,
        ratemyprof_id: int,
        first_name: str,
        last_name: str,
        num_of_ratings: int,
        overall_rating,
    ):
        self.ratemyprof_id = int(ratemyprof_id)

        self.name = f"{first_name} {last_name}".strip()
        self.first_name = first_name
        self.last_name = last_name
        self.num_of_ratings = int(num_of_ratings or 0)

        if self.num_of_ratings < 1:
            self.overall_rating = 0.0
        else:
            try:
                self.overall_rating = float(overall_rating)
            except (TypeError, ValueError):
                self.overall_rating = 0.0
