import pathlib
import datetime

from isca.model.item import Paper, Session
from isca.model.person import Person, Annuary
from isca.model.program import (
    OralSession,
    Presentation,
    PresentationSession,
    OralPresentation,
    Program,
    Timeslot,
    Room,
    AnonymousTimeslot,
)
from isca.model.event import Conference, Event
from enum import Enum


class LongPaper(Paper):
    def __init__(
        self,
        id: str,
        title: str,
        authors: list[Person],
        abstract: str | None = None,
        pdf_file: pathlib.Path | str | None = None,
        reviewers: list[Person] | None = None,
        track: str | None = None,
        metadata_from_pdf: bool = False,
        resource: str | None = None,
    ):
        super().__init__(id, title, authors, abstract, pdf_file, reviewers, track, metadata_from_pdf, resource)


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
        self.description: str = description


class InterspeechEventType(Enum):
    MEETING = 0
    YOUNG_RESEARCHER = 1
    CEREMONY = 2

    def __str__(self) -> str:
        """Return the string representation of the role

        Returns
        -------
        str
            the (uppercase) name of the role
        """
        return f'{self.name.replace("InterspeechEventType.", "")}'


class InterspeechEvent(Session):
    def __init__(self, id: str, name: str, organiser: str, event_type: InterspeechEventType, description: str | None = None):
        super().__init__(id, name)
        self._organiser: str = organiser
        self._event_type: InterspeechEventType = event_type
        self.description = description

    @property
    def organiser(self) -> str:
        return self._organiser

    @property
    def event_type(self) -> InterspeechEventType:
        return self._event_type

    def __repr__(self) -> str:
        return f"InterspeechEvent(id={self.id}, name={self.name}, organisers={self.organiser}, event_type={self.event_type})"


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


class LongPresentation(OralPresentation):
    def __init__(
        self,
        id: str,
        title: str,
        presenters: list[Person] | None,
        duration: int,
        abstract: str | None = None,
        presented_paper: LongPaper | None = None,
    ):
        if presented_paper is not None:
            assert isinstance(presented_paper, LongPaper)
        super().__init__(id, title, presenters, duration, abstract, presented_paper)


class LongSession(OralSession):
    def __init__(
        self,
        id: str,
        name: str,
        start: datetime.datetime,
        end: datetime.datetime,
        presentations: list[LongPresentation | SurveyTalk] | None = None,
        chairs: list[Person] | None = None,
    ):
        super().__init__(id, name, start, end, presentations, chairs, 20)


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
        self.ignored_rooms: set[Room] = set()
        self.ignored_timeslots: set[Timeslot] = set()
        self.satellite_events: list[Satellite] = []

    def update_satellite_events(self, satellite_events: list[Satellite]):
        self.satellite_events += satellite_events

    def update_ignored_rooms(self, rooms: set[Room]):
        self.ignored_rooms.update(rooms)

    def update_ignored_timeslots(self, timeslots: set[Timeslot]):
        self.ignored_timeslots.update(timeslots)

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

    def list_student_award_nominees_presentations(self) -> list[tuple[Presentation, Room, Timeslot]]:
        assert self.program is not None

        presentations = []
        for session, timeslot, room, zone_idx in self.program.sessions:
            if not isinstance(session, PresentationSession):
                continue

            for presentation in session.presentations:
                if presentation.presented_paper in self.best_student_papers_nominees:
                    presentations.append((presentation, room, timeslot, zone_idx))

        presentations = sorted(presentations, key=lambda x: (x[0].start if isinstance(x[0], OralSession) else x[2].start, x[3]))
        return presentations

    def list_theme_award_nominees_presentations(self) -> list[tuple[Presentation, Room, AnonymousTimeslot]]:
        assert self.program is not None

        presentations = []
        for session, timeslot_session, room, zone_idx in self.program.sessions:
            if not isinstance(session, PresentationSession):
                continue

            for idx_presentation, presentation in enumerate(session.presentations):
                if presentation.presented_paper in self.best_theme_papers_nominees:
                    if isinstance(session, OralSession):
                        timeslot = session.timeslot_presentation(idx_presentation)
                    else:
                        timeslot = timeslot_session

                    presentations.append((presentation, room, timeslot, zone_idx))

        presentations = sorted(presentations, key=lambda x: (x[2].start, x[3]))
        return presentations
