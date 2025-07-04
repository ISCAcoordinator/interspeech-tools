import datetime
import pathlib

import jinja2

from isca.model.core import ISCAObject
from isca.model.session import Room, PresentationSession, Timeslot
from isca.model.person import Person
from isca.model.item import Paper
from isca.model.event import Conference


from ..books.utils import (
    latexify,
)
from ..books.filters import (
    sort_by_last_name,
    sort_by_name,
    get_latexified_authors,
    get_latexified_presenters,
    is_presentation,
    has_paper,
    is_presentation_survey,
    is_presentation_bluesky,
    extract_date,
    extract_verbose_date,
    get_session_timeslot,
    get_presentation_timeslot,
    compact_number,
)
from ..books.theme import (
    get_presentation_type,
    get_session_type,
)


class AbstractBookProcessor:
    def __init__(self, conf: Conference):
        self._conf = conf

        templateLoader = jinja2.PackageLoader("isca_publication_tools", "resources/abstract_book")
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
            loader=templateLoader,
        )

        # Set generic filters
        jenv_latex.filters["latexify"] = latexify
        jenv_latex.filters["compact_numbers"] = compact_number
        jenv_latex.filters["has_paper"] = has_paper
        jenv_latex.filters["is_presentation"] = is_presentation
        jenv_latex.filters["sort_authors"] = sort_by_last_name
        jenv_latex.filters["sort_reviewers"] = sort_by_name
        jenv_latex.filters["authors"] = get_latexified_authors
        jenv_latex.filters["presenters"] = get_latexified_presenters
        jenv_latex.filters["type_presentation"] = get_presentation_type
        jenv_latex.filters["type_session"] = get_session_type
        jenv_latex.filters["extract_date"] = extract_date
        jenv_latex.filters["extract_verbose_date"] = extract_verbose_date
        jenv_latex.filters["get_session_timeslot"] = get_session_timeslot
        jenv_latex.filters["get_presentation_timeslot"] = get_presentation_timeslot
        jenv_latex.filters["is_survey"] = is_presentation_survey
        jenv_latex.filters["is_bluesky"] = is_presentation_bluesky

        # Set conference specific filters
        def list_papers(author: Person) -> list[Paper]:
            return conf.list_papers(author)

        jenv_latex.filters["list_papers"] = list_papers

        self._latex_renderer = jenv_latex

    def process(self, root_output_dir: pathlib.Path) -> None:

        root_output_dir.mkdir(exist_ok=True, parents=True)
        delta = self._conf.end_date - self._conf.start_date  # returns timedelta
        for i in range(delta.days + 1):
            date = self._conf.start_date + datetime.timedelta(days=i)
            outfilename = root_output_dir / f"{date}_table.tex"

            # Generate the program table
            day_timeslots = self._conf.get_timeslots(date)
            with open(outfilename, "w") as outfile:
                outfile.write(self._generate_programme_table(day_timeslots))

            # Generate the program content
            day_sessions = []
            for timeslot in day_timeslots:
                if timeslot.sessions is not None:
                    for session in timeslot.sessions:
                        day_sessions.append(session)

            day_sessions = sorted(day_sessions, key=lambda x: x.start)
            day_program_template = self._latex_renderer.get_template("day_program_template.tex")
            outfilename = root_output_dir / f"{date}.tex"
            with open(outfilename, "w") as outfile:
                outfile.write(day_program_template.render(sessions=day_sessions))

        reviewer_template = self._latex_renderer.get_template("reviewers_index_template.tex")
        outfilename = root_output_dir / "reviewers_index.tex"
        with open(outfilename, "w") as outfile:
            outfile.write(reviewer_template.render(reviewers=self._conf.reviewers))

        author_template = self._latex_renderer.get_template("authors_index_template.tex")
        outfilename = root_output_dir / "authors_index.tex"
        with open(outfilename, "w") as outfile:
            outfile.write(author_template.render(authors=self._conf.authors))

    def _generate_programme_table(
            self, timeslots: list[Timeslot], max_cols_per_page:int = 7
    ) -> str:

        # List rooms
        rooms = set()
        for timeslot in timeslots:
            if (timeslot.sessions is not None) and (len(timeslot.sessions) > 1):
                for session in timeslot.sessions:
                    rooms.add(session.room)
        rooms = sorted(rooms, key=lambda x: x.name)

        # retrieve the room names from the plan column names
        parts = []
        for firstCol in list(range(0, len(rooms)))[::max_cols_per_page]:
            part_rooms = rooms[firstCol : firstCol + max_cols_per_page]
            table_part = self._generate_programme_table_part(timeslots, part_rooms)
            parts.append(table_part)

        return "\n\n".join(parts)

    def _generate_programme_table_part(
            self, timeslots: list[Timeslot], rooms: list[Room]
    ):
        content = []

        # Prepare header
        timecolspec = "C{\\tabletimecolwidth}|"
        colspec = "C{\\tablecolwidth}|"
        rooms_latex = [f"\\cellcolor{{RoomCellColour}}\\textbf{{{r.name}}}" for r in rooms]
        header = f"\\begin{{tabular}}{{|{timecolspec}{''.join([colspec for _ in rooms])}}} \\hline \n"
        header += f"& {' & '.join(rooms_latex) } \\\\ \\hline \n"

        # Reorganize sessions per time_start (FIXME: this should be put up a bit)
        for timeslot in timeslots:
            timeslot_str = timeslot.timeslot_without_date().replace(" ", "")
            elts = [timeslot_str]
            if timeslot.sessions is None:
                row = f"\\multicolumn{{{len(rooms)}}}{{c|}}{{"
                row += timeslot.name
                row += "}"
                elts.append(row)
            elif len(timeslot.sessions) == 1:
                session = timeslot.sessions[0]
                session_type = get_session_type(session)
                row = f"\\multicolumn{{{len(rooms)}}}{{c|}}{{"
                row += f"\\cellcolor{{{session_type.capitalize()}BackgroundColour}}{{\\color{{{session_type.capitalize()}ForegroundColour}}\\bf {session.name}}}"
                row += "}"
                elts.append(row)
            else:
                for room in rooms:
                    session = timeslot.get_session_in_room(room)
                    if session is None:
                        elts.append("")
                    else:
                        session_type = get_session_type(session)
                        session_name = session.name.replace("Special Session - ", "") # FIXME: this is hardcoded
                        elts.append(f"\\cellcolor{{{session_type.capitalize()}BackgroundColour}}{{\\color{{{session_type.capitalize()}ForegroundColour}}\\bf {session_name}}}")

            content.append(' & '.join(elts))

        end = "\\\\ \\hline \n \\end{tabular}\n\n"
        end += "\\bigskip\n\n"
        return header + " \\\\ \\hline \n".join(content) + end


    def generate_entry_point(self, output_file: pathlib.Path):
        validation_main_template = self._latex_renderer.get_template("main_template.tex")
        dates = []

        delta = self._conf.end_date - self._conf.start_date  # returns timedelta
        for i in range(delta.days + 1):
            date = self._conf.start_date + datetime.timedelta(days=i)
            dates.append(date)
        with open(output_file, "w") as f:
            f.write(validation_main_template.render(classname="interspeech", dates=dates))
