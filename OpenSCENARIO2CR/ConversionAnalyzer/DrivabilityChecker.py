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
from scenariogeneration.xosc import Vehicle

from OpenSCENARIO2CR.ConversionAnalyzer.Analyzer import Analyzer
from OpenSCENARIO2CR.ConversionAnalyzer.AnalyzerErrorResult import AnalyzerErrorResult
from OpenSCENARIO2CR.ConversionAnalyzer.AnalyzerResult import AnalyzerResult


@dataclass(frozen=True)
class DrivabilityCheckerResult(AnalyzerResult):
    collision: Optional[bool] = None
    feasibility: Optional[bool] = None

    def __getstate__(self) -> Dict:
        return self.__dict__.copy()

    def __setstate__(self, data: Dict):
        self.__dict__.update(data)


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

    def _run(self, scenario: Scenario, obstacles: Dict[str, Optional[DynamicObstacle]],
             obstacles_extra_info: Dict[str, Optional[Vehicle]]) -> Dict[str, AnalyzerResult]:
        try:
            assert len(obstacles) > 0
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
                        calc_time=None,
                        collision=collision_checker.collide(vehicle_collision_object),
                        feasibility=
                        feasibility_checker.trajectory_feasibility(traj, self.vehicle_dynamics, self.dt)[0]
                    )
                except Exception as e:
                    results[obstacle_name] = AnalyzerErrorResult.from_exception(e)
            return results
        except Exception as e:
            return {obstacle_name: AnalyzerErrorResult.from_exception(e) for obstacle_name in obstacles.keys()}
