import os
from osc_cr_converter.utility.configuration import ConverterParams
from osc_cr_converter.converter.osc2cr import Osc2CrConverter
from osc_cr_converter.utility.visualization import visualize_scenario
import osc_cr_converter.utility.logger as util_logger

scenario_path = (
    os.path.dirname(os.path.realpath(__file__)) + "/../scenarios/from_esmini/xosc/"
)
openscenario = "pedestrian_collision.xosc"
config = ConverterParams.load(
    os.path.dirname(os.path.realpath(__file__))
    + "/../configurations/"
    + openscenario.replace(".xosc", ".yaml")
)
util_logger.initialize_logger(config)

converter = Osc2CrConverter(config)
scenario = converter.run_conversion(scenario_path + openscenario)
visualize_scenario(scenario, config)
