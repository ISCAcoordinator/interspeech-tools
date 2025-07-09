import datetime
import pathlib

from isca.model.core import ISCAObject
import jinja2

from isca.model.program import Room, Timeslot
from isca.model.person import Person
from isca.model.item import Paper
from isca.model.event import Conference


from .theme import (
    get_session_type,
)
from .jinja_helpers import configure_latex_jinja


class AbstractBookProcessor(ISCAObject):
    def __init__(self, conf: Conference):
        super().__init__()
        self._conf = conf
        if self._conf.program is None:
            raise Exception("The program of the conference should be defined")

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
                outfile.write("\n")

            # Generate the program content
            day_program_template = self._template_engine.get_template("day_program_template.tex")
            outfilename = root_output_dir / f"{date}.tex"
            with open(outfilename, "w") as outfile:
                outfile.write(day_program_template.render(sessions=self._conf.program.get_day_sessions(date)))
        reviewer_template = self._template_engine.get_template("reviewers_index_template.tex")
        outfilename = root_output_dir / "reviewers_index.tex"
        with open(outfilename, "w") as outfile:
            outfile.write(reviewer_template.render(reviewers=self._conf.reviewers))

        author_template = self._template_engine.get_template("authors_index_template.tex")
        outfilename = root_output_dir / "authors_index.tex"
        with open(outfilename, "w") as outfile:
            outfile.write(author_template.render(authors=self._conf.authors))

    def _generate_programme_table(
            self, timeslots: list[Timeslot], max_rooms_per_page:int = 10
    ) -> str:

        rooms = self._conf.program.rooms

        # retrieve the room names from the plan column names
        parts = []
        for firstCol in list(range(0, len(rooms)))[::max_rooms_per_page]:
            partial_rooms = rooms[firstCol : firstCol + max_rooms_per_page]
            table_part = self._generate_programme_table_part(timeslots, partial_rooms)
            parts.append(table_part)

        return "\n\n".join(parts)

    def _generate_programme_table_part(
            self, timeslots: list[Timeslot], rooms: list[Room]
    ):
        content = []

        nb_zones = len([r for r in rooms for _ in range(r.nb_zones)])
        # Prepare header
        timecolspec = "C{\\tabletimecolwidth}|"
        colspec = "C{\\tablecolwidth}|"
        header = f"\\begin{{tabular}}{{|{timecolspec}{''.join([colspec for _ in range(nb_zones)])}}} \\hline \n"

        rooms_latex = []
        for r in rooms:
            if r.nb_zones > 1:
                rooms_latex.append(f"\\multicolumn{{{r.nb_zones}}} {{c|}} {{\\cellcolor{{RoomCellColour}} \\textbf{{{r.name}}}}}")
            else:
                rooms_latex.append(f"\\cellcolor{{RoomCellColour}}\\textbf{{{r.name}}}")
        header += f"& {' & '.join(rooms_latex) } \\\\ \\hline \n"

        # Reorganize sessions per time_start (FIXME: this should be put up a bit)
        for timeslot in timeslots:
            self._logger.info(timeslot)
            sessions = self._conf.program.get_timeslot_sessions(timeslot)
            timeslot_str = timeslot.timeslot_without_date().replace(" ", "")
            elts = [timeslot_str]
            if not sessions:
                row = f"\\multicolumn{{{nb_zones}}}{{c|}}{{"
                row += timeslot.name
                row += "}"
                elts.append(row)
            elif len(sessions.keys()) == 1:
                sessions = sessions[list(sessions.keys())[0]]
                if len(sessions) > 1:
                    raise Exception("For now, only one session implies an overall session")
                session = sessions[0]
                session_type = get_session_type(session)
                row = f"\\multicolumn{{{nb_zones}}}{{c|}}{{"
                row += f"\\cellcolor{{{session_type.capitalize()}BackgroundColour}}{{\\color{{{session_type.capitalize()}ForegroundColour}}\\bf {session.name}}}"
                row += "}"
                elts.append(row)
            else:
                for room in rooms:
                    if room not in sessions:
                        elts.append("")
                        continue

                    room_sessions = sessions[room]
                    # FIXME: for now it is all or nothing. We don't support partial zones
                    if (room.nb_zones > 1) and (len(room_sessions) == 1):
                        session = room_sessions[0]
                        session_type = get_session_type(session)
                        session_name = session.name.replace("Special Session - ", "") # FIXME: this is hardcoded
                        elts.append(f"\\multicolumn{{{room.nb_zones}}} {{c|}} {{\\cellcolor{{{session_type.capitalize()}BackgroundColour}} {{\\color{{{session_type.capitalize()}ForegroundColour}} \\textbf{{{session_name}}}}}}}")
                    else:
                        for session in room_sessions:
                            session_type = get_session_type(session)
                            session_name = session.name.replace("Special Session - ", "") # FIXME: this is hardcoded
                            elts.append(f"\\cellcolor{{{session_type.capitalize()}BackgroundColour}}{{\\color{{{session_type.capitalize()}ForegroundColour}}\\bf {session_name}}}")

            content.append(' & '.join(elts))

        print(content)
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
