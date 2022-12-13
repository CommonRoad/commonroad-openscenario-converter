import re

import os

import matplotlib.pyplot as plt
from commonroad.common.util import Interval
from commonroad.scenario.scenario import Tag
from commonroad.visualization.mp_renderer import MPRenderer


from OpenSCENARIO2CR.OpenSCENARIOWrapper.Esmini.EsminiWrapperProvider import EsminiWrapperProvider
from OpenSCENARIO2CR.OpenSCENARIOWrapper.Esmini.StoryBoardElement import EStoryBoardElementLevel
from OpenSCENARIO2CR.Osc2CrConverter import Osc2CrConverter
from OpenSCENARIO2CR.util.AbsRel import AbsRel
from OpenSCENARIO2CR.util.PPSBuilder import PPSBuilder

# two examples, you can also download the scenarios from esmini or the openscenario website
scenario_path = os.getcwd() + "/scenarios/from_esmini/xosc/pedestrian.xosc"
# scenario_path =  os.getcwd() + "/scenarios/from_openScenario_standard/DoubleLaneChanger.xosc"

run_viewer = False
plots_step = 5
plot_limit = 20  # If non-null the renderer follows the ego vehicle
following_obstacle_index = 0


# Setup EsminiWrapper
esmini_wrapper = EsminiWrapperProvider().provide_esmini_wrapper()
esmini_wrapper.min_time = 15
esmini_wrapper.max_time = 30.0
esmini_wrapper.grace_time = 1.0
esmini_wrapper.ignored_level = EStoryBoardElementLevel.ACT
esmini_wrapper.log_to_console = True
esmini_wrapper.log_to_file = False
esmini_wrapper.random_seed = 0

if run_viewer:
    wrapper = EsminiWrapperProvider().provide_esmini_wrapper()
    wrapper.grace_time = None
    wrapper.max_time = 60.0
    wrapper.ignored_level = EStoryBoardElementLevel.ACT
    wrapper.view_scenario(scenario_path)

pps_builder = PPSBuilder()
pps_builder.time_interval = AbsRel(Interval(-10, 0), AbsRel.EUsage.REL_ADD)
pps_builder.pos_length = AbsRel(50, AbsRel.EUsage.ABS)
pps_builder.pos_width = AbsRel(10, AbsRel.EUsage.ABS)
pps_builder.pos_rotation = AbsRel(0, AbsRel.EUsage.REL_ADD)
pps_builder.pos_center_x = AbsRel(0, AbsRel.EUsage.REL_ADD)
pps_builder.pos_center_y = AbsRel(0, AbsRel.EUsage.REL_ADD)
pps_builder.velocity_interval = AbsRel(Interval(-5, 5), AbsRel.EUsage.REL_ADD)
pps_builder.orientation_interval = None

converter = Osc2CrConverter(
    author="ADD AUTHOR HERE",
    affiliation="ADD AFFILIATION HERE",
    source="ADD SOURCE HERE",
    tags={Tag.SIMULATED},
)

converter.sim_wrapper = esmini_wrapper
converter.pps_builder = pps_builder

converter.dt_cr = 0.1
converter.keep_ego_vehicle = True
converter.trim_scenario = False
converter.use_implicit_odr_file = True
converter.analyzers = {
}
# If you only want to run with default parameters for analyzers you can also use:
# converter.analyzers = [EAnalyzer.SPOT_ANALYZER, EAnalyzer.DRIVABILITY_CHECKER, EAnalyzer.STL_MONITOR]

converter.dt_sim = 0.01
converter.odr_file_override = None
converter.ego_filter = re.compile(r".*ego.*", re.IGNORECASE)

result = converter.run_conversion(scenario_path)

count = 0

scenario = result.scenario
pps = result.planning_problem_set
analysis = result.analysis
stats = result.statistics

lim_y = 30
lim_x = lim_y * 3
size = 10

rnd = MPRenderer(figsize=(size, size), plot_limits=[-15, 495, -60, 110])
scenario.draw(rnd, draw_params={
    "trajectory": {
        "draw_continuous": True,
        "line_width": 1,
        "unique_colors": True,
    }
})
pps.draw(rnd)
rnd.render()
plt.savefig("overview.png")
#plt.show()

times = [70, 85, 110]

for t in times:
    rnd = MPRenderer(
        figsize=(size, size),
        draw_params={"focus_obstacle_id": scenario.dynamic_obstacles[0].obstacle_id},
        plot_limits=[-lim_x, lim_x, -lim_y, lim_y],
    )
    scenario.draw(rnd, draw_params={
        "trajectory": {
            "draw_continuous": True,
            "line_width": 1,
            "unique_colors": True,
        },
        "time_begin": t
    })
    pps.draw(rnd)
    rnd.render()
    plt.savefig(f"step-{t:2d}.png")
    #plt.show()

