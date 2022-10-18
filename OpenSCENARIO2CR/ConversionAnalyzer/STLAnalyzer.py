import traceback
import warnings
from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
from commonroad.scenario.obstacle import DynamicObstacle
from commonroad.scenario.scenario import Scenario
from crmonitor.common.world import World
from crmonitor.evaluation.evaluation import RuleEvaluator
from scenariogeneration.xosc import Vehicle

from OpenSCENARIO2CR.ConversionAnalyzer.Analyzer import Analyzer
from OpenSCENARIO2CR.ConversionAnalyzer.AnalyzerErrorResult import AnalyzerErrorResult
from OpenSCENARIO2CR.ConversionAnalyzer.AnalyzerResult import AnalyzerResult


@dataclass(frozen=True)
class STLAnalyzerResult(AnalyzerResult):
    r_g1: Optional[np.ndarray] = None
    r_g2: Optional[np.ndarray] = None
    r_g3: Optional[np.ndarray] = None

    def __getstate__(self) -> Dict:
        return self.__dict__.copy()

    def __setstate__(self, data: Dict):
        self.__dict__.update(data)


@dataclass
class STLAnalyzer(Analyzer):
    def _run(self, scenario: Scenario, obstacles: Dict[str, Optional[DynamicObstacle]],
             obstacles_extra_info: Dict[str, Optional[Vehicle]]) -> Dict[str, AnalyzerResult]:
        try:
            assert len(scenario.lanelet_network.lanelets) > 0
            for obstacle in scenario.dynamic_obstacles:
                if obstacle.prediction.shape_lanelet_assignment is None:
                    scenario.assign_obstacles_to_lanelets(obstacle_ids={obstacle.obstacle_id})
                assert obstacle.prediction.shape_lanelet_assignment is not None
            assert len(obstacles) > 0
            world = World.create_from_scenario(scenario)
            results = {}
            for obstacle_name, obstacle in obstacles.items():
                try:
                    if obstacle is None:
                        continue
                    vehicle = world.vehicle_by_id(obstacle.obstacle_id)
                    assert vehicle is not None, \
                        "Vehicle probably has weird trajectory and left lanelet network for at least one timestamp"
                    results[obstacle_name] = STLAnalyzerResult(
                        r_g1=RuleEvaluator.create_from_config(world, vehicle, rule="R_G1").evaluate(),
                        r_g2=RuleEvaluator.create_from_config(world, vehicle, rule="R_G2").evaluate(),
                        r_g3=RuleEvaluator.create_from_config(world, vehicle, rule="R_G3").evaluate(),
                    )
                except Exception as e:
                    results[obstacle_name] = AnalyzerErrorResult.from_exception(e)
            return results
        except Exception as e:
            warnings.warn(f"<STLMonitor/run> Failed with: {e}")
            warnings.warn(traceback.format_exc(limit=50))
            return {obstacle_name: AnalyzerErrorResult.from_exception(e) for obstacle_name in obstacles.keys()}
