import os
import configparser
from typing import Union
from ast import literal_eval


class Configure:
    def __init__(self):
        self.script_dir = os.path.dirname(__file__)
        self.file = os.path.join(self.script_dir, "config.conf")
        self.conf = configparser.RawConfigParser()

    def get_config_value(self, section: str, name: Union[str, list]):
        self.conf.read(self.file)
        if type(name) != str:
            return "".join(self.conf.get(section, opt) for opt in name)  # section/"var1"+"var2"
        return self.conf.get(section, name)  # section/name

    def set_config_value(self, section: str, name: Union[str, list], value: Union[str, list]):
        assert type(name) == type(value)  # нельзя принимать список имен с одним значением, и наоборот

        self.conf.read(self.file)
        if type(name) == list:
            for n, v in zip(name, value):
                self.conf.set(section, n, v)
        else:
            self.conf.set(section, name, value)  # section/name/value
        with open(self.file, "w") as config:
            self.conf.write(config)

    def update_config_data(self):
        DEFAULT_SETTINGS = {"start_setting": {"default": False},
                           "file": {"path": os.getcwd(), "name": "/vacancies.csv"},
                           "options": {"pages": 5, "drop_duplicate": True,
                                       "write_to_file": True, "get_report": True,
                                       "experimental_parsers": False}}
        self.conf.read(self.file)
        if literal_eval(self.get_config_value("start_setting", "default")) is True:
            for section in DEFAULT_SETTINGS:
                self.set_config_value(section,
                                 list(DEFAULT_SETTINGS[section].keys()),
                                 list(DEFAULT_SETTINGS[section].values()))
