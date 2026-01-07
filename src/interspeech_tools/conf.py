from typing import Any
import pprint
import pathlib
from isca.io.utils.pdf import ISCAObject
from ruamel.yaml import YAML


class Config(ISCAObject):
    def __init__(self, configuration_file: pathlib.Path | str):
        self._configuration_file = pathlib.Path(configuration_file)
        yaml = YAML(typ="rt", pure=True)
        with open(configuration_file) as f_in:
            self._conf_info = yaml.load(f_in.read())

        # Fix root directory
        if not self["input_data"]["root_dir"].startswith("/"):
            self["input_data"]["root_dir"] = self._configuration_file.parent / self["input_data"]["root_dir"]

        # NOTE: apparently autamtically converted into a date when loading the YAML configuration
        # # Convert the dates to datetime
        # config["startDate"] = datetime.strptime(config["startDate"], "%Y-%m-%d")
        # config["endDate"] = datetime.strptime(config["endDate"], "%Y-%m-%d")

    def __getitem__(self, key: str) -> Any:
        return self._conf_info[key]

    def __contains__(self, object: Any) -> bool:
        return object in self._conf_info

    def __str__(self) -> str:
        return f"Configuration loaded from {self._configuration_file}"

    def __repr__(self) -> str:
        return f"Configuration:\n{pprint.pformat(self.__dict__)}"
