__author__ = "Michael Ratzel, Yuanfei Lin"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["KoSi"]
__version__ = "0.0.1"
__maintainer__ = "Yuanfei Lin"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Pre-alpha"

import os
import warnings
import xml.etree.ElementTree as Et
from dataclasses import dataclass
from os import path
from typing import Dict, Optional, Set, Union

from scenariogeneration.xosc import (
    Vehicle,
    ParseOpenScenario,
    Scenario,
    CatalogReference,
    Catalog,
)

from osc_cr_converter.analyzer.error import AnalyzerErrorResult
from osc_cr_converter.utility.general import dataclass_is_complete


@dataclass
class ObstacleExtraInfoFinder:
    scenario_path: str = None
    obstacle_names: Set[str] = None

    def run(self) -> Union[AnalyzerErrorResult, Dict[str, Optional[Vehicle]]]:
        assert dataclass_is_complete(self)
        try:
            scenario: Scenario = ParseOpenScenario(self.scenario_path)

            matched_obstacles: Dict[str, Vehicle] = {
                o_name: None for o_name in self.obstacle_names
            }
            for scenario_object in scenario.entities.scenario_objects:
                if scenario_object.name not in matched_obstacles.keys():
                    continue
                if scenario_object.name in self.obstacle_names and isinstance(
                    scenario_object.entityobject, Vehicle
                ):
                    matched_obstacles[
                        scenario_object.name
                    ] = scenario_object.entityobject

            if all([obstacle is not None for obstacle in matched_obstacles.values()]):
                return matched_obstacles

            catalogs = self._parse_catalogs(scenario)
            for scenario_object in scenario.entities.scenario_objects:
                if scenario_object.name not in matched_obstacles.keys():
                    continue
                if (
                    scenario_object.name in matched_obstacles
                    and matched_obstacles[scenario_object.name] is not None
                ):
                    continue
                if isinstance(scenario_object.entityobject, CatalogReference):
                    if scenario_object.entityobject.catalogname in catalogs:
                        for obj in catalogs[scenario_object.entityobject.catalogname]:
                            if (
                                obj.tag == "Vehicle"
                                and obj.attrib["name"]
                                == scenario_object.entityobject.entryname
                            ):
                                matched_obstacles[scenario_object.name] = Vehicle.parse(
                                    obj
                                )

            return matched_obstacles
        except Exception as e:
            warnings.warn(
                f"<ObstacleExtraInfoFinder/run> {path.basename(self.scenario_path)} failed with {str(e)}"
            )
            return AnalyzerErrorResult.from_exception(e)

    def _parse_catalogs(self, scenario: Scenario) -> Dict[str, Et.Element]:
        assert (
            "VehicleCatalog" in Catalog._CATALOGS
        ), "Probably the OpenSCENARIO standard changed"
        if "VehicleCatalog" in scenario.catalog.catalogs:
            # Prefer the VehicleCatalog by inserting it at first
            catalog_locations = [scenario.catalog.catalogs["VehicleCatalog"]]
            catalog_locations.extend(
                [
                    location
                    for l_name, location in scenario.catalog.catalogs.items()
                    if l_name != "VehicleCatalog"
                ]
            )
        else:
            catalog_locations = scenario.catalog.catalogs.values()

        catalog_files = []
        for catalog_path in catalog_locations:
            catalog_path = path.join(path.dirname(self.scenario_path), catalog_path)
            for file in os.listdir(catalog_path):
                file = path.join(catalog_path, file)
                if path.isfile(file):
                    catalog_files.append(file)

        return {
            catalog.attrib["name"]: catalog
            for catalog_file in catalog_files
            if (catalog := self._parse_single_catalog(catalog_file)) is not None
        }

    @staticmethod
    def _parse_single_catalog(catalog_file) -> Optional[Et.Element]:
        root = Et.parse(catalog_file)
        return root.find("Catalog")
