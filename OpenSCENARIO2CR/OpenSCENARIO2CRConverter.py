import math
import sys
from io import BytesIO
from os import path
from typing import Optional, Set
from zipfile import ZipFile

import requests
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Scenario, Tag, Location
from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad

from OpenSCENARIO2CR.EsminiWrapper.EsminiWrapper import EsminiWrapper
from OpenSCENARIO2CR.EsminiWrapper.ScenarioObjectState import ScenarioObjectState


class OpenSCENARIO2CRConverter:
    osc_file: str
    osd_file: str
    cr_dt: float
    esmini_wrapper: Optional[EsminiWrapper]

    scenario: Optional[Scenario]
    planning_problem_set: Optional[PlanningProblemSet]

    author: Optional[str]
    affiliation: Optional[str]
    source: Optional[str]
    tags: Optional[Set[Tag]]
    location: Optional[Location]
    decimal_precision: Optional[int]

    def __init__(self, openscenario_file_name: str, opendrive_file_name, delta_t: float,
                 esmini_delta_t: Optional[float] = None):
        self.osc_file = path.abspath(openscenario_file_name)
        self.osd_file = path.abspath(opendrive_file_name)
        self.cr_dt = delta_t
        self.esmini_dt = esmini_delta_t if esmini_delta_t is not None else delta_t / 10
        self.esmini_wrapper = self._load_esmini_wrapper()

        self.scenario = opendrive_to_commonroad(self.osd_file)
        self.planning_problem_set = None

        self.author = None
        self.affiliation = None
        self.source = None
        self.tags = None
        self.location = None
        self.decimal_precision = None

        self._pre_run_checks()

    @staticmethod
    def _load_esmini_wrapper(version: Optional[str] = None) -> Optional[EsminiWrapper]:

        if version is None:
            try:
                r = requests.get('https://github.com/esmini/esmini/releases/latest')
                latest_version = r.url.split("/")[-1]
                version = latest_version
            except requests.exceptions.ConnectionError:
                version = "v2.25.1"
        esmini_path = "esmini_{}".format(version)
        bin_path = path.abspath(path.join(esmini_path, "esmini", "bin"))
        if not path.exists(bin_path):
            OpenSCENARIO2CRConverter.download_esmini(version, esmini_path)
        if path.exists(bin_path):
            return EsminiWrapper(bin_path)
        return None

    @staticmethod
    def download_esmini(version: str, directory_path: str):
        archive_name = ""
        if sys.platform.startswith("linux"):
            archive_name = "EsminiWrapper-bin_ubuntu.zip"
        elif sys.platform.startswith("darwin"):
            archive_name = "EsminiWrapper-bin_mac_catalina.zip"
        elif sys.platform.startswith("win32"):
            archive_name = "EsminiWrapper-bin_win_x64.zip"
        else:
            print("Unsupported platform: {}".format(sys.platform))
            quit()
        r = requests.get("/".join(["https://github.com/esmini/esmini/releases/download", version, archive_name]))
        with ZipFile(BytesIO(r.content), "r") as zipObj:
            zipObj.extractall(directory_path)

    def _pre_run_checks(self):
        if self.esmini_wrapper is None:
            raise ValueError("Esmini Wrapper was not created successfully")

    def run(self, view: bool = False, gif_file_path: Optional[str] = None):
        states, sim_time = self.esmini_wrapper.simulate_scenario(
            scenario_path=self.osc_file,
            dt=self.esmini_dt,
            grace_time=1.0,
        )
        if states is not None:
            final_timestamps = [step * self.cr_dt for step in range(math.ceil(sim_time / self.cr_dt) + 1)]
            interpolated_states = {
                object_id: [ScenarioObjectState.build_interpolated(state_list, t) for t in final_timestamps]
                for object_id, state_list in states.items()
            }

        if view:
            self.esmini_wrapper.view_scenario(
                scenario_path=self.osc_file,
                grace_time=1.0,
            )
        if gif_file_path is not None:
            gif_path = self.esmini_wrapper.render_scenario_to_gif(
                scenario_path=self.osc_file,
                gif_file_path=gif_file_path,
                grace_time=1.0,
            )
            if gif_path is not None:
                print("Rendered {} to {}".format(path.basename(self.osc_file), gif_path))

    def save_to_file(self, target_file_path: str):
        extra_information = {}
        if self.author is not None:
            extra_information["author"] = self.author
        if self.affiliation is not None:
            extra_information["affiliation"] = self.affiliation
        if self.source is not None:
            extra_information["source"] = self.source
        if self.tags is not None:
            extra_information["tags"] = self.tags
        if self.location is not None:
            extra_information["location"] = self.location
        if self.decimal_precision is not None:
            extra_information["decimal_precision"] = self.decimal_precision

        fw = CommonRoadFileWriter(self.scenario, self.planning_problem_set, **extra_information)
        fw.write_to_file(target_file_path, OverwriteExistingFile.ALWAYS)
        raise NotImplementedError


if __name__ == '__main__':
    conv = OpenSCENARIO2CRConverter(
        "/home/michael/SoftwareProjects/CommonRoad/openscenario/scenarios/from_openScenario_standard/DoubleLaneChanger.xosc",
        "/home/michael/SoftwareProjects/CommonRoad/openscenario/scenarios/from_openScenario_standard/Databases/AB_RQ31_Straight.xodr",
        0.1,
        0.03
    )
    conv.run(gif_file_path="test.gif")
