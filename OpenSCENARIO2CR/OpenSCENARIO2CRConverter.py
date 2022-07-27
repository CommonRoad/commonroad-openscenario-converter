import os.path
import sys

import wget
from typing import List, Optional
from zipfile import ZipFile

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.scenario.scenario import Scenario as CrScenario
from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad
from scenariogeneration import xosc


class OpenSCENARIO2CRConverter:
    osc: xosc.Scenario
    osd: CrScenario
    cr: Optional[CrScenario]
    esmini_bin_path: Optional[str]

    def __init__(self, openscenario_file_name: str, opendrive_file_name):
        self.osc = xosc.ParseOpenScenario(openscenario_file_name)
        opendrive_file = os.path.join(opendrive_file_name)
        self.osd = opendrive_to_commonroad(opendrive_file)

        self.cr = None
        self.esmini_bin_path = None
        self._load_esmini()
        self._pre_run_checks()

    def _load_esmini(self):
        archive_name = ""
        if sys.platform.startswith("linux"):
            archive_name = "esmini-bin_ubuntu.zip"
        elif sys.platform.startswith("darwin"):
            archive_name = "esmini-bin_mac_catalina.zip"
        elif sys.platform.startswith("win32"):
            archive_name = "esmini-bin_win_x64.zip"
        else:
            print("Unsupported platform: {}".format(sys.platform))
            quit()

        if os.path.exists(os.path.abspath(os.path.join("esmini", "bin"))):
            self.esmini_bin_path = os.path.abspath(os.path.join("esmini", "bin"))
            return
        wget.download("https://github.com/esmini/esmini/releases/download/v2.25.1/" + archive_name)
        with ZipFile(archive_name, "r") as zipObj:
            zipObj.extractall()
        os.remove(archive_name)
        if os.path.exists(os.path.abspath(os.path.join("esmini", "bin"))):
            self.esmini_bin_path = os.path.abspath(os.path.join("esmini", "bin"))

    def _pre_run_checks(self):
        if self.esmini_bin_path is None:
            raise ValueError("Couldn't initialize esmini path to bin directory")
        if not isinstance(self.osc, xosc.Scenario):
            raise ValueError("Can't parse non Scenario OpenScenario files")

    def run(self):
        raise NotImplementedError
        self.osd = opendrive_to_commonroad("asdf")

    def merge(self, common_road_files: List[str]):
        assert self.cr is not None, "Common road file not created, did you run run() beforehand?"
        for path in common_road_files:
            cr_scenario, _ = CommonRoadFileReader(path).open()
            self._merge_single(self.cr, cr_scenario)

    @staticmethod
    def _merge_single(main_scenario: CrScenario, additional_scenario: CrScenario):
        raise NotImplementedError

    def print_statistics(self):
        raise NotImplementedError

    def save_to_file(self, target_file_path: str):
        raise NotImplementedError


if __name__ == '__main__':
    OpenSCENARIO2CRConverter(
        "/home/michael/SoftwareProjects/CommonRoad/openscenario/scenarios/from_openScenario_standard/DoubleLaneChanger.xosc",
        "/home/michael/SoftwareProjects/CommonRoad/openscenario/scenarios/from_openScenario_standard/Databases/AB_RQ31_Straight.xodr"
    )
