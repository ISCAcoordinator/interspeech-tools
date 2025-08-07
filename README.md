# Interspeech tools

**This repository is not stable at all!!**

## How to install

This repository relies on the isca lib (which is also in development stage). Therefore it is recommended to create an environment and:
  1. install the isca-lib using the instructions from there: https://github.com/ISCAcoordinator/isca-lib/blob/main/README.md
  2. clone the current repository, go to the directory and then use pip to install

```sh
pip install -e .[dev]
```

## How to use the tools

We assume that the data from the google drive is stored into `../data/ForPublicationCommittee`

### Generate the validation book

```sh
mkdir -p output/validation_book/
is_pub -vv generate_validation_book -b --compile-tool="latexmk" ../data/ForPublicationCommittee/config.yaml output/validation_book/
```

### Generate the abstract book

```sh
mkdir -p output/abstract_book/
is_pub -vv generate_abstract_book -b --compile-tool="latexmk" ../data/ForPublicationCommittee/config.yaml output/abstract_book/
```

### Generate the app data

```sh
mkdir -p output/app_data
is_pub -vv generate_app_data ../data/ForPublicationCommittee/config.yaml output/app_data
```

### Generate the archive

```sh
mkdir -p output/archive
is_pub -vv generate_archive ../data/ForPublicationCommittee/config.yaml output/archive
```

## How to use as a library

### Extract the paper ID/presentation ID association

```python
import pathlib
import re
import pandas as pd
from interspeech_tools.io.cmt import CMTSerialiser
from isca.model.program import Presentation

# Helper used in the publication tool to extract a condensed version of the presentation ID
def short_presentation_id(input: Presentation) -> str:
    presentation_id = input.id
    presentation_id = re.sub(r"Area([0-9])-", r"Area0\1-", presentation_id)
    shorten = {"Area": "A", "Oral": "O", "Poster": "P", "ShowAndTell": "ST"}
    for s, v in shorten.items():
        presentation_id = presentation_id.replace(s, v)

    return presentation_id

# Load the conference
ser = CMTSerialiser(False, False)
input_file = pathlib.Path("../data/ForPublicationCommittee/config.yaml")
conf = ser.load(input_file)

# Extract the association information
paperid2presentationid = []
for session in conf.sessions:
    if isinstance(session, ScientificSession):
        for presentation in session.presentations:
            if presentation.presented_paper is not None:
                paperid2presentationid.append({"paper ID": int(presentation.presented_paper.id), "presentation ID": short_presentation_id(presentation)})


# Convert to a dataframe, sort by paper ID and save to an excel spreadsheet
df = pd.DataFrame(paperid2presentationid)
df = df.sort_values(by="paper ID")
df.to_excel("paper_id2presentation_id.xlsx", index=False)
```
