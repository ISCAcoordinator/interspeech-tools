import logging
import pathlib
import jinja2

from isca.model.item import Session
from isca.model.program import (
    OralSession,
    PosterSession,
    KeynoteSession,
    OralPresentation,
    PosterPresentation,
    Presentation,
    SocialSession,
)
from ...model import (
    BlueSkyPresentation,
    Interspeech,
    InterspeechEvent,
    LongPresentation,
    LongSession,
    SpecialSession,
    ShowAndTellSession,
    ShowAndTellPresentation,
    SpecialPresentation,
    SurveyTalk,
    TutorialSession,
)

SPECIFIC_SESSION_IDS = {
    KeynoteSession: "keynote",
    SpecialSession: "special",
    ShowAndTellSession: "showandtell",
    TutorialSession: "tutorial",
}
GENERIC_SESSION_IDS = {OralSession: "oral", PosterSession: "poster", SocialSession: "social", LongSession: "long"}
SPECIFIC_PRESENTATION_IDS = {
    ShowAndTellPresentation: "showandtell",
    SpecialPresentation: "special",
    SurveyTalk: "survey",
    BlueSkyPresentation: "bluesky",
}
GENERIC_PRESENTATION_IDS = {OralPresentation: "oral", PosterPresentation: "poster", LongPresentation: "long"}


def get_presentation_type(input_presentation: Presentation) -> str:
    if type(input_presentation) in SPECIFIC_PRESENTATION_IDS:
        return SPECIFIC_PRESENTATION_IDS[type(input_presentation)]

    if type(input_presentation) in GENERIC_PRESENTATION_IDS:
        return GENERIC_PRESENTATION_IDS[type(input_presentation)]

    logger = logging.getLogger("get_presentation_type")
    logger.warning(f"{type(input_presentation)} is unknown, use the default information")
    return "default"


def get_session_type(input_session: Session) -> str:
    if type(input_session) in SPECIFIC_SESSION_IDS:
        return SPECIFIC_SESSION_IDS[type(input_session)]

    if type(input_session) in GENERIC_SESSION_IDS:
        return GENERIC_SESSION_IDS[type(input_session)]

    if isinstance(input_session, InterspeechEvent):
        return str(input_session.event_type).lower()

    logger = logging.getLogger("get_session_type")
    logger.warning(f"{type(input_session)} is unknown, use the default information")
    return "default"


def generate_theme_file(conf: Interspeech, output_file: pathlib.Path, template_engine: jinja2.Environment):
    if conf.theme is None:
        raise Exception("There is no theme element defined for the conference")

    if "colors" not in conf.theme:
        raise Exception("There is no default colors in the theme")

    # Now move to the other colors
    default_colors = dict()
    if "colors" not in conf.theme:
        raise Exception("Default background and foreground colors should be defined")

    for scope, html_code in conf.theme["colors"].items():
        default_colors[scope] = html_code.replace("#", "")

    unknown_types = list()
    known_types = dict()
    for elt, elt_info in conf.theme.items():
        # Ignore the default key
        if elt in ("colors", "font", "footer"):
            continue

        #
        if "colors" not in elt_info:
            unknown_types.append(elt)
        else:
            known_types[elt] = dict()
            for scope, html_code in elt_info["colors"].items():
                known_types[elt][scope] = html_code.replace("#", "")

    session_types = set()
    for session in conf.sessions:
        session_types.add(get_session_type(session))

    for session_type in session_types:
        if session_type not in known_types:
            unknown_types.append(session_type)

    presentation_types = set()
    for presentation_type in SPECIFIC_PRESENTATION_IDS.values():
        presentation_types.add(presentation_type)

    for presentation_type in presentation_types:
        if presentation_type not in known_types:
            unknown_types.append(presentation_type)

    day_program_template = template_engine.get_template("colour.tex.jinja2")
    with open(output_file, "w") as outfile:
        outfile.write(
            day_program_template.render(
                default_colors=default_colors,
                known_types=known_types,
                unknown_types=unknown_types,
            )
        )
