import time
from dataclasses import dataclass, replace
from multiprocessing import Manager, Process
from typing import Optional, Dict

from commonroad.scenario.obstacle import DynamicObstacle
from commonroad.scenario.scenario import Scenario
from scenariogeneration.xosc import Vehicle

from OpenSCENARIO2CR.ConversionAnalyzer.AnalyzerErrorResult import AnalyzerErrorResult
from OpenSCENARIO2CR.ConversionAnalyzer.AnalyzerResult import AnalyzerResult
from OpenSCENARIO2CR.util.UtilFunctions import dataclass_is_complete


@dataclass
class Analyzer:
    timeout: float = 120

    def run(self, scenario: Scenario, obstacles: Dict[str, Optional[DynamicObstacle]],
            obstacles_extra_info: Dict[str, Optional[Vehicle]]) -> Dict[str, AnalyzerResult]:
        """
        The run function is the main entry point for your analyzer. It is called by the
        scenario runner and expects to receive three arguments:

            * A Scenario object, which contains all information about the scenario that was converted.
            * A dictionary of DynamicObstacle objects, keyed by obstacle name, which represents all dynamic obstacles in
              this scenario
            * A dictionary of Vehicle objects, keyed by obstacle name, which represent additional information about the
              obstacles

        The method will run the run in a sub-process to be able to enforce the timeout. This timeout in seconds can
        be configured via the timeout attribute of the Analyzer object

        :param scenario:Scenario: Get the current scenario
        :param obstacles:Dict[str, Optional[DynamicObstacle]]: Obstacles per name
        :param obstacles_extra_info:Dict[str, Optional[Vehicle]]: Extra obstacle info per name
        :return: A dictionary of analyzer results per obstacle name
        """
        assert dataclass_is_complete(self)

        time_start = time.time()

        result_dict = Manager().dict()
        process = Process(target=self.__run, args=(scenario, obstacles, obstacles_extra_info, result_dict), daemon=True)
        process.start()
        process.join(self.timeout)
        exec_time = time.time() - time_start
        if process.exitcode is None:
            process.terminate()
            process.join(self.timeout / 2)
            exception_text = "Timed out"
            if process.exitcode is None:
                process.kill()
                exception_text = "Timed out - NEEDED SIGKILL"
            result = AnalyzerErrorResult(
                calc_time=exec_time,
                exception_text=exception_text,
                traceback_text=""
            )
            results = {o_name: result for o_name in obstacles.keys()}
        else:
            results = {o_name: replace(res, calc_time=exec_time) for o_name, res in result_dict.items()}
        return results

    def __run(self, scenario: Scenario, obstacles: Dict[str, Optional[DynamicObstacle]],
              obstacles_extra_info: Dict[str, Optional[Vehicle]], result_dict: Dict[str, AnalyzerResult]):
        result_dict.update(self._run(scenario, obstacles, obstacles_extra_info))

    def _run(self, scenario: Scenario, obstacles: Dict[str, Optional[DynamicObstacle]],
             obstacles_extra_info: Dict[str, Optional[Vehicle]]) -> Dict[str, AnalyzerResult]:
        """
        The _run function is the function where the actual work of the analyzer happens

        :param scenario:Scenario: Get the current scenario
        :param obstacles:Dict[str, Optional[DynamicObstacle]]: Obstacles per name
        :param obstacles_extra_info:Dict[str, Optional[Vehicle]]: Extra obstacle info per name
        :return: A dictionary of analyzer results per obstacle name
        """
        raise NotImplementedError
