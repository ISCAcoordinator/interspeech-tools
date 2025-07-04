import datetime
import pathlib

import jinja2

from isca.model.core import ISCAObject
from isca.model.session import Room, PresentationSession
from isca.model.person import Person
from isca.model.item import Paper
from isca.model.event import Conference


from ..books.utils import (
    latexify,
)
from ..books.filters import(
    sort_by_last_name,
    sort_by_name,
    get_latexified_authors,
    get_latexified_presenters,
    is_presentation,
    has_paper,
    is_presentation_survey,
    is_presentation_bluesky,
    get_presentation_type,
    get_session_type,
    extract_date,
    extract_verbose_date,
    get_session_timeslot,
    get_presentation_timeslot,
    compact_number
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

        rooms_sessions = self._conf.associate_sessions_to_rooms()
        root_output_dir.mkdir(exist_ok=True, parents=True)
        delta = self._conf.end_date - self._conf.start_date   # returns timedelta
        for i in range(delta.days + 1):
            date = self._conf.start_date + datetime.timedelta(days=i)
            outfilename = root_output_dir / f"{date}_table.tex"

            # Subset the rooms/sessions to a given date
            day_sessions = []
            day_rooms_sessions = dict()
            for r, sessions in rooms_sessions.items():
                cur_room_sessions = []
                for cur_session in sessions:
                    if cur_session.start.date() == date:
                        cur_room_sessions.append(cur_session)
                        day_sessions.append(cur_session)
                if cur_room_sessions:
                    day_rooms_sessions[r] = cur_room_sessions

            with open(outfilename, "w") as outfile:
                outfile.write(self._generate_programme_table(date, day_rooms_sessions))


            day_sessions = sorted(day_sessions, key=lambda x: x.start)
            day_program_template = self._latex_renderer.get_template("day_program_template.tex")
            outfilename = root_output_dir / f"{date}.tex"
            with open(outfilename, "w") as outfile:
                outfile.write(day_program_template.render(sessions=day_sessions))

        # outfilename = root_output_dir / "paper_index.tex"
        # with open(outfilename, "w") as outfile:
        #     outfile.write(self._generate_submissions_index())

        reviewer_template = self._latex_renderer.get_template("reviewers_index_template.tex")
        outfilename = root_output_dir / "reviewers_index.tex"
        with open(outfilename, "w") as outfile:
            outfile.write(reviewer_template.render(reviewers = self._conf.reviewers))

        # outfilename = root_output_dir / "presenter_index.tex"
        # with open(outfilename, "w") as outfile:
        #     outfile.write(self._generate_presenter_index())

        author_template = self._latex_renderer.get_template("authors_index_template.tex")
        outfilename = root_output_dir / "authors_index.tex"
        with open(outfilename, "w") as outfile:
            outfile.write(author_template.render(authors = self._conf.authors))

    def _generate_programme_table(self, date: datetime.date, rooms_sessions: dict[Room, list[PresentationSession]]) -> str:

        # retrieve the room names from the plan column names
        rooms = list(rooms_sessions.keys())
        content = ""
        maxColsPerPage = 10
        parts = []
        multicolumnRows = {}
        for firstCol in list(range(0,len(rooms)))[::maxColsPerPage]:
            part_rooms = rooms[firstCol:firstCol+maxColsPerPage]
            part_rooms_sessions = dict()
            for r in part_rooms:
                part_rooms_sessions[r] = rooms_sessions[r]

            newPart = self._generate_programme_table_part(date, part_rooms_sessions)
            parts.append(newPart)
            for lineNumber, line in newPart['multicolumnRows'].items():
                multicolumnRows[lineNumber] = line

        content = ''
        for part in parts:
            for lineNumber, line in multicolumnRows.items():
                part['content'][lineNumber] = line['start'] + f"\\multicolumn{{{part['width']}}}{{c|}}{{{line['value']}}}"
            content += part['start'] + ' \\\\ \\hline \n'.join(part['content']) + ' \\\\ \\hline \n' + part['end'] + '\n\n'
        return content


    def _generate_programme_table_part(self, date: datetime.date, rooms_sessions: dict[Room, list[PresentationSession]]):
        content = []
        multicolumnRows = {}
        rooms = list(rooms_sessions.keys())

        # Reorganize sessions per time_start (FIXME: this should be put up a bit)
        sorted_sessions = {}
        for r, sessions in rooms_sessions.items():
            for cur_session in sessions:
                start = cur_session.start
                if start not in sorted_sessions:
                    sorted_sessions[start] = dict()
                sorted_sessions[start][r] = cur_session

        content = []
        for start, elts in sorted_sessions.items():


            row_val = [""]
            for r in rooms:
                if r in elts:
                    session = elts[r]
                    session_type = get_session_type(session)
                    cell_val = f"\\cellcolor{{{session_type.capitalize()}BackgroundColour}}{{\\color{{{session_type.capitalize()}ForegroundColour}}\\bf {session.name}}}"
                    row_val.append(cell_val)
                else:
                    row_val.append("")
            content.append(" & ".join(row_val))

        timecolspec = "C{\\tabletimecolwidth}|"
        colspec = "C{\\tablecolwidth}|"
        rooms_latex = [f"\\cellcolor{{RoomCellColour}}\\textbf{{{r.name}}}" for r in rooms]
        rval = f"\\begin{{tabular}}{{|{timecolspec}{''.join([colspec for _ in rooms])}}} \\hline \n"
        rval += f"& {' & '.join(rooms_latex) } \\\\ \\hline \n"

        return {'start': rval, 'content': content, 'end': "\\end{tabular}", 'multicolumnRows': multicolumnRows, 'width': len(rooms_latex)}

    def generate_entry_point(self, output_file: pathlib.Path):
        validation_main_template = self._latex_renderer.get_template("main_template.tex")
        dates = []

        delta = self._conf.end_date - self._conf.start_date   # returns timedelta
        for i in range(delta.days + 1):
            date = self._conf.start_date + datetime.timedelta(days=i)
            dates.append(date)
        with open(output_file, "w") as f:
            f.write(validation_main_template.render(classname="interspeech", dates=dates))
