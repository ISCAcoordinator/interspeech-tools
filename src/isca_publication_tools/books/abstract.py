import datetime
import pathlib

import jinja2

from isca.model.core import ISCAObject
from isca.model.session import Room, PresentationSession, Timeslot
from isca.model.person import Person
from isca.model.item import Paper
from isca.model.event import Conference


from .theme import (
    get_session_type,
)
from .jinja_helpers import configure_latex_jinja


class AbstractBookProcessor:
    def __init__(self, conf: Conference):
        self._conf = conf

        template_loader = jinja2.PackageLoader("isca_publication_tools", "resources/abstract_book")
        self._template_engine = configure_latex_jinja(template_loader)

        # Set conference specific filters
        def list_papers(author: Person) -> list[Paper]:
            return conf.list_papers(author)

        self._template_engine.filters["list_papers"] = list_papers

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
            day_program_template = self._template_engine.get_template("day_program_template.tex")
            outfilename = root_output_dir / f"{date}.tex"
            with open(outfilename, "w") as outfile:
                outfile.write(day_program_template.render(sessions=day_sessions))

        reviewer_template = self._template_engine.get_template("reviewers_index_template.tex")
        outfilename = root_output_dir / "reviewers_index.tex"
        with open(outfilename, "w") as outfile:
            outfile.write(reviewer_template.render(reviewers=self._conf.reviewers))

        author_template = self._template_engine.get_template("authors_index_template.tex")
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
        validation_main_template = self._template_engine.get_template("main_template.tex")
        dates = []

        delta = self._conf.end_date - self._conf.start_date  # returns timedelta
        for i in range(delta.days + 1):
            date = self._conf.start_date + datetime.timedelta(days=i)
            dates.append(date)
        with open(output_file, "w") as f:
            f.write(validation_main_template.render(classname="interspeech", dates=dates))
