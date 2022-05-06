from typing import List, Optional

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.scenario.scenario import Scenario as CrScenario
from scenariogeneration import xosc


class OscToCrConverter:
    osc: xosc.Scenario
    cr: Optional[CrScenario]

    def __init__(self, scenario_file_name: str):
        self.osc = xosc.ParseOpenScenario(scenario_file_name)
        self.cr = None
        self._pre_run_checks()

    def _pre_run_checks(self):
        if not isinstance(self.osc, xosc.Scenario):
            raise ValueError("Can't parse non Scenario OpenScenario files")

    def run(self):
        raise NotImplementedError

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
