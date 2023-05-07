import unittest
import os

from commonroad.scenario.scenario import Scenario
from commonroad.scenario.lanelet import LaneletNetwork

from osc_cr_converter.converter.osc2cr import Osc2CrConverter, EFailureReason
from osc_cr_converter.utility.configuration import ConverterParams


class TestOpenSCENARIOToCommonRoadConversion(unittest.TestCase):
    """Performs some basic tests of the conversion by comparing what the converter produced with the content
    of the respective .xosc files."""

    def setUp(self) -> None:
        super().setUp()
        config = ConverterParams()
        self.converter = Osc2CrConverter(config)

    def load_and_convert_openscenario(self, file_name: str) -> Scenario:
        source_file = os.path.dirname(os.path.realpath(__file__)) + "/../scenarios/" + file_name
        return self.converter.run_conversion(source_file)

    def test_esmini_scenario(self):
        name = "from_esmini/xosc/pedestrian.xosc"
        scenario = self.load_and_convert_openscenario(name)

        # check whether the conversion is successfully done or not
        self.assertFalse(isinstance(scenario, EFailureReason))

        # test map conversion
        self.assertIsInstance(scenario.lanelet_network, LaneletNetwork)

        # test nr of obstacles
        self.assertEqual(len(scenario.dynamic_obstacles), 2)
        self.assertEqual(len(scenario.static_obstacles), 0)

    def test_standard_scenario(self):
        name = "from_openScenario_standard/DoubleLaneChanger.xosc"
        scenario = self.load_and_convert_openscenario(name)

        # check whether the conversion is successfully done or not
        self.assertFalse(isinstance(scenario, EFailureReason))

        # test map conversion
        self.assertIsInstance(scenario.lanelet_network, LaneletNetwork)

        # test nr of obstacles
        self.assertEqual(len(scenario.dynamic_obstacles), 3)
        self.assertEqual(len(scenario.static_obstacles), 0)

