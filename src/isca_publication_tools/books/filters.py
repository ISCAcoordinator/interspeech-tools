import datetime
import logging

from isca.model.item import SurveyTalk, BlueSkyPresentation
from isca.model.session import PresentationSession, Session

from isca.model.item import Paper, Presentation
from isca.model.person import Person

from .utils import latexify

from .theme import SPECIFIC_PRESENTATION_IDS, GENERIC_PRESENTATION_IDS, SPECIFIC_SESSION_IDS, GENERIC_SESSION_IDS


def is_presentation(input: object) -> bool:
    return isinstance(input, Presentation)


def has_paper(input: Presentation) -> bool:
    if not is_presentation(input):
        return False
    if input.presented_paper is None:
        return False
    return True


def get_latexified_authors(input_paper: Paper | Presentation) -> str:
    list_authors = []
    if is_presentation(input_paper):
        input_paper = input_paper.presented_paper

    for cur_author in input_paper.authors:
        list_authors.append(cur_author.str_with_flatten_affiliations(input_paper.id, short=True))

    return latexify(", ".join(list_authors))


def get_latexified_presenters(input_presentation: Presentation) -> str:
    list_presenters = []
    if input_presentation.presenters is not None:
        for cur_presenter in input_presentation.presenters:
            list_presenters.append(cur_presenter.str_with_flatten_affiliations(input_presentation.id, short=True))

    return latexify(", ".join(list_presenters))


def sort_by_last_name(people: set[Person]) -> list[Person]:
    list_people = sorted(people, key=lambda x: x.lastname + " " + str(x.middle_initial) + " " + str(x.firstname))
    return list_people


def sort_by_name(people: set[Person]) -> list[Person]:
    list_people = sorted(people, key=lambda x: x.name)
    return list_people


def get_presentation_type(input_presentation: Presentation) -> str:
    if type(input_presentation) in SPECIFIC_PRESENTATION_IDS:
        return SPECIFIC_PRESENTATION_IDS[type(input_presentation)]

    if type(input_presentation) in GENERIC_PRESENTATION_IDS:
        return GENERIC_PRESENTATION_IDS[type(input_presentation)]

    logger = logging.getLogger("get_type")
    logger.warning(f"{type(input_presentation)} is unknown for the validation book, use the default information")
    return "default"


def get_session_type(input_session: Session) -> str:
    if type(input_session) in SPECIFIC_SESSION_IDS:
        return SPECIFIC_SESSION_IDS[type(input_session)]

    if type(input_session) in GENERIC_SESSION_IDS:
        return GENERIC_SESSION_IDS[type(input_session)]

    logger = logging.getLogger("get_type")
    logger.warning(f"{type(input_session)} is unknown for the validation book, use the default information")
    return "default"


def extract_date(input_time: datetime.datetime) -> str:
    return input_time.strftime("%Y-%m-%d")


def extract_verbose_date(input_time: datetime.datetime) -> str:
    return input_time.strftime("%A %-d %B %Y")


def get_session_timeslot(input_session: PresentationSession) -> str:
    return input_session.start.strftime("%H:%M") + "--" + input_session.end.strftime("%H:%M")


def get_presentation_timeslot(input_session: PresentationSession, presentation_idx: int) -> str:
    start = input_session.start_presentation(presentation_idx)
    end = input_session.end_presentation(presentation_idx)
    return start.strftime("%H:%M") + "--" + end.strftime("%H:%M")


def is_presentation_survey(input_presentation: Presentation) -> bool:
    return isinstance(input_presentation, SurveyTalk)

def is_presentation_bluesky(input_presentation: Presentation) -> bool:
    return isinstance(input_presentation, BlueSkyPresentation)
