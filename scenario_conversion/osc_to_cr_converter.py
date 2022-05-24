import os.path
from typing import List, Optional

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.scenario.scenario import Scenario as CrScenario
from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad
from scenariogeneration import xosc


class OscToCrConverter:
    osc: xosc.Scenario
    osd: CrScenario
    cr: Optional[CrScenario]

    def __init__(self, openscenario_file_name: str, opendrive_file_name):
        self.osc = xosc.ParseOpenScenario(openscenario_file_name)
        opendrive_file = os.path.join(opendrive_file_name)
        self.osd = opendrive_to_commonroad(opendrive_file)

        self.cr = None
        self._pre_run_checks()

    def _pre_run_checks(self):
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
