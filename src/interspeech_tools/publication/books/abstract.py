import datetime
import pathlib
import shutil

from isca.model.core import ISCAObject
from isca.model.item import Session
import jinja2

from isca.model.program import KeynoteSession, OralSession, PosterSession, Room, Timeslot, Presentation
from isca.model.person import Person, Speaker


from ...model import Interspeech, ShowAndTellSession, SpecialSession, TutorialSession

from .theme import (
    get_session_type,
)
from .jinja_helpers import configure_latex_jinja


def is_content_session(input_session: Session) -> bool:
    return (
        isinstance(input_session, KeynoteSession)
        or isinstance(input_session, OralSession)
        or isinstance(input_session, PosterSession)
        or isinstance(input_session, SpecialSession)
        or isinstance(input_session, ShowAndTellSession)
    )


class AbstractBookProcessor(ISCAObject):
    def __init__(self, conf: Interspeech):
        super().__init__()
        self._conf = conf
        if self._conf.program is None:
            raise Exception("The program of the conference should be defined")

        template_loader = jinja2.PackageLoader("interspeech_tools.publication", "resources/abstract_book")
        self._template_engine = configure_latex_jinja(template_loader)

        self._author2presentations = self._conf.program.authors2presentations()
        # Set conference specific filters

        def list_presentations(author: Person) -> list[Presentation]:
            if author not in self._author2presentations:
                return []
            return self._author2presentations[author]

        self._template_engine.filters["list_presentations"] = list_presentations

    def process(self, root_output_dir: pathlib.Path) -> None:

        root_output_dir.mkdir(exist_ok=True, parents=True)

        # core program
        delta = self._conf.end_date - self._conf.start_date  # returns timedelta
        content_dates = []
        for i in range(delta.days + 1):
            date = self._conf.start_date + datetime.timedelta(days=i)
            outfilename = root_output_dir / f"{date}_table.tex"

            # Generate the program table
            day_timeslots = self._conf.get_timeslots(date)
            with open(outfilename, "w") as outfile:
                outfile.write(self._generate_programme_table(day_timeslots))
                outfile.write("\n")

            # Get the sessions
            sessions = self._conf.program.get_day_sessions(date)
            sessions = [s for s in sessions if is_content_session(s[0])]

            # Generate the program content
            if sessions:
                content_dates.append(date)
                day_program_template = self._template_engine.get_template("day_program.tex.jinja2")
                outfilename = root_output_dir / f"{date}.tex"
                with open(outfilename, "w") as outfile:
                    outfile.write(day_program_template.render(sessions=sessions))

        # Copy photos
        for person in self._conf._annuary:
            if isinstance(person, Speaker):
                if (person.photo is not None) and person.photo.exists():
                    self.logger.debug(f"Copy speaker photo {person.photo} to {root_output_dir/person.photo.name}")
                    shutil.copy(person.photo, root_output_dir / person.photo.name)

        # Best student papers
        best_students = self._template_engine.get_template("best_papers.tex.jinja2")
        outfilename = root_output_dir / "best_student.tex"
        with open(outfilename, "w") as outfile:
            outfile.write(best_students.render(papers=self._conf.best_student_papers_nominees))

        # Best theme papers
        best_themes = self._template_engine.get_template("best_papers.tex.jinja2")
        outfilename = root_output_dir / "best_theme.tex"
        with open(outfilename, "w") as outfile:
            outfile.write(best_themes.render(papers=self._conf.best_theme_papers_nominees))

        # Tutorials
        tutorial_template = self._template_engine.get_template("tutorials.tex.jinja2")
        outfilename = root_output_dir / "tutorials.tex"
        tutorials = self._conf.program.select_sessions(lambda t, r, s: isinstance(s, TutorialSession))
        with open(outfilename, "w") as outfile:
            outfile.write(tutorial_template.render(tutorial_sessions=tutorials))

        # Keynotes
        keynote_template = self._template_engine.get_template("keynotes.tex.jinja2")
        outfilename = root_output_dir / "keynotes.tex"
        with open(outfilename, "w") as outfile:
            outfile.write(keynote_template.render(sessions=self._conf.sessions))

        # Surveys
        surveys_template = self._template_engine.get_template("surveys.tex.jinja2")
        outfilename = root_output_dir / "surveys.tex"
        with open(outfilename, "w") as outfile:
            outfile.write(surveys_template.render(sessions=self._conf.sessions))

        # Special Sessions
        special_sessions_template = self._template_engine.get_template("special_sessions.tex.jinja2")
        outfilename = root_output_dir / "special_sessions.tex"
        with open(outfilename, "w") as outfile:
            outfile.write(special_sessions_template.render(sessions=self._conf.sessions))

        # Reviewer index
        reviewer_template = self._template_engine.get_template("reviewers_index.tex.jinja2")
        outfilename = root_output_dir / "reviewers_index.tex"
        with open(outfilename, "w") as outfile:
            outfile.write(reviewer_template.render(reviewers=self._conf.reviewers))

        # Author index
        author_template = self._template_engine.get_template("authors_index.tex.jinja2")
        outfilename = root_output_dir / "authors_index.tex"
        with open(outfilename, "w") as outfile:
            outfile.write(author_template.render(conf=self._conf, authors=self._conf.authors))

    def _generate_programme_table(self, timeslots: list[Timeslot], max_rooms_per_page: int = 10) -> str:

        rooms = self._conf.program.rooms

        # retrieve the room names from the plan column names
        parts = []
        for firstCol in list(range(0, len(rooms)))[::max_rooms_per_page]:
            partial_rooms = rooms[firstCol : firstCol + max_rooms_per_page]
            table_part = self._generate_programme_table_part(timeslots, partial_rooms)
            parts.append(table_part)

        return "\n\n".join(parts)

    def _generate_programme_table_part(self, timeslots: list[Timeslot], rooms: list[Room]):
        nb_zones = sum(r.nb_zones for r in rooms)
        rows = []

        for timeslot in timeslots:
            sessions = self._conf.program.get_timeslot_sessions(timeslot)
            row = {"timeslot_str": timeslot.timeslot_without_date().replace(" ", ""), "elts": []}

            if not sessions:
                row["elts"].append({"type": "multicolumn", "colspan": nb_zones, "content": timeslot.name})
            elif len(sessions.keys()) == 1:
                sessions = sessions[list(sessions.keys())[0]]
                if len(sessions) > 1:
                    raise Exception("For now, only one session implies an overall session")
                session = sessions[0]
                session_type = get_session_type(session)
                row["elts"].append(
                    {
                        "type": "multicolumn",
                        "colspan": nb_zones,
                        "content": {
                            "id": session.id,
                            "name": session.name,
                            "bg": f"{session_type.capitalize()}BackgroundColour",
                            "fg": f"{session_type.capitalize()}ForegroundColour",
                        },
                    }
                )
            else:
                for room in rooms:
                    if room not in sessions:
                        row["elts"].append({"type": "empty"})
                        continue

                    room_sessions = sessions[room]
                    if room.nb_zones > 1 and len(room_sessions) == 1:
                        session = room_sessions[0]
                        session_type = get_session_type(session)
                        session_name = session.name.replace("Special Session - ", "")
                        row["elts"].append(
                            {
                                "type": "multicolumn",
                                "colspan": room.nb_zones,
                                "content": {
                                    "id": session.id,
                                    "name": session_name,
                                    "bg": f"{session_type.capitalize()}BackgroundColour",
                                    "fg": f"{session_type.capitalize()}ForegroundColour",
                                },
                            }
                        )
                    else:
                        for session in room_sessions:
                            session_type = get_session_type(session)
                            session_name = session.name.replace("Special Session - ", "")
                            row["elts"].append(
                                {
                                    "type": "cell",
                                    "content": {
                                        "id": session.id,
                                        "name": session_name,
                                        "bg": f"{session_type.capitalize()}BackgroundColour",
                                        "fg": f"{session_type.capitalize()}ForegroundColour",
                                    },
                                }
                            )

            rows.append(row)

        # Render the template
        template = self._template_engine.get_template("program_table.tex.jinja2")
        return template.render(nb_zones=nb_zones, rooms=rooms, rows=rows)

    def generate_entry_point(self, output_file: pathlib.Path):
        validation_main_template = self._template_engine.get_template("main.tex.jinja2")
        dates = []

        delta = self._conf.end_date - self._conf.start_date  # returns timedelta
        for i in range(delta.days + 1):
            date = self._conf.start_date + datetime.timedelta(days=i)

        # core program
        delta = self._conf.end_date - self._conf.start_date  # returns timedelta
        content_dates = []
        for i in range(delta.days + 1):
            date = self._conf.start_date + datetime.timedelta(days=i)
            dates.append(date)

            # Get the sessions
            sessions = self._conf.program.get_day_sessions(date)
            sessions = [s for s in sessions if is_content_session(s[0])]
            if sessions:
                content_dates.append(date)

        with open(output_file, "w") as f:
            f.write(validation_main_template.render(classname="interspeech", dates=dates, content_dates=content_dates))
