import traceback
import warnings
from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
from commonroad.scenario.obstacle import DynamicObstacle
from commonroad.scenario.scenario import Scenario
from crmonitor.common.world import World
from crmonitor.evaluation.evaluation import RuleEvaluator

from OpenSCENARIO2CR.ConversionAnalyzer.AnalysisResult import AnalysisResult
from OpenSCENARIO2CR.ConversionAnalyzer.Analyzer import Analyzer
from OpenSCENARIO2CR.ConversionAnalyzer.ErrorAnalysisResult import ErrorAnalysisResult


@dataclass(frozen=True)
class STLMonitorResult(AnalysisResult):
    r_g1: Optional[np.ndarray] = None
    r_g2: Optional[np.ndarray] = None
    r_g3: Optional[np.ndarray] = None

    def to_dict(self) -> Dict:
        ret = {}
        if self.r_g1 is not None:
            ret["R_G1"] = self.ndarray_to_str(self.r_g1)
        if self.r_g2 is not None:
            ret["R_G2"] = self.ndarray_to_str(self.r_g2)
        if self.r_g3 is not None:
            ret["R_G3"] = self.ndarray_to_str(self.r_g3)
        return ret

    @staticmethod
    def from_dict(data: Dict) -> "STLMonitorResult":
        return STLMonitorResult(
            r_g1=AnalysisResult.str_to_ndarray(data["R_G1"]) if "R_G1" in data else None,
            r_g2=AnalysisResult.str_to_ndarray(data["R_G2"]) if "R_G2" in data else None,
            r_g3=AnalysisResult.str_to_ndarray(data["R_G3"]) if "R_G3" in data else None,
        )


class STLMonitor(Analyzer):
    def run(self, scenario: Scenario, obstacles: Dict[str, Optional[DynamicObstacle]]) -> Dict[str, STLMonitorResult]:
        try:
            assert len(scenario.lanelet_network.lanelets) > 0
            for obstacle in scenario.dynamic_obstacles:
                if obstacle.prediction.shape_lanelet_assignment is None:
                    scenario.assign_obstacles_to_lanelets(obstacle_ids={obstacle.obstacle_id})
                assert obstacle.prediction.shape_lanelet_assignment is not None
            if len(obstacles) > 0:
                world = World.create_from_scenario(scenario)
                results = {}
                for obstacle_name, obstacle in obstacles.items():
                    try:
                        if obstacle is None:
                            continue
                        vehicle = world.vehicle_by_id(obstacle.obstacle_id)
                        assert vehicle is not None
                        results[obstacle_name] = STLMonitorResult(
                            r_g1=RuleEvaluator.create_from_config(world, vehicle, rule="R_G1").evaluate(),
                            r_g2=RuleEvaluator.create_from_config(world, vehicle, rule="R_G2").evaluate(),
                            r_g3=RuleEvaluator.create_from_config(world, vehicle, rule="R_G3").evaluate(),
                        )
                    except Exception as e:
                        results[obstacle_name] = ErrorAnalysisResult.from_exception(e)
                return results
        except Exception as e:
            warnings.warn(f"<STLMonitor/run> Failed with: {e}")
            warnings.warn(traceback.format_exc(limit=50))
            return {obstacle_name: ErrorAnalysisResult.from_exception(e) for obstacle_name in obstacles.keys()}
        return {obstacle_name: STLMonitorResult() for obstacle_name in obstacles.keys()}
