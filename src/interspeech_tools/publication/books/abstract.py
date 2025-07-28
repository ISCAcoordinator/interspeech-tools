from collections import defaultdict
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
    MAX_SESSION_NAME_SIZE_MULTICOL = 20

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
            outfile.write(best_students.render(presentations=self._conf.list_student_award_nominees_presentations()))

        # Best theme papers
        best_themes = self._template_engine.get_template("best_papers.tex.jinja2")
        outfilename = root_output_dir / "best_theme.tex"
        with open(outfilename, "w") as outfile:
            outfile.write(best_themes.render(presentations=self._conf.list_theme_award_nominees_presentations()))

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

    def _generate_programme_table(self, timeslots: list[Timeslot], max_zones_per_page: int = 7) -> str:

        rooms = self._conf.program.rooms

        parts = []
        room_indices = []
        cur_nb_zones = 0
        for room_idx, room in enumerate(rooms):
            if room in self._conf.ignored_rooms:
                continue
            room_indices.append(room_idx)
            for _ in range(0, room.nb_zones):
                cur_nb_zones += 1
                if cur_nb_zones > max_zones_per_page:
                    room_indices.remove(room_idx)
                    partial_rooms = [rooms[i] for i in room_indices]
                    table_part = self._generate_programme_table_part(timeslots, partial_rooms)
                    if table_part is not None:
                        parts.append(table_part)
                    room_indices = [room_idx]
                    cur_nb_zones = room.nb_zones
                    break

        if room_indices:
            partial_rooms = [rooms[i] for i in room_indices]
            table_part = self._generate_programme_table_part(timeslots, partial_rooms)
            if table_part is not None:
                parts.append(table_part)

        tables = "\n\n".join(parts)

        # TODO: this is just a place holder for now
        excluded = "\\vspace{2mm}\\\\"
        excluded += "+ 14:30--16:30 \\hyperlink{Mon-S1}{Special Session: Assessing and Mitigating AI Bias in Speech Processing Systems (Panel Discussion)} [Wicklow Meeting Room 1] \\\\"
        excluded += "\\vspace{1mm}"
        excluded += (
            "+ 14:30--16:30 \\hyperlink{Mon-SaT}{Show and Tell: Health applications and emotion recognition} [Show and Tell Area]"
        )
        content = tables + excluded
        return content

    def _generate_programme_table_part(self, timeslots: list[Timeslot], rooms: list[Room]) -> str | None:

        # Filter rooms
        room_usage = defaultdict(list)
        timeslot_sessions = {timeslot: self._conf.program.get_timeslot_sessions(timeslot) for timeslot in timeslots}
        for timeslot, sessions in timeslot_sessions.items():
            active_rooms = list(sessions.keys()) if sessions else []
            for room in active_rooms:
                room_usage[room].append((timeslot, len(active_rooms)))

        kept_rooms = []
        for room in rooms:
            usage = room_usage.get(room, [])
            if any(count > 1 for (_, count) in usage):
                kept_rooms.append(room)

        rooms = kept_rooms
        nb_zones = sum(r.nb_zones for r in rooms)

        if nb_zones == 0:
            return None

        rows = []
        for timeslot in timeslots:
            if timeslot in self._conf.ignored_timeslots:
                continue

            sessions = self._conf.program.get_timeslot_sessions(timeslot)
            row = {"timeslot_str": timeslot.timeslot_without_date().replace(" ", ""), "elts": []}

            no_sessions = True
            for room in rooms:
                if (room in sessions) and (room not in self._conf.ignored_rooms):
                    no_sessions = False
                    break

            # Save the plenary sessions and the social ones
            if no_sessions:
                for room in sessions.keys():
                    if ((room.type.lower() == "plenary") or (room.type.lower() == "social")) and (
                        room not in self._conf.ignored_rooms
                    ):
                        no_sessions = False
                        break

            if no_sessions:
                if str(timeslot.type).lower().endswith("break"):
                    row["elts"].append(
                        {
                            "type": "multicolumn",
                            "colspan": nb_zones,
                            "content": {
                                "id": "",
                                "name": timeslot.name,
                                "bg": "BreakBackgroundColour",
                                "fg": "BreakForegroundColour",
                            },
                        }
                    )
                else:
                    continue
            elif len(sessions.keys()) == 1:
                room = list(sessions.keys())[0]
                # FIXME: not sure that the type should be hardcoded like that in a string format
                if (room.type.lower() == "plenary") or (room.type.lower() == "social"):
                    sessions = sessions[room]
                    if len(sessions) > 1:
                        raise Exception("For now, only one session implies an overall session")

                    session = sessions[0]
                    session_type = get_session_type(session)
                    row["elts"].append(
                        {
                            "type": "multicolumn",
                            "colspan": nb_zones,
                            "content": {
                                "id": session.id if (session_type != "social") else "",
                                "name": f"{session.name} [{room.name}]",
                                "bg": f"{session_type.capitalize()}BackgroundColour",
                                "fg": f"{session_type.capitalize()}ForegroundColour",
                            },
                        }
                    )
                else:
                    for room in rooms:
                        if room not in sessions:
                            for _ in range(room.nb_zones):
                                row["elts"].append({"type": "empty"})
                            continue

                        room_sessions = sessions[room]
                        if room.nb_zones > 1 and len(room_sessions) == 1:
                            session = room_sessions[0]
                            session_type = get_session_type(session)
                            session_name = session.name.replace("Special Session - ", "")
                            if len(session_name) > AbstractBookProcessor.MAX_SESSION_NAME_SIZE_MULTICOL:
                                session_name = session_name[: AbstractBookProcessor.MAX_SESSION_NAME_SIZE_MULTICOL - 3] + "..."
                            row["elts"].append(
                                {
                                    "type": "multicolumn",
                                    "colspan": room.nb_zones,
                                    "content": {
                                        "id": session.id if (session_type != "social") else "",
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
                                            "id": session.id if (session_type != "social") else "",
                                            "name": session_name,
                                            "bg": f"{session_type.capitalize()}BackgroundColour",
                                            "fg": f"{session_type.capitalize()}ForegroundColour",
                                        },
                                    }
                                )

            else:
                # FIXME: it is a bit dirty but if no sessions available here, let's just not print the slot :)
                for room in rooms:
                    if room not in sessions:
                        for _ in range(room.nb_zones):
                            row["elts"].append({"type": "empty"})
                        continue

                    room_sessions = sessions[room]
                    if room.nb_zones > 1 and len(room_sessions) == 1:
                        session = room_sessions[0]
                        session_type = get_session_type(session)

                        session_name = session.name.replace("Special Session - ", "")
                        if len(session_name) > AbstractBookProcessor.MAX_SESSION_NAME_SIZE_MULTICOL:
                            session_name = session_name[: AbstractBookProcessor.MAX_SESSION_NAME_SIZE_MULTICOL - 3] + "..."

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
