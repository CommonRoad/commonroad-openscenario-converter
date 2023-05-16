
import os
from osc_cr_converter.utility.configuration import ConverterParams
from osc_cr_converter.converter.osc2cr import Osc2CrConverter
from osc_cr_converter.utility.visualization import visualize_scenario

scenario_path = os.path.dirname(os.path.realpath(__file__)) + '/../scenarios/from_esmini/xosc/'
openscenario = 'acc-test.xosc'
openscenario = "drop-bike-udp.xosc"
# openscenario = 'pedestrian_collision_udp.xosc'
# openscenario = 'follow_trajectory.xosc'

# scenario_path = os.path.dirname(os.path.realpath(__file__)) + '/../scenarios/from_openScenario_standard/'
# openscenario = 'DoubleLaneChanger.xosc'
# config = ConverterParams.load(os.path.dirname(os.path.realpath(__file__)) +
#                               '/../configurations/' + openscenario.replace('.xosc', '.yaml'))
config = ConverterParams()
config.debug.write_to_xml = True
converter = Osc2CrConverter(config)

scenario = converter.run_conversion(scenario_path + openscenario)
config.debug.time_steps = [0, 100, 150]

visualize_scenario(scenario, config)

