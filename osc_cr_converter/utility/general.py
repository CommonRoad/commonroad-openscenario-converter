__author__ = "Michael Ratzel, Yuanfei Lin"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["KoSi"]
__version__ = "0.1.0"
__maintainer__ = "Yuanfei Lin"
__email__ = "commonroad@lists.lrz.de"
__status__ = "beta"

import copy
from dataclasses import fields
from typing import get_origin, Union, get_args

from commonroad.scenario.scenario import Scenario


def trim_scenario(scenario: Scenario, deep_copy: bool = True) -> Scenario:
    trimmed_scenario = copy.deepcopy(scenario) if deep_copy else scenario

    if len(trimmed_scenario.lanelet_network.lanelets) == 0:
        return trimmed_scenario
    trimmed_scenario.assign_obstacles_to_lanelets()

    if any(
        obstacle.prediction.shape_lanelet_assignment is None
        for obstacle in trimmed_scenario.dynamic_obstacles
    ):
        return trimmed_scenario

    used_lanelets = set()
    for obstacle in trimmed_scenario.dynamic_obstacles:
        for lanelet_set in obstacle.prediction.shape_lanelet_assignment.values():
            for lanelet in lanelet_set:
                used_lanelets.add(lanelet)

    removable_lanelets = []
    all_ids = {
        lanelet.lanelet_id for lanelet in trimmed_scenario.lanelet_network.lanelets
    }
    for lanelet_id in all_ids - used_lanelets:
        lanelet = trimmed_scenario.lanelet_network.find_lanelet_by_id(lanelet_id)
        if lanelet is not None:
            removable_lanelets.append(lanelet)
    trimmed_scenario.remove_lanelet(removable_lanelets)
    trimmed_scenario.assign_obstacles_to_lanelets()

    return trimmed_scenario


def dataclass_is_complete(dataclass_object) -> bool:
    for field in fields(dataclass_object):
        if get_origin(field.type) is not Union or type(None) not in get_args(
            field.type
        ):
            if (
                not hasattr(dataclass_object, field.name)
                or getattr(dataclass_object, field.name) is None
            ):
                return False
    return True
