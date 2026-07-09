from collections import defaultdict
import datetime
import pathlib
import shutil

from isca.model.core import ISCAObject
from isca.model.item import Session
import jinja2

from isca.model.program import KeynoteSession, OralSession, PosterSession, Room, Timeslot, Presentation
from isca.model.person import Person, Speaker

from ...conf import Config
from ...model import Interspeech, InterspeechEvent, LongSession, ShowAndTellSession, SpecialSession, TutorialSession

from .theme import (
    get_session_type,
)
from .jinja_helpers import configure_latex_jinja, format_timeslot


def is_content_session(input_session: Session) -> bool:
    return (
        isinstance(input_session, KeynoteSession)
        or isinstance(input_session, OralSession)
        or isinstance(input_session, LongSession)
        or isinstance(input_session, PosterSession)
        or isinstance(input_session, SpecialSession)
        or isinstance(input_session, ShowAndTellSession)
    )


class AbstractBookProcessor(ISCAObject):
    def __init__(self, config: Config, conference: Interspeech):
        super().__init__()
        self._conf = conference
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

        self._config = config

    def process(self, root_output_dir: pathlib.Path, draft: bool = False) -> None:

        root_output_dir.mkdir(exist_ok=True, parents=True)

        # core program
        delta = self._conf.end_date - self._conf.start_date  # returns timedelta
        content_dates = []
        for i in range(delta.days + 1):
            date = self._conf.start_date + datetime.timedelta(days=i)
            outfilename = root_output_dir / f"{date}_table.tex"

            # Generate the program table
            day_timeslots = self._conf.get_timeslots(date)
            print(day_timeslots)
            with open(outfilename, "w") as outfile:
                outfile.write(self._generate_programme_table(day_timeslots))
                outfile.write("\n")

            # Get the sessions
            sessions = self._conf.program.get_day_sessions(date)
            sessions = [s for s in sessions if is_content_session(s[0])]

            # Generate the program content
            if sessions:
                content_dates.append(date)

                # Reorganise the sessions to find the duplicate places
                rendering_sessions = []
                for session, timeslot, room, z_idx in sessions:
                    if (len(rendering_sessions) >= 1) and (rendering_sessions[-1][0] == session):
                        if room not in rendering_sessions[-1][-1]:
                            rendering_sessions[-1][-1][room] = []
                        rendering_sessions[-1][-1][room].append(room.zones[z_idx])
                    else:
                        rendering_sessions.append([session, timeslot, {room: [room.zones[z_idx]]}])

                # Render the place as strings
                for i_session, session in enumerate(rendering_sessions):
                    areas = session[-1]
                    places = []
                    for room, zones in areas.items():
                        if room.nb_zones == 1:
                            places.append(room.name)
                        else:
                            cur_place = room.name + " - " + ",".join(zones)
                            places.append(cur_place)

                    session[-1] = "; ".join(places)
                    rendering_sessions[i_session] = session

                day_program_template = self._template_engine.get_template("day_program.tex.jinja2")
                outfilename = root_output_dir / f"{date}.tex"
                with open(outfilename, "w") as outfile:
                    outfile.write(day_program_template.render(sessions=rendering_sessions, draft=draft))

        # Copy photos
        for person in self._conf._annuary:
            if isinstance(person, Speaker):
                if (person.photo is not None) and person.photo.exists():
                    self.logger.debug(f"Copy speaker photo {person.photo} to {root_output_dir/person.photo.name}")
                    shutil.copy(person.photo, root_output_dir / person.photo.name)

        # Best student papers
        if self._config["output"]["parts"]["best_student_papers"]:
            best_students = self._template_engine.get_template("best_papers.tex.jinja2")
            outfilename = root_output_dir / "best_student.tex"
            with open(outfilename, "w") as outfile:
                outfile.write(
                    best_students.render(presentations=self._conf.list_student_award_nominees_presentations(), draft=draft)
                )

        # Best theme papers
        if self._config["output"]["parts"]["best_theme_papers"]:
            best_themes = self._template_engine.get_template("best_papers.tex.jinja2")
            outfilename = root_output_dir / "best_theme.tex"
            with open(outfilename, "w") as outfile:
                outfile.write(best_themes.render(presentations=self._conf.list_theme_award_nominees_presentations(), draft=draft))

        # Tutorials
        if self._config["output"]["parts"]["tutorials"]:
            tutorial_template = self._template_engine.get_template("tutorials.tex.jinja2")
            outfilename = root_output_dir / "tutorials.tex"
            tutorials = self._conf.program.select_sessions(lambda s, t, r, z: isinstance(s, TutorialSession))
            with open(outfilename, "w") as outfile:
                outfile.write(tutorial_template.render(tutorial_sessions=tutorials, draft=draft))

        # Keynotes
        if self._config["output"]["parts"]["keynotes"]:
            keynote_template = self._template_engine.get_template("keynotes.tex.jinja2")
            keynote_sessions = self._conf.program.select_sessions(lambda s, t, r, z: isinstance(s, KeynoteSession))
            outfilename = root_output_dir / "keynotes.tex"
            with open(outfilename, "w") as outfile:
                outfile.write(keynote_template.render(sessions=keynote_sessions, draft=draft))

        # Surveys
        if self._config["output"]["parts"]["surveys"]:
            surveys_template = self._template_engine.get_template("surveys.tex.jinja2")
            outfilename = root_output_dir / "surveys.tex"
            with open(outfilename, "w") as outfile:
                outfile.write(surveys_template.render(sessions=self._conf.program.sessions, draft=draft))

        # Special Sessions
        if self._config["output"]["parts"]["special_sessions"]:
            special_sessions_template = self._template_engine.get_template("special_sessions.tex.jinja2")
            outfilename = root_output_dir / "special_sessions.tex"
            special_sessions = self._conf.program.select_sessions(lambda s, t, r, z: isinstance(s, SpecialSession))
            with open(outfilename, "w") as outfile:
                outfile.write(special_sessions_template.render(sessions=special_sessions, draft=draft))

        # Satellites
        if self._config["output"]["parts"]["satellites"]:
            satellites_template = self._template_engine.get_template("satellite_events.tex.jinja2")
            outfilename = root_output_dir / "satellite_events.tex"
            with open(outfilename, "w") as outfile:
                outfile.write(satellites_template.render(events=self._conf.satellite_events, draft=draft))

        # Reviewer index
        if self._config["output"]["parts"]["reviewers"]:
            reviewer_template = self._template_engine.get_template("reviewers_index.tex.jinja2")
            outfilename = root_output_dir / "reviewers_index.tex"
            with open(outfilename, "w") as outfile:
                outfile.write(reviewer_template.render(reviewers=self._conf.reviewers, draft=draft))

        # Author index
        author_template = self._template_engine.get_template("authors_index.tex.jinja2")
        outfilename = root_output_dir / "authors_index.tex"
        with open(outfilename, "w") as outfile:
            outfile.write(author_template.render(conf=self._conf, authors=self._conf.authors, draft=draft))

    def _generate_programme_table(self, timeslots: list[Timeslot], max_zones_per_page: int = 7) -> str:

        rooms = self._conf.program.rooms

        parts = []
        room_indices = []
        cur_nb_zones = 0
        ignored_sessions = []

        # Add the ignored timeslots sessions
        timeslot_sessions = {timeslot: self._conf.program.get_timeslot_sessions(timeslot) for timeslot in timeslots}
        for timeslot, room_session in timeslot_sessions.items():
            if timeslot in self._conf.ignored_timeslots:
                for room, sessions in room_session.items():
                    for zone_idx, session in sessions.items():
                        ignored_sessions.append([session, timeslot, room, zone_idx])

        for room_idx, room in enumerate(rooms):
            if room in self._conf.ignored_rooms:
                for timeslot, room_session in timeslot_sessions.items():
                    if room in room_session:
                        for zone_idx, session in room_session[room].items():
                            ignored_sessions.append([session, timeslot, room, zone_idx])
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
        excluded = ""
        excluded_sessions = []
        for session, timeslot, room, zone_idx in ignored_sessions:
            session_type = get_session_type(session)
            session_id = session.id if (not isinstance(session, InterspeechEvent)) and (session_type != "social") else ""
            excluded_session = (
                f"\\noindent + {format_timeslot(timeslot)} \\hyperlink{{{session_id}}}{{{session.name}}} [{room.name}]"
            )
            excluded_sessions.append(excluded_session)

        if excluded_sessions:
            excluded = "\\vspace{2mm}\\\\ \n"
            excluded += "\\\\ \n \\vspace{1mm} \\\\ \n".join(excluded_sessions)

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

            #
            no_sessions = True
            for room in rooms:
                if (room in sessions) and (room not in self._conf.ignored_rooms):
                    no_sessions = False
                    break

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
                    rows.append(row)
                continue

            # Overarching session (FIXME: room type in string => should be set into a enum type)
            room = list(sessions.keys())[0]
            if (len(sessions.keys()) == 1) and ((room.type.lower() == "plenary") or (room.type.lower() == "social")):
                sessions = sessions[room]
                if len(sessions) > 1:
                    raise Exception("Plenary room & social room do not support more than one zone")

                session = sessions[list(sessions.keys())[0]]
                session_type = get_session_type(session)
                session_id = session.id if (not isinstance(session, InterspeechEvent)) and (session_type != "social") else ""

                row["elts"].append(
                    {
                        "type": "multicolumn",
                        "colspan": nb_zones,
                        "content": {
                            "id": session_id,
                            "name": f"{session.name} [{room.name}]",
                            "bg": f"{session_type.replace('_', ' ').title().replace(' ', '')}BackgroundColour",
                            "fg": f"{session_type.replace('_', ' ').title().replace(' ', '')}ForegroundColour",
                        },
                    }
                )
                rows.append(row)
                continue

            # Standard session
            else:
                # Flatten room and zones:
                flatten_rooms_zones = [(room, zone) for room in rooms for zone in range(room.nb_zones)]

                buffer_session = None
                for i_area, (room, zone) in enumerate(flatten_rooms_zones):
                    session = None
                    if (room in sessions) and (zone in sessions[room]):
                        session = sessions[room][zone]

                    # If we are currently part of a sliding session, just keep/update it in the buffer
                    if ((i_area + 1) < len(flatten_rooms_zones)) and (session is not None):
                        next_zone = flatten_rooms_zones[i_area + 1]
                        next_session = None
                        if (next_zone[0] in sessions) and (next_zone[1] in sessions[room]):
                            next_session = sessions[next_zone[0]][next_zone[1]]

                        if (next_session is not None) and (session.id == next_session.id):
                            if buffer_session is not None:
                                buffer_session["colspan"] += 1
                                raise Exception("ok?")
                            else:
                                session_type = get_session_type(session)
                                session_name = session.name.replace("Special Session - ", "")
                                session_id = (
                                    session.id
                                    if (not isinstance(session, InterspeechEvent)) and (session_type != "social")
                                    else ""
                                )
                                buffer_session = {
                                    "colspan": 1,
                                    "session_id": session_id,
                                    "session_name": session_name,
                                    "color_id": session_type.replace("_", " ").title().replace(" ", ""),
                                }

                            continue

                    # If there was a buffered session, add it to the table
                    if buffer_session is not None:
                        session_name = buffer_session["session_name"]
                        if len(session_name) > self._config["output"]["abstract_book"]["max_session_name_size_multicol"]:
                            session_name = (
                                session_name[: self._config["output"]["abstract_book"]["max_session_name_size_multicol"] - 3]
                                + "..."
                            )

                        row["elts"].append(
                            {
                                "type": "multicolumn",
                                "colspan": buffer_session["colspan"] + 1,
                                "content": {
                                    "id": buffer_session["session_id"],
                                    "name": session_name,
                                    "bg": f"{buffer_session['color_id']}BackgroundColour",
                                    "fg": f"{buffer_session['color_id']}ForegroundColour",
                                },
                            }
                        )

                        buffer_session = None
                    else:
                        # Now focus on the actual zone
                        if session is None:
                            row["elts"].append({"type": "empty"})
                        else:
                            session_type = get_session_type(session)
                            session_name = session.name.replace("Special Session - ", "")
                            session_id = (
                                session.id if (not isinstance(session, InterspeechEvent)) and (session_type != "social") else ""
                            )

                            row["elts"].append(
                                {
                                    "type": "cell",
                                    "content": {
                                        "id": session_id,
                                        "name": session_name,
                                        "bg": f"{session_type.replace('_', ' ').title().replace(' ', '')}BackgroundColour",
                                        "fg": f"{session_type.replace('_', ' ').title().replace(' ', '')}ForegroundColour",
                                    },
                                }
                            )

                if buffer_session is not None:
                    session_name = buffer_session["session_name"]
                    if len(session_name) > self._config["output"]["abstract_book"]["max_session_name_size_multicol"]:
                        session_name = (
                            session_name[: self._config["output"]["abstract_book"]["max_session_name_size_multicol"] - 3] + "..."
                        )

                    row["elts"].append(
                        {
                            "type": "multicolumn",
                            "colspan": buffer_session["colspan"],
                            "content": {
                                "id": buffer_session["session_id"],
                                "name": session_name,
                                "bg": f"{buffer_session['color_id']}BackgroundColour",
                                "fg": f"{buffer_session['color_id']}ForegroundColour",
                            },
                        }
                    )
                rows.append(row)

        # Render the template
        template = self._template_engine.get_template("program_table.tex.jinja2")
        return template.render(nb_zones=nb_zones, rooms=rooms, rows=rows)

    def generate_entry_point(self, output_file: pathlib.Path, draft: bool = False):
        main_template = self._template_engine.get_template("main.tex.jinja2")
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
            f.write(
                main_template.render(
                    classname="interspeech",
                    conf_name=self._conf.name,
                    dates=dates,
                    content_dates=content_dates,
                    draft=draft,
                    conf=self._config,
                )
            )
