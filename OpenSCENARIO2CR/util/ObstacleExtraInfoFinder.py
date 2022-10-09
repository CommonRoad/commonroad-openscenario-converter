import os
import xml.etree.ElementTree as Et
from dataclasses import dataclass
from os import path
from typing import Dict, Optional

from commonroad.scenario.obstacle import DynamicObstacle
from scenariogeneration.xosc import Vehicle, ParseOpenScenario, Scenario, CatalogReference, Catalog

from OpenSCENARIO2CR.util.UtilFunctions import dataclass_is_complete


@dataclass
class ObstacleExtraInfoFinder:
    scenario_path: str = None
    obstacles: Dict[str, Optional[DynamicObstacle]] = None

    def run(self) -> Dict[str, Optional[Vehicle]]:
        assert dataclass_is_complete(self)

        scenario: Scenario = ParseOpenScenario(self.scenario_path)

        matched_obstacles: Dict[str, Vehicle] = {o_name: None for o_name in self.obstacles.keys()}
        for scenario_object in scenario.entities.scenario_objects:
            if scenario_object.name not in matched_obstacles.keys():
                continue
            if scenario_object.name in self.obstacles.keys() and isinstance(scenario_object.entityobject, Vehicle):
                matched_obstacles[scenario_object.name] = scenario_object.entityobject

        if all([obstacle is not None for obstacle in matched_obstacles.values()]):
            return matched_obstacles

        catalogs = self._parse_catalogs(scenario)
        for scenario_object in scenario.entities.scenario_objects:
            if scenario_object.name not in matched_obstacles.keys():
                continue
            if scenario_object.name in matched_obstacles and matched_obstacles[scenario_object.name] is not None:
                continue
            if isinstance(scenario_object.entityobject, CatalogReference):
                if scenario_object.entityobject.catalogname in catalogs:
                    for entry in catalogs[scenario_object.entityobject.catalogname]:
                        if entry.tag == "Vehicle" and entry.attrib["name"] == scenario_object.entityobject.entryname:
                            matched_obstacles[scenario_object.name] = Vehicle.parse(entry)

        return matched_obstacles

    def _parse_catalogs(self, scenario: Scenario) -> Dict[str, Et.Element]:
        assert "VehicleCatalog" in Catalog._CATALOGS, "Probably the OpenSCENARIO standard changed"
        if "VehicleCatalog" in scenario.catalog.catalogs:
            # Prefer the VehicleCatalog by inserting it at first
            catalog_locations = [scenario.catalog.catalogs["VehicleCatalog"]]
            catalog_locations.extend([
                location for l_name, location in scenario.catalog.catalogs.items() if l_name != "VehicleCatalog"
            ])
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
            catalog.attrib["name"]: catalog for catalog_file in catalog_files if
            (catalog := self._parse_single_catalog(catalog_file)) is not None
        }

    @staticmethod
    def _parse_single_catalog(catalog_file) -> Optional[Et.Element]:
        root = Et.parse(catalog_file)
        return root.find("Catalog")
