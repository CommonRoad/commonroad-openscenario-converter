
from osc_cr_converter.utility.configuration import ConverterParams

# two examples, you can also download the scenarios from esmini or the openscenario website
# scenario_path = os.getcwd() + "/scenarios/from_esmini/xosc/pedestrian.xosc"
# scenario_path =  os.getcwd() + "/scenarios/from_openScenario_standard/DoubleLaneChanger.xosc"
# scenario_path = "/home/yuanfei/commonroad2/esmini-demo_ubuntu/esmini-demo/resources/xosc/alks_r157_cut_in_quick_brake.xosc"
# scenario_path = "/home/yuanfei/commonroad/esmini-demo_ubuntu/esmini-demo/resources/xosc/example/CutIn.xosc"
scenario_path = "/home/yuanfei/commonroad/esmini-demo_ubuntu/esmini-demo/resources/xosc/acc-test.xosc"
#scenario_path = "/home/yuanfei/Documents/standard_download61fa668a0fbb1_18112/openscenario-v1.1.1/standard/Examples/CutIn.xosc"
scenario_path = '/home/yuanfei/commonroad/esmini-demo_ubuntu/esmini-demo/resources/xosc/pedestrian_collision.xosc'
scenario_path = '/home/yuanfei/commonroad2/openscenario_files/saneon/xosc/padestrian_01.xosc'
#scenario_path = "/home/yuanfei/Downloads/padestrian_01.xosc"
# scenario_path = ''
sc_id = 'looming-HighWayTest.xosc'

run_viewer = True

config = ConverterParams()
from osc_cr_converter.converter.osc2cr import Osc2CrConverter

converter = Osc2CrConverter(config)

result = converter.run_conversion(scenario_path)

count = 0
#
# scenario = result.scenario
# pps = result.planning_problem_set
# stats = result.statistics
#
# lim_y = 30
# lim_x = lim_y * 3
# size = 10
#
# rnd = MPRenderer(figsize=(size, size), plot_limits=[-15, 495, -60, 110])
# scenario.draw(rnd, draw_params={
#     "trajectory": {
#         "draw_continuous": True,
#         "line_width": 1,
#         "unique_colors": True,
#     }
# })
# pps.draw(rnd)
# rnd.render()
# plt.savefig("overview.png")
# plt.show()
#

#
# times = [70, 85, 110]
#
# for t in times:
#     rnd = MPRenderer(
#         figsize=(size, size),
#         draw_params={"focus_obstacle_id": scenario.dynamic_obstacles[0].obstacle_id},
#         plot_limits=[-lim_x, lim_x, -lim_y, lim_y],
#     )
#     scenario.draw(rnd, draw_params={
#         "trajectory": {
#             "draw_continuous": True,
#             "line_width": 1,
#             "unique_colors": True,
#         },
#         "time_begin": t
#     })
#     pps.draw(rnd)
#     rnd.render()
#     plt.savefig(f"step-{t:2d}.png")
#     #plt.show()



# # import necessary classes from different modules
# from commonroad.common.file_writer import CommonRoadFileWriter
# from commonroad.common.file_writer import OverwriteExistingFile
# from commonroad.scenario.scenario import Location
# from commonroad.scenario.scenario import Tag
#
# author = 'Yuanfei Lin'
# affiliation = 'Technical University of Munich, Germany'
# source = 'pedestrian_collision.xosc'
# tags = {Tag.CRITICAL, Tag.INTERSTATE}
#
# # write new scenario
# fw = CommonRoadFileWriter(scenario, pps, author, affiliation, source, tags)
#
#
# filename = "OSC_PedestrianCollision-1_1_T-1.xml"
# fw.write_to_file(filename, OverwriteExistingFile.ALWAYS)
#
