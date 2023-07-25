__author__ = "Yuanfei Lin"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["KoSi"]
__version__ = "0.1.0"
__maintainer__ = "Yuanfei Lin"
__email__ = "commonroad@lists.lrz.de"
__status__ = "beta"

from enum import Enum
import numpy as np
from typing import List, Union
import matplotlib.pyplot as plt

from commonroad.visualization.mp_renderer import MPRenderer
from commonroad.scenario.scenario import Scenario, DynamicObstacle
from commonroad.scenario.state import PMState, CustomState
from commonroad.geometry.shape import ShapeGroup

from osc_cr_converter.utility.configuration import ConverterParams


class TUMcolor(tuple, Enum):
    TUMblue = (0, 101 / 255, 189 / 255)
    TUMred = (227 / 255, 27 / 255, 35 / 255)
    TUMdarkred = (139 / 255, 0, 0)
    TUMgreen = (162 / 255, 173 / 255, 0)
    TUMgray = (156 / 255, 157 / 255, 159 / 255)
    TUMdarkgray = (88 / 255, 88 / 255, 99 / 255)
    TUMorange = (227 / 255, 114 / 255, 34 / 255)
    TUMdarkblue = (0, 82 / 255, 147 / 255)
    TUMwhite = (1, 1, 1)
    TUMblack = (0, 0, 0)
    TUMlightgray = (217 / 255, 218 / 255, 219 / 255)


zorder = 22


def draw_state_list(
    rnd: MPRenderer,
    state_list: List[Union[PMState, CustomState]],
    start_time_step: Union[None, int] = None,
    color: TUMcolor = TUMcolor.TUMdarkblue,
    linewidth: float = 0.75,
) -> None:
    """
    Visualizing the state list as a connecting trajectory. The transparency is based on the starting
    time step.
    """
    global zorder
    # visualize optimal trajectory
    pos = np.asarray([state.position for state in state_list])
    if start_time_step:
        opacity = 0.5 * (start_time_step / len(state_list) + 1)
    else:
        opacity = 1
    rnd.ax.plot(
        pos[:, 0],
        pos[:, 1],
        linestyle="-",
        marker="o",
        color=color,
        markersize=5,
        zorder=zorder,
        linewidth=linewidth,
        alpha=opacity,
    )
    zorder += 1


def draw_dyn_vehicle_shape(
    rnd: MPRenderer,
    obstacle: DynamicObstacle,
    time_step: int,
    color: TUMcolor = TUMcolor.TUMblue,
):
    global zorder
    obs_shape = obstacle.occupancy_at_time(time_step).shape
    if isinstance(obs_shape, ShapeGroup):
        for shape_element in obs_shape.shapes:
            x, y = shape_element.shapely_object.exterior.xy
            rnd.ax.fill(x, y, alpha=0.5, fc=color, ec=None, zorder=zorder)
    else:
        x, y = obs_shape.shapely_object.exterior.xy
        rnd.ax.fill(x, y, alpha=0.5, fc=color, ec=None, zorder=zorder)
    zorder += 1


def visualize_scenario(scenario: Scenario, config: ConverterParams):
    rnd = MPRenderer(plot_limits=config.debug.plot_limit)
    if config.debug.time_steps is None:
        # plot the initial time step
        time_steps = [0]
    else:
        time_steps = config.debug.time_steps
    rnd.draw_params.time_begin = time_steps[0]
    rnd.draw_params.time_end = time_steps[-1]
    rnd.draw_params.trajectory.draw_trajectory = False
    rnd.draw_params.dynamic_obstacle.draw_icon = True
    scenario.draw(rnd)
    rnd.render()
    for obs in scenario.obstacles:
        if obs.prediction.final_time_step >= time_steps[-1]:
            draw_state_list(
                rnd,
                obs.prediction.trajectory.state_list[
                    time_steps[0] : time_steps[-1] + 1
                ],
                color=TUMcolor.TUMblue,
                linewidth=5,
            )
            for ts in time_steps[1:]:
                draw_dyn_vehicle_shape(rnd, obs, ts, color=TUMcolor.TUMblue)
    plt.show()
