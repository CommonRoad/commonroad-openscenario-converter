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

from OpenSCENARIO2CR.utility.abs_rel import AbsRel
from OpenSCENARIO2CR.utility.general import dataclass_is_complete


@dataclass
class PPSBuilder:
    """
    Planning Problem Set builder
    """
    # Required
    time_interval: AbsRel[Interval] = AbsRel(Interval(-10, 0), AbsRel.EUsage.REL_ADD)

    pos_length: AbsRel[float] = AbsRel(50, AbsRel.EUsage.ABS)
    pos_width: AbsRel[float] = AbsRel(10, AbsRel.EUsage.ABS)
    pos_rotation: AbsRel[float] = AbsRel(0, AbsRel.EUsage.REL_ADD)
    pos_center_x: AbsRel[float] = AbsRel(0, AbsRel.EUsage.REL_ADD)
    pos_center_y: AbsRel[float] = AbsRel(0, AbsRel.EUsage.REL_ADD)

    # Optional
    velocity_interval: Optional[AbsRel[Interval]] = None
    orientation_interval: Optional[AbsRel[AngleInterval]] = None

    def build(self, obstacle: DynamicObstacle) -> PlanningProblemSet:
        assert dataclass_is_complete(self)

        initial_state = obstacle.prediction.trajectory.state_list[0]
        final_state = obstacle.prediction.trajectory.final_state

        goal_state = State()

        position_rotation = self.pos_rotation.get(final_state.orientation)
        while not is_valid_orientation(position_rotation):
            if position_rotation > 0:
                position_rotation -= 2 * np.pi
            else:
                position_rotation += 2 * np.pi
        center = np.array((
            self.pos_center_x.get(final_state.position[0]),
            self.pos_center_y.get(final_state.position[1]),
        ))
        goal_state.position = Rectangle(
            length=self.pos_length.get(obstacle.obstacle_shape.length),
            width=self.pos_width.get(obstacle.obstacle_shape.width),
            center=center,
            orientation=position_rotation
        )

        goal_state.time_step = self.time_interval.get(final_state.time_step)

        if self.velocity_interval is not None:
            goal_state.velocity = self.velocity_interval.get(final_state.velocity)
        if self.orientation_interval is not None:
            goal_state.orientation = self.orientation_interval.get(final_state.orientation)

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
