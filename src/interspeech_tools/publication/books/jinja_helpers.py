import re
import datetime
import jinja2
from pyuca import Collator

from isca.model.person import Person
from isca.model.item import Paper
from isca.model.program import PresentationSession, Presentation, SurveyTalk, BlueSkyPresentation, Timeslot


from .utils import latexify
from .theme import (
    get_presentation_type,
    get_session_type,
)


def is_presentation(input: object) -> bool:
    return isinstance(input, Presentation)


def has_paper(input: Presentation) -> bool:
    if not is_presentation(input):
        return False
    if input.presented_paper is None:
        return False
    return True


def get_latexified_validation_authors(input_paper: Paper | Presentation) -> str:
    list_authors = []
    if is_presentation(input_paper):
        input_paper = input_paper.presented_paper

    for cur_author in input_paper.authors:
        list_authors.append(cur_author.str_with_flatten_affiliations(input_paper.id, short=True, markers=True))

    return latexify(", ".join(list_authors))


def get_latexified_validation_presenters(input_presentation: Presentation) -> str:
    list_presenters = []
    if input_presentation.presenters is not None:
        for cur_presenter in input_presentation.presenters:
            if input_presentation.presented_paper is None:
                list_presenters.append(cur_presenter.str_with_flatten_affiliations(None, short=True, markers=False))
            else:
                list_presenters.append(cur_presenter.str_with_flatten_affiliations(input_presentation.presented_paper.id, short=True, markers=False))

    return latexify(", ".join(list_presenters))

def get_latexified_authors(input_paper: Paper | Presentation) -> str:
    list_authors = []
    if is_presentation(input_paper):
        input_paper = input_paper.presented_paper

    for cur_author in input_paper.authors:
        list_authors.append(cur_author.str_with_flatten_affiliations(input_paper.id, short=True, markers=False))

    return latexify(", ".join(list_authors))


def get_latexified_presenters(input_presentation: Presentation) -> str:
    list_presenters = []
    if input_presentation.presenters is not None:
        for cur_presenter in input_presentation.presenters:
            if input_presentation.presented_paper is None:
                list_presenters.append(cur_presenter.str_with_flatten_affiliations(None, short=True, markers=False))
            else:
                list_presenters.append(cur_presenter.str_with_flatten_affiliations(input_presentation.presented_paper.id, short=True, markers=False))

    return latexify(", ".join(list_presenters))


def sort_by_last_name(people: set[Person]) -> list[Person]:
    pyuca_collator = Collator()
    list_people = sorted(people, key=lambda x: pyuca_collator.sort_key(x.lastname + " " + str(x.middle_initial) + " " + str(x.firstname)))
    return list_people


def sort_by_name(people: set[Person]) -> list[Person]:
    pyuca_collator = Collator()
    list_people = sorted(people, key=lambda x:pyuca_collator.sort_key( x.name))
    return list_people


def extract_date(input_time: datetime.datetime) -> str:
    return input_time.strftime("%Y-%m-%d")


def extract_verbose_date(input_time: datetime.datetime) -> str:
    return input_time.strftime("%A %-d %B %Y")


def format_timeslot(timeslot: Timeslot) -> str:
    return timeslot.start.strftime("%H:%M") + "--" + timeslot.end.strftime("%H:%M")


def get_presentation_timeslot(input_session: PresentationSession, presentation_idx: int) -> str:
    start = input_session.start_presentation(presentation_idx)
    end = input_session.end_presentation(presentation_idx)
    return start.strftime("%H:%M") + "--" + end.strftime("%H:%M")


def is_presentation_survey(input_presentation: Presentation) -> bool:
    return isinstance(input_presentation, SurveyTalk)


def is_presentation_bluesky(input_presentation: Presentation) -> bool:
    return isinstance(input_presentation, BlueSkyPresentation)


def compact_number(input: str) -> str:
    return re.sub(r"[ ]+([0-9]+)", r"~\g<1>", input)


def configure_latex_jinja(template_loader: jinja2.PackageLoader):
    jenv_latex = jinja2.Environment(
        block_start_string="\\BLOCK{",
        block_end_string="}",
        variable_start_string="\\VAR{",
        variable_end_string="}",
        comment_start_string="\\#{",
        comment_end_string="}",
        line_statement_prefix="% ;;",
        line_comment_prefix="% ##",
        trim_blocks=True,
        autoescape=False,
        loader=template_loader,
    )

    # Set generic filters
    jenv_latex.filters["latexify"] = latexify
    jenv_latex.filters["compact_numbers"] = compact_number
    jenv_latex.filters["has_paper"] = has_paper
    jenv_latex.filters["is_presentation"] = is_presentation
    jenv_latex.filters["sort_authors"] = sort_by_last_name
    jenv_latex.filters["sort_reviewers"] = sort_by_name
    jenv_latex.filters["sort_presenters"] = sort_by_name
    jenv_latex.filters["authors"] = get_latexified_authors
    jenv_latex.filters["presenters"] = get_latexified_presenters
    jenv_latex.filters["validation_authors"] = get_latexified_validation_authors
    jenv_latex.filters["validation_presenters"] = get_latexified_validation_presenters
    jenv_latex.filters["type_presentation"] = get_presentation_type
    jenv_latex.filters["type_session"] = get_session_type
    jenv_latex.filters["extract_date"] = extract_date
    jenv_latex.filters["extract_verbose_date"] = extract_verbose_date
    jenv_latex.filters["format_timeslot"] = format_timeslot
    jenv_latex.filters["get_presentation_timeslot"] = get_presentation_timeslot
    jenv_latex.filters["is_survey"] = is_presentation_survey
    jenv_latex.filters["is_bluesky"] = is_presentation_bluesky

    return jenv_latex
