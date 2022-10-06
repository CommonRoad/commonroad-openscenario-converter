from typing import Optional, Dict, List, Any

from commonroad.scenario.obstacle import DynamicObstacle
from commonroad.scenario.scenario import Scenario

from OpenSCENARIO2CR.ConversionAnalyzer.AnalysisResult import AnalysisResult


class Analyzer:
    def run(self, scenario: Scenario, obstacles: Dict[str, Optional[DynamicObstacle]], utils: List[Any]) \
            -> Dict[str, AnalysisResult]:
        """
        The run function is the main entry point for a scenario analysis plugin. It is called by the
        scenario runner and expects to receive two arguments:

            * A Scenario object, which contains all information about the scenario that was converted.
            * A dictionary of DynamicObstacle objects, keyed by obstacle ID, which represents all dynamic obstacles in
              this scenario


        :param scenario:Scenario: Pass the scenario to the run function
        :param obstacles:Dict[str: Pass the dynamic obstacles to the run function
        :param Optional[DynamicObstacle]]: Indicate whether the obstacle is dynamic or not
        :param utils:List[Any]: Pass in any additional util classes that may be needed to run the analysis
        :return: A dictionary of the form:
        """
        raise NotImplementedError
