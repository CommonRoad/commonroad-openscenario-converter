
import os
from osc_cr_converter.utility.configuration import ConverterParams
from osc_cr_converter.converter.osc2cr import Osc2CrConverter

scenario_path = os.path.dirname(os.path.realpath(__file__)) + '/scenarios/from_esmini/xosc/pedestrian.xosc'
config = ConverterParams()
converter = Osc2CrConverter(config)
scenario = converter.run_conversion(scenario_path)
