import logging
import pathlib

from isca.io.cmt import OralSession, PosterSession
from isca.model.event import Conference
from isca.model.session import OralSession, PosterSession, KeynoteSession, SpecialSession, ShowAndTellSession, Session
from isca.model.item import (
    ShowAndTellPresentation,
    SpecialPresentation,
    SurveyTalk,
    OralPresentation,
    PosterPresentation,
    Presentation,
)


SPECIFIC_SESSION_IDS = {KeynoteSession: "keynote", SpecialSession: "special", ShowAndTellSession: "showandtell"}
GENERIC_SESSION_IDS = {OralSession: "oral", PosterSession: "poster"}
SPECIFIC_PRESENTATION_IDS = {
    ShowAndTellPresentation: "showandtell",
    SpecialPresentation: "special",
    SurveyTalk: "survey",
}
GENERIC_PRESENTATION_IDS = {
    OralPresentation: "oral",
    PosterPresentation: "poster",
}


def get_presentation_type(input_presentation: Presentation) -> str:
    if type(input_presentation) in SPECIFIC_PRESENTATION_IDS:
        return SPECIFIC_PRESENTATION_IDS[type(input_presentation)]

    if type(input_presentation) in GENERIC_PRESENTATION_IDS:
        return GENERIC_PRESENTATION_IDS[type(input_presentation)]

    logger = logging.getLogger("get_presentation_type")
    logger.warning(f"{type(input_presentation)} is unknown for the validation book, use the default information")
    return "default"


def get_session_type(input_session: Session) -> str:
    if type(input_session) in SPECIFIC_SESSION_IDS:
        return SPECIFIC_SESSION_IDS[type(input_session)]

    if type(input_session) in GENERIC_SESSION_IDS:
        return GENERIC_SESSION_IDS[type(input_session)]

    logger = logging.getLogger("get_session_type")
    logger.warning(f"{type(input_session)} is unknown for the validation book, use the default information")
    return "default"


def generate_theme_file(conf: Conference, output_file: pathlib.Path):
    if conf.theme is None:
        raise Exception("There is no theme element defined for the conference")

    if "colors" not in conf.theme:
        raise Exception("There is no default colors in the theme")

    tcb_lines = []
    with open(output_file, "w") as f_color_theme:
        f_color_theme.write("%% Default colour information\n")
        f_color_theme.write(
            f"\\definecolor{{DefaultForegroundColour}}{{HTML}}{{{conf.theme['colors']['foreground'].replace('#', '')}}}\n"
        )
        f_color_theme.write(
            f"\\definecolor{{LinkColour}}{{HTML}}{{{conf.theme['colors']['foreground'].replace('#', '')}}}\n"
        )
        f_color_theme.write(
            f"\\definecolor{{DefaultBackgroundColour}}{{HTML}}{{{conf.theme['colors']['background'].replace('#', '')}}}\n"
        )
        f_color_theme.write(f"\\colorlet{{DefaultBackgroundColour}}{{DefaultBackgroundColour}}\n")
        f_color_theme.write(f"\\colorlet{{DefaultForegroundColour}}{{DefaultForegroundColour}}\n")

        # FIXME: hardcoded
        f_color_theme.write(f"\\colorlet{{FooterBackgroundColour}}{{DefaultForegroundColour}}\n")
        f_color_theme.write(f"\\colorlet{{FooterForegroundColour}}{{white}}\n")
        f_color_theme.write(f"\\colorlet{{RoomColour}}{{DefaultForegroundColour}}\n")
        f_color_theme.write(f"\\colorlet{{RoomCellColour}}{{gray!25!white}}\n")
        f_color_theme.write("\n")
        tcb_lines.append("default/.style={colframe=DefaultForegroundColour, colback=DefaultBackgroundColour}")

        # Now move to the other colors
        configured_session_type_theme = set()
        for elt, elt_info in conf.theme.items():
            # Ignore the default key
            if elt in ("colors", "font", "footer"):
                continue

            #
            if "colors" not in elt_info:
                f_color_theme.write(f"\\colorlet{{{elt.capitalize()}BackgroundColour}}{{DefaultBackgroundColour}}\n")
                f_color_theme.write(f"\\colorlet{{{elt.capitalize()}ForegroundColour}}{{DefaultForegroundColour}}\n")
            else:
                f_color_theme.write(f"%% {elt.capitalize()} colour information\n")
                f_color_theme.write(
                    f"\\definecolor{{{elt.capitalize()}ForegroundColour}}{{HTML}}{{{elt_info['colors']['foreground'].replace('#', '')}}}\n"
                )
                f_color_theme.write(
                    f"\\definecolor{{{elt.capitalize()}BackgroundColour}}{{HTML}}{{{elt_info['colors']['background'].replace('#', '')}}}\n"
                )
                f_color_theme.write(
                    f"\\colorlet{{{elt.capitalize()}BackgroundColour}}{{{elt.capitalize()}BackgroundColour}}\n"
                )
                f_color_theme.write(
                    f"\\colorlet{{{elt.capitalize()}ForegroundColour}}{{{elt.capitalize()}ForegroundColour}}\n"
                )
                f_color_theme.write("\n")
            tcb_lines.append(
                f"{elt}/.style={{colframe={elt.capitalize()}ForegroundColour, colback={elt.capitalize()}BackgroundColour}}"
            )
            configured_session_type_theme.add(elt)


        f_color_theme.write("\n\n")
        f_color_theme.write(f"%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n")
        f_color_theme.write(f"%% Colours not defined in the configuration\n")
        f_color_theme.write(f"%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n")
        session_types = set()
        for session in conf.sessions:
            session_types.add(get_session_type(session))

        for session_type in session_types:
            if session_type not in configured_session_type_theme:
                f_color_theme.write(f"%% {session_type.capitalize()} colour information\n")
                f_color_theme.write(
                    f"\\colorlet{{{session_type.capitalize()}BackgroundColour}}{{DefaultBackgroundColour}}\n"
                )
                f_color_theme.write(
                    f"\\colorlet{{{session_type.capitalize()}ForegroundColour}}{{DefaultForegroundColour}}\n"
                )
                f_color_theme.write("\n")
                tcb_lines.append(
                    f"{session_type}/.style={{colframe={session_type.capitalize()}ForegroundColour, colback={session_type.capitalize()}BackgroundColour}}"
                )

        # Now we are done, just add the
        f_color_theme.write("\\tcbset{\n  ")
        f_color_theme.write(",\n  ".join(tcb_lines))
        f_color_theme.write("\n}")
