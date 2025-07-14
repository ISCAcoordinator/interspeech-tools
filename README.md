# Interspeech tools

**This repository is not stable at all!!**

## How to install

This repository relies on the isca lib (which is also in development stage). Therefore it is recommended to create an environment and:
  1. install the isca-lib using the instructions from there: https://github.com/ISCAcoordinator/isca-lib/blob/main/README.md
  2. clone the current repository, go to the directory and then use pip to install

```sh
pip install -e .[dev]
```

## How to use

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
