from dataclasses import dataclass
from typing import Optional

import numpy as np
from commonroad.common.util import Interval, AngleInterval
from commonroad.common.validity import is_valid_orientation
from commonroad.geometry.shape import Rectangle
from commonroad.planning.goal import GoalRegion
from commonroad.planning.planning_problem import PlanningProblemSet, PlanningProblem
from commonroad.scenario.obstacle import DynamicObstacle
from commonroad.scenario.trajectory import State

from OpenSCENARIO2CR.util.AbsRel import AbsRel
from OpenSCENARIO2CR.util.UtilFunctions import dataclass_is_complete


@dataclass
class PPSBuilder:
    """
    Planning Problem Set builder
    """
    # Required
    goal_state_position_length: float = 50
    goal_state_position_width: float = 10
    goal_state_time_step: AbsRel[Interval] = AbsRel(Interval(-10, 0), False)
    goal_state_position_use_ego_rotation: bool = True

    # Optional
    goal_state_velocity: Optional[AbsRel[Interval]] = None
    goal_state_orientation: Optional[AbsRel[AngleInterval]] = None

    def build(self, obstacle: DynamicObstacle) -> PlanningProblemSet:
        assert dataclass_is_complete(self)

        initial_state = obstacle.prediction.trajectory.state_list[0]
        final_state = obstacle.prediction.trajectory.final_state
        orientation = final_state.orientation if self.goal_state_position_use_ego_rotation else 0.0
        while not is_valid_orientation(orientation):
            if orientation > 0:
                orientation -= 2 * np.pi
            else:
                orientation += 2 * np.pi

        goal_state = State()

        goal_state.position = Rectangle(
            length=self.goal_state_position_length,
            width=self.goal_state_position_width,
            center=final_state.position,
            orientation=orientation
        )

        goal_state.time_step = self.goal_state_time_step.as_summand(final_state.time_step)

        if self.goal_state_velocity is not None:
            goal_state.velocity = self.goal_state_velocity.as_summand(final_state.velocity)
        if self.goal_state_orientation is not None:
            goal_state.orientation = self.goal_state_orientation.as_summand(final_state.orientation)

        return PlanningProblemSet(
            [
                PlanningProblem(
                    planning_problem_id=obstacle.obstacle_id,
                    initial_state=initial_state,
                    goal_region=GoalRegion(
                        state_list=[goal_state]
                    )
                )
            ]
        )
