import copy
import ctypes
import re
import warnings
from dataclasses import dataclass, field
from multiprocessing import Value
from typing import Dict, Optional, Union, Any, ClassVar, List, Tuple, Callable

import numpy as np
import spot
from commonroad.common.util import Interval
from commonroad.geometry.shape import ShapeGroup, Polygon
from commonroad.planning.goal import GoalRegion
from commonroad.planning.planning_problem import PlanningProblem
from commonroad.prediction.prediction import Occupancy, SetBasedPrediction
from commonroad.scenario.obstacle import DynamicObstacle
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.trajectory import State
from scenariogeneration.xosc import Vehicle

from OpenSCENARIO2CR.ConversionAnalyzer.Analyzer import Analyzer
from OpenSCENARIO2CR.ConversionAnalyzer.AnalyzerErrorResult import AnalyzerErrorResult
from OpenSCENARIO2CR.ConversionAnalyzer.AnalyzerResult import AnalyzerResult
from OpenSCENARIO2CR.util.AbsRel import AbsRel
from OpenSCENARIO2CR.util.UtilFunctions import dataclass_is_complete


@dataclass(frozen=True)
class SpotAnalyzerResult(AnalyzerResult):
    predictions: Dict[int, SetBasedPrediction] = field(default_factory=dict)

    def __getstate__(self) -> Dict:
        return self.__dict__.copy()

    def __setstate__(self, data: Dict):
        self.__dict__.update(data)


@dataclass
class SpotAnalyzer(Analyzer):
    __scenario_id: ClassVar[Value] = Value(ctypes.c_int, 0)

    start_time: float = 0.0
    num_time_steps: int = 10

    compute_occ_m1: bool = True
    compute_occ_m2: bool = True
    compute_occ_m3: bool = True

    a_comfort_max_factor: Optional[AbsRel[float]] = None
    a_comfort_min_factor: Optional[AbsRel[float]] = None
    constr_no_backward: Optional[bool] = None
    constr_no_lane_change: Optional[bool] = None
    speeding_factor: Optional[float] = None
    only_in_lane: Optional[bool] = None

    def _run(self, scenario: Scenario, obstacles: Dict[str, Optional[DynamicObstacle]],
             obstacles_extra_info: Dict[str, Optional[Vehicle]]) -> Dict[str, AnalyzerResult]:

        assert dataclass_is_complete(self)

        results: Dict[str, AnalyzerResult] = {}
        start_time_step = round(self.start_time / scenario.dt)
        start_time = start_time_step * scenario.dt

        try:
            spot_results = self._run_spot_simulation(scenario, start_time, obstacles, obstacles_extra_info)
            for o_name, o_results in spot_results.items():
                if isinstance(o_results, AnalyzerErrorResult):
                    results[o_name] = o_results
                else:
                    results[o_name] = self._convert_spot_result_to_analyzer_result(o_results, start_time_step)
            return results
        except Exception as e:
            return {o_name: AnalyzerErrorResult.from_exception(e) for o_name in obstacles.keys()}

    @classmethod
    def get_next_scenario_id(cls) -> int:
        with cls.__scenario_id.get_lock():
            spot_scenario_id = cls.__scenario_id.value
            cls.__scenario_id.value += 1
        return spot_scenario_id

    def _run_spot_simulation(
            self,
            scenario: Scenario,
            start_time: float,
            obstacles: Dict[str, Optional[DynamicObstacle]],
            obstacles_extra_info: Dict[str, Optional[Vehicle]]
    ) -> Dict[str, Union[AnalyzerErrorResult, Any]]:
        spot_results = {}
        for obstacle_name, obstacle in obstacles.items():
            try:
                scenario_id = self.get_next_scenario_id()
                o_scenario = copy.deepcopy(scenario)
                o_scenario.remove_obstacle(obstacle)
                pp = PlanningProblem(
                    planning_problem_id=obstacle.obstacle_id,
                    initial_state=obstacle.initial_state,
                    goal_region=GoalRegion(state_list=[
                        State(time_step=Interval(start=0, end=obstacle.prediction.final_time_step))
                    ])
                )
                res = spot.registerScenario(
                    scenario_id,
                    o_scenario.lanelet_network,
                    o_scenario.dynamic_obstacles,
                    [pp]
                )
                assert res == 0, f"<SpotAnalyzer/run> registerScenario failed with {res}"
                spot.updateProperties(scenario_id, self._get_update_properties(
                    obstacle_name, obstacles, obstacles_extra_info
                ))
                spot_results[obstacle_name] = (
                    spot.doOccupancyPrediction(
                        scenario_id,
                        float(start_time),
                        float(o_scenario.dt),
                        float(start_time + o_scenario.dt * self.num_time_steps),
                        int(1)
                    )
                )
                spot.removeScenario(scenario_id)
            except TimeoutError as e:
                raise e
            except Exception as e:
                spot_results[obstacle_name] = AnalyzerErrorResult.from_exception(e)
        return spot_results

    def _get_update_properties(self, ego_name: str, obstacles, obstacles_extra_info) \
            -> Dict[str, Dict[int, Dict[str, Union[bool, float]]]]:
        update_properties: Dict[str, Dict[int, Dict[str, Union[bool, float]]]] = {}
        obstacle_properties: Dict[int, Dict[str, Union[bool, float]]] = {}

        def float_no_fail(target: Dict, target_field_name: str, source: Callable):
            try:
                target[target_field_name] = source()
            except Exception as e:
                warnings.warn(str(e))

        def _float(value) -> float:
            # TODO This is definitely not the full parameter evaluation capabilities OpenSCENARIO expects, but a nice
            #  hack for a common km/h -> m/s conversion
            #  Either make heavier use of the esmini evaluation ones, but that's in C++ and not populated via the
            #  standard API.
            #  Or the Second approach, and probably also the better one for the whole community: implement those
            #  capabilities in the scenariogeneration package
            if isinstance(value, str) and re.match(r"\$\{\d+\.?\d*/3.6}", value):
                return float(value.strip()[2:-5]) / 3.6
            else:
                return float(value)

        for o_name, o in obstacles.items():
            if o_name == ego_name or o is None or obstacles_extra_info[o_name] is None:
                continue
            obstacle_properties[o.obstacle_id] = {
                "v_max": abs(_float(obstacles_extra_info[o_name].dynamics.max_speed)),
                "a_max": abs(_float(obstacles_extra_info[o_name].dynamics.max_acceleration)),
            }
        if len(obstacle_properties) > 0:
            update_properties["Vehicle"] = obstacle_properties

        ego_properties: Dict[str, Union[bool, _float]] = {}
        if obstacles[ego_name] is not None:
            o: DynamicObstacle = obstacles[ego_name]
            ego_properties.update({
                "length": _float(o.obstacle_shape.length),
                "width": _float(o.obstacle_shape.width),
            })
        if obstacles_extra_info[ego_name] is not None:
            extra: Vehicle = obstacles_extra_info[ego_name]
            ego_properties.update({
                "compute_occ_m1": self.compute_occ_m1,
                "compute_occ_m2": self.compute_occ_m2,
                "compute_occ_m3": self.compute_occ_m3,
            })
            float_no_fail(ego_properties, "wheelbase",
                          lambda: abs(_float(extra.axles.frontaxle.xpos - extra.axles.rearaxle.xpos)))
            float_no_fail(ego_properties, "maxSteeringAngle", lambda: max(
                abs(_float(extra.axles.frontaxle.maxsteer)),
                abs(_float(extra.axles.rearaxle.maxsteer))
            ))
            float_no_fail(ego_properties, "a_max", lambda: abs(_float(extra.dynamics.max_acceleration)))
            float_no_fail(ego_properties, "a_min_long", lambda: -abs(_float(extra.dynamics.max_acceleration)))
            float_no_fail(ego_properties, "a_max_long", lambda: abs(_float(extra.dynamics.max_acceleration)))
            float_no_fail(ego_properties, "v_max", lambda: abs(_float(extra.dynamics.max_speed)))
            if self.a_comfort_max_factor is not None:
                float_no_fail(ego_properties, "a_comfort_max",
                              lambda: abs(self.a_comfort_max_factor.as_factor(_float(extra.dynamics.max_acceleration))))
            if self.a_comfort_min_factor is not None:
                float_no_fail(ego_properties, "a_comfort_min",
                              lambda: -abs(
                                  self.a_comfort_min_factor.as_factor(_float(extra.dynamics.max_acceleration))))
            if self.constr_no_backward is not None:
                ego_properties["constr_no_backward"] = self.constr_no_backward
            if self.constr_no_lane_change is not None:
                ego_properties["constr_no_lane_change"] = self.constr_no_lane_change
            if self.speeding_factor is not None:
                ego_properties["speeding_factor"] = self.speeding_factor
            if self.only_in_lane is not None:
                ego_properties["onlyInLane"] = self.only_in_lane

        if len(ego_properties) > 0:
            update_properties["EgoVehicle"] = {0: ego_properties}
        return update_properties

    def _convert_spot_result_to_analyzer_result(self, spot_result: list, start_time_step: int) -> AnalyzerResult:
        """
        Convert the spot return into actual usable obstacle objects

        Expected format of the spot return:
        - Obstacle 1 : list
            - ObstacleID : int
            - OccupanciesAllTime : list
                - OccupanciesTime 1 : list
                    - VelocitiesAllLanes : list
                        - Lane 1 : list
                            - LaneID : int (0 for no LaneID, in the future this might be actual usable LaneletIDs)
                            - MinVel : float
                            - MaxVel : float
                        - Lane 2
                        - ...
                    - ObstacleVertices : list
                        - Vertex 1 : list
                            - x : float
                            - y : float
                        - Vertex 2
                        - ...
                - OccupanciesTime 2
                - ...
        - Obstacle 2
        - ...
        """
        predictions: Dict[int, SetBasedPrediction] = {}
        for cpp_obstacle in spot_result:
            assert len(cpp_obstacle) == 2, "SPOT result shaped unexpectedly"
            o_id = cpp_obstacle[0]
            assert type(o_id) == int, "SPOT result shaped unexpectedly"
            occupancy_all_time_steps = cpp_obstacle[1]

            # initialise
            occupancy_list: List[Occupancy] = []
            assert len(occupancy_all_time_steps) == self.num_time_steps, \
                f"SPOT result shaped unexpectedly {len(occupancy_all_time_steps)} != {self.num_time_steps}"
            for t in range(self.num_time_steps):
                occ = Occupancy(t + 1, ShapeGroup([]))
                occupancy_list.append(occ)

            for t, occupancy_at_time_step in enumerate(occupancy_all_time_steps):
                assert len(occupancy_at_time_step) == 2, "SPOT result shaped unexpectedly"
                # velocities_all_lanes: list = occupancy_at_time_step[0] is unused
                obstacle_vertices = occupancy_at_time_step[1]

                shape_vertices: List[Tuple[float, float]] = []
                for vertex in obstacle_vertices:
                    assert len(vertex) == 2, "SPOT result shaped unexpectedly"
                    assert isinstance(vertex[0], float), "SPOT result shaped unexpectedly"
                    assert isinstance(vertex[1], float), "SPOT result shaped unexpectedly"
                    shape_vertices.append(tuple(vertex))
                    if len(shape_vertices) <= 1:
                        # First vertex added -> no checks if polygon is closed
                        continue
                    elif shape_vertices[0][0] == vertex[0] and shape_vertices[0][1] == vertex[1]:
                        # Polygon is closed
                        if len(shape_vertices) <= 2:
                            shape_vertices = shape_vertices[1:]
                            warnings.warn('Warning: one duplicated vertex skipped when copying predicted occupancies'
                                          ' to CommonRoad')
                        else:
                            shape_obj = Polygon(np.array(shape_vertices))
                            shape_group = occupancy_list[t].shape
                            assert isinstance(shape_group, ShapeGroup)
                            shape_group.shapes.append(shape_obj)
                            shape_vertices.clear()
                if len(shape_vertices) != 0:
                    raise ValueError(f"Obstacle {o_id}: Last polygon not closed (at time_step={t})")

            predictions[o_id] = SetBasedPrediction(start_time_step, occupancy_list[0:])
        return SpotAnalyzerResult(
            calc_time=None,
            predictions=predictions,
        )
