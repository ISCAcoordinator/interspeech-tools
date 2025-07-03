import pathlib

from isca.model.event import Conference
from isca.model.session import OralPresentation, PosterPresentation
from isca.model.item import ShowAndTellPresentation, SpecialPresentation, SurveyTalk

SPECIFIC_PRESENTATION_IDS = {
    ShowAndTellPresentation: "showandtell",
    SpecialPresentation: "special",
    SurveyTalk: "survey",
}
GENERIC_PRESENTATION_IDS = {
    OralPresentation: "oral",
    PosterPresentation: "poster",
}


def generate_theme_file(conf: Conference, output_file: pathlib.Path):
    if conf.theme is None:
        raise Exception("There is no theme element defined for the conference")

    if "colors" not in conf.theme:
        raise Exception("There is no default colors in the theme")

    tcb_lines = []
    with open(output_file, "w") as f_color_theme:
        f_color_theme.write("%% Default colour information\n")
        f_color_theme.write(f"\\definecolor{{DefaultForegroundColour}}{{HTML}}{{{conf.theme['colors']['foreground'].replace('#', '')}}}\n")
        f_color_theme.write(f"\\definecolor{{LinkColour}}{{HTML}}{{{conf.theme['colors']['foreground'].replace('#', '')}}}\n")
        f_color_theme.write(f"\\definecolor{{DefaultBackgroundColour}}{{HTML}}{{{conf.theme['colors']['background'].replace('#', '')}}}\n")
        f_color_theme.write(f"\\colorlet{{DefaultBackgroundColour}}{{DefaultBackgroundColour}}\n")
        f_color_theme.write(f"\\colorlet{{DefaultForegroundColour}}{{DefaultForegroundColour}}\n")
        f_color_theme.write(f"\\colorlet{{FooterBackgroundColour}}{{DefaultForegroundColour}}\n") # FIXME: hardcoded
        f_color_theme.write(f"\\colorlet{{FooterForegroundColour}}{{white}}\n") # FIXME: hardcoded
        f_color_theme.write("\n")
        tcb_lines.append('default/.style={colframe=DefaultForegroundColour, colback=DefaultBackgroundColour}')

        # Now move to the other colors
        for elt, elt_info in conf.theme.items():
            # Ignore the default key
            if elt in ("colors", "font", "footer"):
                continue

            #
            if "colors" not in elt_info:
                tcb_lines.append(f'{elt}/.style={{colframe=DefaultForegroundColour, colback=DefaultBackgroundColour}}')
            else:
                f_color_theme.write(f"%% {elt.capitalize()} colour information\n")
                f_color_theme.write(f"\\definecolor{{{elt.capitalize()}ForegroundColour}}{{HTML}}{{{elt_info['colors']['foreground'].replace('#', '')}}}\n")
                f_color_theme.write(f"\\definecolor{{{elt.capitalize()}BackgroundColour}}{{HTML}}{{{elt_info['colors']['background'].replace('#', '')}}}\n")
                f_color_theme.write(f"\\colorlet{{{elt.capitalize()}BackgroundColour}}{{{elt.capitalize()}BackgroundColour}}\n")
                f_color_theme.write(f"\\colorlet{{{elt.capitalize()}ForegroundColour}}{{{elt.capitalize()}ForegroundColour}}\n")
                f_color_theme.write("\n")
                tcb_lines.append(f'{elt}/.style={{colframe={elt.capitalize()}ForegroundColour, colback={elt.capitalize()}BackgroundColour}}')

        # Now we are done, just add the
        f_color_theme.write("\\tcbset{\n  ")
        f_color_theme.write(",\n  ".join(tcb_lines))
        f_color_theme.write("\n}")
