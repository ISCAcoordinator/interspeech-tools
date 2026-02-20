import re
import pathlib
import pandas as pd
from trieregex import TrieRegEx as TRE
from interspeech_tools.conf import Config
from interspeech_tools.io.cmt import InterspeechCMTSerialiser

# Load the conference
input_file = pathlib.Path("../data/ForPublicationCommittee/config.yaml")
config = Config(input_file)
ser = InterspeechCMTSerialiser(config)
conference = ser.load()

sure = input("This scripts overwrite the data, are you sure (yes|no) you want to run it?")
if sure != "yes":
    import sys

    sys.exit(0)


# FIXME: for now the annuary is private, but need to think about a better integration
annuary = conference._annuary
flipped_alternative_emails = dict()
for alternative, reference in annuary.alternative_emails.items():
    if reference not in flipped_alternative_emails:
        flipped_alternative_emails[reference] = []
    flipped_alternative_emails[reference].append(alternative)

# Prepare the replacement dictionnary
replace_dict = {}
for person_idx, person in enumerate(annuary):
    list_emails = [person.email]
    if person.email in flipped_alternative_emails:
        for alternative in flipped_alternative_emails[person.email]:
            list_emails.append(alternative)

    tre = TRE(*list_emails)

    replace_dict[re.compile(tre.regex(), re.IGNORECASE)] = f"id{person_idx}@is.invalid"


def replace(input_str):
    for old, new in replace_dict.items():
        input_str = old.sub(new, input_str)
    return input_str


# Load data
input_root_dir = config["input_data"]["root_dir"]
for key in config["input_data"].keys():
    if not key.endswith("_spreadsheet"):
        continue

    if config["input_data"][key].startswith("/"):
        input_file = pathlib.Path(config["input_data"][key])
    else:
        input_file = input_root_dir / config["input_data"][key]

    # Replace in every sheet
    if input_file.exists():
        print(f"Anonymizing {input_file}")
        sheets = pd.read_excel(input_file, sheet_name=None)
        for sheet_name, df in sheets.items():
            df = df.map(lambda x: replace(x) if isinstance(x, str) else x)

            # Filter rows with people who are not in the annuary
            contains_at = df.astype(str).apply(lambda col: col.str.contains("@"))
            contains_allowed = df.astype(str).apply(lambda col: col.str.contains("@is.invalid"))
            rows_to_drop = contains_at.any(axis=1) & ~contains_allowed.any(axis=1)
            sheets[sheet_name] = df[~rows_to_drop]

        # Overwrite the excel file
        with pd.ExcelWriter(input_file, engine="xlsxwriter") as writer:
            for sheet_name, df in sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        print(f"{input_file} doesn't exist and is therefore ignored!")
