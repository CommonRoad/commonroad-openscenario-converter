import os.path
import sys

import requests
import wget
from typing import List, Optional
from zipfile import ZipFile

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.scenario.scenario import Scenario as CrScenario
from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad
from scenariogeneration import xosc
from OpenSCENARIO2CR.EsminiWrapper import EsminiWrapper


class OpenSCENARIO2CRConverter:
    osc: xosc.Scenario
    osd: CrScenario
    cr: Optional[CrScenario]
    esmini_wrapper: Optional[EsminiWrapper]

    def __init__(self, openscenario_file_name: str, opendrive_file_name):
        self.osc = xosc.ParseOpenScenario(openscenario_file_name)
        opendrive_file = os.path.join(opendrive_file_name)
        self.osd = opendrive_to_commonroad(opendrive_file)

        self.cr = None
        self.esmini_wrapper = None
        self.esmini_wrapper = self._load_esmini_wrapper()
        self._pre_run_checks()

    @staticmethod
    def _load_esmini_wrapper(version: Optional[str]=None) -> Optional[EsminiWrapper]:

        if version is None:
            r = requests.get('https://github.com/esmini/esmini/releases/latest')
            latest_version = r.url.split("/")[-1]
            version = latest_version
        esmini_path = "esmini_{}".format(version)
        bin_path = os.path.abspath(os.path.join(esmini_path, "bin"))
        if not os.path.exists(bin_path):
            OpenSCENARIO2CRConverter.download_esmini(version, esmini_path)
        if os.path.exists(bin_path):
            return EsminiWrapper(bin_path)
        return None

    @staticmethod
    def download_esmini(version: str, directory_path: str):
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
        wget.download("/".join(["https://github.com/esmini/esmini/releases/download", version, archive_name]))
        with ZipFile(archive_name, "r") as zipObj:
            zipObj.extractall()
        os.remove(archive_name)
        os.rename("esmini", directory_path)

    def _pre_run_checks(self):
        if self.esmini_wrapper is None:
            raise ValueError("Esmini Wrapper was not created successfully")
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
