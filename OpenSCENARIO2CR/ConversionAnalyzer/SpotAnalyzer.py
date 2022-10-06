import copy
import ctypes
from multiprocessing import Lock, Value
from typing import Dict, Optional

import spot
from commonroad.scenario.obstacle import DynamicObstacle
from commonroad.scenario.scenario import Scenario
from interface.python.commonroad_spot.spot_interface import SPOTInterface

from OpenSCENARIO2CR.ConversionAnalyzer.AnalysisResult import AnalysisResult
from OpenSCENARIO2CR.ConversionAnalyzer.Analyzer import Analyzer
from OpenSCENARIO2CR.ConversionAnalyzer.ErrorAnalysisResult import ErrorAnalysisResult


class SpotAnalyzerResult(AnalysisResult):
    def to_dict(self) -> Dict:
        raise NotImplementedError

    @staticmethod
    def from_dict(data: Dict) -> "SpotAnalyzerResult":
        raise NotImplementedError


class SpotAnalyzer(Analyzer):
    __lock: Lock = Lock()
    __num_waiting_processes = Value(ctypes.c_int, 0)

    def run(self, scenario: Scenario, obstacles: Dict[str, Optional[DynamicObstacle]]) -> Dict[str, AnalysisResult]:
        self.__num_waiting_processes += 1
        with self.__lock:
            results = {}
            try:
                for obstacle_name, obstacle in obstacles.items():
                    try:
                        scenario = copy.deepcopy(scenario)
                        scenario.remove_obstacle(obstacle)

                        interface = SPOTInterface(

                        )
                        result = spot.doOccupancyPrediction(

                        )
                    except Exception as e:
                        results[obstacle_name] = ErrorAnalysisResult.from_exception(e)
            except Exception as e:
                results = {o_name: ErrorAnalysisResult.from_exception(e) for o_name in obstacles.keys()}
            self.__num_waiting_processes -= 1
            return results
