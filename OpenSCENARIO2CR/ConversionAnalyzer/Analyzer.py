from typing import Optional, Dict

from commonroad.scenario.obstacle import DynamicObstacle
from commonroad.scenario.scenario import Scenario

from OpenSCENARIO2CR.ConversionAnalyzer.AnalysisResult import AnalysisResult


class Analyzer:
    def run(self, scenario: Scenario, obstacles: Dict[str, Optional[DynamicObstacle]]) -> Dict[str, AnalysisResult]:
        raise NotImplementedError
