import datetime

from isca.model.item import Paper, Session
from isca.model.person import Person, Annuary
from isca.model.program import Presentation, PresentationSession, OralPresentation, PosterPresentation, Program
from isca.model.event import Conference, Event


class Satellite(Event):
    def __init__(
        self,
        id: str,
        name: str,
        start_date: datetime.date,
        end_date: datetime.date,
        location: str,
        description: str,
        url: str,
    ):
        super().__init__(id, name, start_date, end_date, location, url)
        self.description = description


class Tutorial(Presentation):
    def __init__(self, id: str, title: str, presenters: list[Person], duration: int, description: str, is_invited: bool = False):
        super().__init__(id, title, presenters, duration, description)
        self._is_invited = is_invited

    @property
    def description(self) -> str:
        return str(self.abstract)

    @property
    def is_invited(self) -> bool:
        return self._is_invited


class SurveyTalk(OralPresentation):
    def __init__(
        self,
        id: str,
        title: str,
        presenters: list[Person] | None,
        duration: int,
        abstract: str | None = None,
    ):
        super().__init__(id, title, presenters, duration, abstract, None)


class SpecialPresentation(Presentation):
    def __init__(
        self,
        id: str,
        title: str,
        presenters: list[Person] | None,
        abstract: str | None = None,
        presented_paper: Paper | None = None,
    ):
        super().__init__(id, title, presenters, None, abstract, presented_paper)


class ShowAndTellPresentation(Presentation):
    def __init__(
        self,
        id: str,
        title: str,
        presenters: list[Person] | None,
        abstract: str | None = None,
        presented_paper: Paper | None = None,
    ):
        super().__init__(id, title, presenters, None, abstract, presented_paper)


class BlueSkyPresentation(OralPresentation):
    def __init__(
        self,
        id: str,
        title: str,
        presenters: list[Person] | None,
        duration: int,
        abstract: str | None = None,
        presented_paper: Paper | None = None,
    ):
        super().__init__(id, title, presenters, duration, abstract, presented_paper)


class SpecialSession(PresentationSession):
    def __init__(
        self,
        id: str,
        name: str,
        start: datetime.datetime,
        end: datetime.datetime,
        description: str,
        presentations: list[Presentation] | None = None,
        chairs: list[Person] | None = None,
    ):
        super().__init__(id, name, start, end, presentations, chairs)
        self._description: str = description

    @property
    def description(self) -> str:
        return self._description


class ShowAndTellSession(PresentationSession):
    def __init__(
        self,
        id: str,
        name: str,
        start: datetime.datetime,
        end: datetime.datetime,
        presentations: list[Presentation] | None = None,
        chairs: list[Person] | None = None,
    ):
        super().__init__(id, name, start, end, presentations, chairs)


class TutorialSession(PresentationSession):
    def __init__(self, id: str, name: str, start: datetime.datetime, end: datetime.datetime, tutorial: Tutorial):
        super().__init__(id, name, start, end, [tutorial])

    @property
    def tutorial(self) -> Tutorial:
        presentation = self.presentations[0]
        assert isinstance(presentation, Tutorial)
        return presentation


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
