import datetime

from isca.model.item import Paper, Session
from isca.model.person import Person, Annuary
from isca.model.program import Program
from isca.model.event import Conference


class Interspeech(Conference):
    def __init__(
        self,
        id: str,
        name: str,
        start_date: datetime.date,
        end_date: datetime.date,
        papers: dict[str, Paper],
        program: Program | None = None,
        sessions: list[Session] | None = None,
        location: str | None = None,
        url: str | None = None,
        chairs: list[Person] | None = None,
        generate_doi: bool = False,
        theme: dict[str, object] | None = None,
        annuary: Annuary | None = None,
    ):
        super().__init__(
            id,
            name,
            start_date,
            end_date,
            papers,
            program,
            sessions,
            location,
            url,
            "Interspeech",
            chairs,
            "2958-1796",
            generate_doi,
            theme,
            annuary,
        )
        self.best_student_papers_nominees: set[Paper] = set()
        self.best_theme_papers_nominees: set[Paper] = set()

    def add_student_award_nominees(self, paper: Paper | str):
        if isinstance(paper, str):
            paper = self.papers[paper]

        self.best_student_papers_nominees.add(paper)

    def is_student_award_nominee(self, paper: Paper | str):
        if isinstance(paper, str):
            paper = self.papers[paper]

        return paper in self.best_student_papers_nominees

    def add_theme_award_nominees(self, paper: Paper | str):
        if isinstance(paper, str):
            paper = self.papers[paper]

        self.best_theme_papers_nominees.add(paper)

    def is_theme_award_nominee(self, paper: Paper | str):
        if isinstance(paper, str):
            paper = self.papers[paper]

        return paper in self.best_theme_papers_nominees
