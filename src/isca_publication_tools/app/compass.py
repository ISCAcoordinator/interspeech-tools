import pathlib
import logging
import pandas as pd

from isca.model import Conference

class CompassDataGenerator:
    AGENDA_COLUMNS = [
        "id",
        "name",
        "subtitle",
        "subtitleDetail",
        "configuratorType",
        "info",
        "orderingName",
        "parent",
        "date",
        "startTime",
        "endTime",
        "classifierId_1"
    ]
    PERSON_COLUMNS = [
        "id",
	"name",
	"subtitle",
	"subtitleDetail",
	"configuratorType",
	"info",
	"orderingName",
	"email",
	"firstName",
	"lastName",
	"classifierId_"
    ]
    PLACE_COLUMNS = [
        "id",
        "name",
	"subtitle",
	"subtitleDetail",
	"configuratorType",
	"info",
	"orderingName",
	"exhibitorId"
    ]

    def __init__(self, conference: Conference):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.conference = conference


    def generate_data(self, output_root_dir: pathlib.Path):
        output_root_dir.mkdir(exist_ok=True, parents=True)
        self._generate_app_person(output_root_dir / "Persons.xlsx")
        self._generate_app_place(output_root_dir / "Places.xlsx")
        # self._generate_app_agenda(output_root_dir / "Timeslots.xlsx")
        # self._generate_app_institution(output_root_dir / "Institutions.xlsx")
        # self._generate_app_classifier(output_root_dir / "Classifiers.xlsx")

    def _generate_app_classifier(self, output_classifier_file: pathlib.Path) -> None:
        pass
    def _generate_app_institution(self, output_institution_file: pathlib.Path) -> None:
        pass

    def _generate_app_place(self, output_place_file: pathlib.Path) -> None:

        list_place = []
        for cur_room in self.conference.rooms:
            # Initialise the new session
            cur_place = {
                "id": cur_room.name,
                "name": cur_room.name,
                "configuratorType": "place:room"
            }
            list_place.append(cur_place)

        df_place = pd.DataFrame(list_place)
        for col_to_add in CompassDataGenerator.PLACE_COLUMNS:
            if col_to_add not in df_place.columns:
                df_place[col_to_add] = ""
        df_place = df_place.reindex(columns=CompassDataGenerator.PLACE_COLUMNS)
        # df_place.sort_values(by=["date", "endTime"], inplace=True)
        df_place.to_excel(output_place_file, index=False)

    def _generate_app_person(self, output_person_file: pathlib.Path) -> None:

        list_persons = []

        # List the authors
        authors = self.conference.authors
        for author in authors:
            cur_person = {
                "id": author.id,
                "email": author.email,
                "firstName": f"{author.firstname}".strip(),
                "lastName": author.lastname,
                # "Company": person_obj._organization,
                "configuratorType": "person:person",
            }

            # Entry is done
            list_persons.append(cur_person)



        # Save the generated dataframe to the excel file
        df_persons = pd.DataFrame(list_persons)
        for col_to_add in CompassDataGenerator.PERSON_COLUMNS:
            if col_to_add not in df_persons.columns:
                df_persons[col_to_add] = ""
        df_persons = df_persons.reindex(columns=CompassDataGenerator.PERSON_COLUMNS)
        df_persons.sort_values(by=["lastName", "firstName"], inplace=True)
        df_persons.to_excel(output_person_file, index=False)


    def _generate_app_agenda(self, output_agenda_file: pathlib.Path) -> None:
        raise NotImplementedError("This method is not yet implemented")
        # list_agenda = []
        # previous_row = ("", None)
        # cur_session = None
        # current_presenter_list = []

        # list_session_ids = self._programme.sessions.index.unique(level="SessionName")
        # header_sessions_df = self._programme.sessions[
        #     self._programme.sessions.index.get_level_values("SessionName").isin(list_session_ids) &
        #     (self._programme.sessions.index.get_level_values("Sequence") == 1)
        # ]
        # for session_id, session_info in header_sessions_df.iterrows():
        #     session_name, session_seq = session_id
        #     # Initialise the new session
        #     cur_session = {
        #         "id": session_name,  # NOTE: Empty as it will be filled by the APP designer
        #         "name": self._programme.template.loc[session_name, "SessionNameLong"],
        #         "placeId": session_info["Room"],
        #         "date": session_info["Start"].strftime("%d-%m-%y"),
        #         "startTime": session_info["Start"].strftime("%H:%M"),
        #         "endTime": session_info["End"].strftime("%H:%M"),
        #         "configuratorType": "timeslot:session"
        #     }

        #     chair1 = self._programme.template.loc[session_name, "Session Chair 1"]
        #     if not pd.isna(chair1):
        #         cur_session["roleId_role:chair_1"] = chair1

        #     chair2 = self._programme.template.loc[session_name, "Session Chair 2"]
        #     if not pd.isna(chair2):
        #         cur_session["roleId_role:chair_2"] = chair2

        #     list_agenda.append(cur_session)

        #     session_type = session_info['SlotPresentationFormat'].lower()
        #     if (session_type == "oral") or (session_type == "keynote"):
        #         session_type = "presentation"

        #     # Fill description (i.e., list of presentations) (FIXME: there is likely a better way of doing this)
        #     session_df = self._programme.sessions[
        #         self._programme.sessions.index.get_level_values("SessionName") == session_name
        #     ]
        #     description = ""
        #     speakers = []
        #     for presentation_id, presentation_info in session_df.iterrows():
        #         session_name, seq = presentation_id
        #         code = self._programme.session_short_name_map[session_name]
        #         start = presentation_info["Start"].strftime('%H:%M')
        #         end = presentation_info["End"].strftime('%H:%M')
        #         paper_id = presentation_info["Paper ID"]
        #         abstract = ""
        #         if pd.isna(paper_id) or (paper_id <= 0):
        #             title = presentation_info["Paper Title"]
        #             if pd.isna(title):
        #                 continue
        #         else:
        #             title = self._programme.submissions.loc[paper_id, "Paper Title"]

        #             # Add the abstract content
        #             if self._programme._with_abstract:
        #                 if (self._programme._abstract_dir / f"{paper_id:d}.txt").exists():
        #                     with open(self._programme._abstract_dir / f"{paper_id:d}.txt") as f_abstract:
        #                         abstract = f_abstract.read().strip()

        #         cur_session = {
        #             "id": f"{session_name}_{seq}",
        #             "name": title,
        #             "placeId": session_info["Room"],
        #             "date": session_info["Start"].strftime("%d-%m-%y"),
        #             "parent": session_name,
        #             "startTime": start,
        #             "endTime": end,
        #             "configuratorType": f"timeslot:{session_type}",
        #             "info": abstract
        #         }


        #         # Deal with speakers
        #         if not pd.isna(presentation_info["Presenter"]):
        #             presenter_emails = presentation_info["Presenter"].strip().lower()
        #             presenter_emails = presenter_emails.replace("(", "").replace(")", "").split(",")
        #             for i_speaker, speaker_id in enumerate(presenter_emails, 1):
        #                 cur_session[f"roleId_role:speaker_{i_speaker}"] = speaker_id

        #         # And authors
        #         if not (pd.isna(paper_id) or (paper_id <= 0)):
        #             author_emails = self._programme.submissions.loc[paper_id, "Author Emails"].lower().strip().replace("*", "").split("; ")
        #             for i_author, author_id in enumerate(author_emails, 1):
        #                 cur_session[f"roleId_role:author_{i_author}"] = author_id

        #         list_agenda.append(cur_session)

        # # Save the generated dataframe to the excel file
        # df_agenda = pd.DataFrame(list_agenda)
        # for col_to_add in CompassDataGenerator.AGENDA_COLUMNS:
        #     if col_to_add not in df_agenda.columns:
        #         df_agenda[col_to_add] = ""

        # # Added columns
        # columns = CompassDataGenerator.AGENDA_COLUMNS.copy()
        # for col_to_keep in df_agenda.columns:
        #     if col_to_keep not in columns:
        #         columns.append(col_to_keep)
        # df_agenda = df_agenda.reindex(columns=columns)
        # df_agenda.to_excel(output_agenda_file, index=False)
