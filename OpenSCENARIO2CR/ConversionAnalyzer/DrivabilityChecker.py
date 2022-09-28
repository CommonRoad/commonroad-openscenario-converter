import traceback
import warnings
from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, Optional

from commonroad.scenario.obstacle import DynamicObstacle
from commonroad.scenario.scenario import Scenario
from commonroad_dc.boundary.boundary import create_road_boundary_obstacle
from commonroad_dc.collision.collision_detection.pycrcc_collision_dispatch import create_collision_checker, \
    create_collision_object
from commonroad_dc.feasibility import feasibility_checker
from commonroad_dc.feasibility.vehicle_dynamics import VehicleDynamics, VehicleType

from OpenSCENARIO2CR.ConversionAnalyzer.AnalysisResult import AnalysisResult
from OpenSCENARIO2CR.ConversionAnalyzer.Analyzer import Analyzer
from OpenSCENARIO2CR.ConversionAnalyzer.ErrorAnalysisResult import ErrorAnalysisResult


@dataclass(frozen=True)
class DrivabilityCheckerResult(AnalysisResult):
    collision: Optional[bool] = None
    feasibility: Optional[bool] = None

    def to_dict(self) -> Dict:
        ret = {}
        if self.collision is not None:
            ret["collision"] = self.collision
        if self.feasibility is not None:
            ret["feasibility"] = self.feasibility
        return ret

    @staticmethod
    def from_dict(data: Dict) -> "DrivabilityCheckerResult":
        collision = data["collision"] if "collision" in data else None
        feasibility = data["feasibility"] if "feasibility" in data else None
        return DrivabilityCheckerResult(
            collision=collision,
            feasibility=feasibility
        )


class DrivabilityChecker(Analyzer):
    def __init__(self):
        self.vehicle_dynamics = VehicleDynamics.KS(VehicleType.BMW_320i)
        self.dt = 0.1

    @property
    def vehicle_dynamics(self) -> VehicleDynamics:
        return self._vehicle_dynamics

    @vehicle_dynamics.setter
    def vehicle_dynamics(self, new_vehicle_dynamics: VehicleDynamics):
        self._vehicle_dynamics = new_vehicle_dynamics

    @property
    def dt(self) -> float:
        return self._dt

    @dt.setter
    def dt(self, new_dt: float):
        self._dt = new_dt

    def run(self, scenario: Scenario, obstacles: Dict[str, Optional[DynamicObstacle]]) \
            -> Dict[str, DrivabilityCheckerResult]:
        try:
            if len(obstacles) > 0:
                _, road_boundary = create_road_boundary_obstacle(scenario)
                results = {}
                for obstacle_name, obstacle in obstacles.items():
                    try:
                        scenario_for_vehicle = deepcopy(scenario)
                        scenario_for_vehicle.remove_obstacle(obstacle)
                        collision_checker = create_collision_checker(scenario_for_vehicle)
                        collision_checker.add_collision_object(road_boundary)
                        traj = obstacle.prediction.trajectory
                        vehicle_collision_object = create_collision_object(obstacle)
                        results[obstacle_name] = DrivabilityCheckerResult(
                            collision=collision_checker.collide(vehicle_collision_object),
                            feasibility=
                            feasibility_checker.trajectory_feasibility(traj, self.vehicle_dynamics, self.dt)[0]
                        )
                    except Exception as e:
                        results[obstacle_name] = ErrorAnalysisResult.from_exception(e)
                return results
        except Exception as e:
            warnings.warn(f"<DrivabilityChecker/run> Failed with: {e}")
            warnings.warn(traceback.format_exc(limit=50))
            return {obstacle_name: ErrorAnalysisResult.from_exception(e) for obstacle_name in obstacles.keys()}
        return {obstacle_name: DrivabilityCheckerResult() for obstacle_name in obstacles.keys()}
