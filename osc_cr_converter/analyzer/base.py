__author__ = "Michael Ratzel, Yuanfei Lin"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["KoSi"]
__version__ = "0.1.0"
__maintainer__ = "Yuanfei Lin"
__email__ = "commonroad@lists.lrz.de"
__status__ = "beta"

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from multiprocessing import Manager, Process
from typing import Optional, Dict, Tuple

from commonroad.scenario.obstacle import DynamicObstacle
from commonroad.scenario.scenario import Scenario

from scenariogeneration.xosc import Vehicle

from osc_cr_converter.analyzer.error import AnalyzerErrorResult
from osc_cr_converter.analyzer.result import AnalyzerResult
from osc_cr_converter.utility.general import dataclass_is_complete


@dataclass
class Analyzer(ABC):
    """
    The base interface for all post conversion analyzer.

    To implement your own analyzer, implement the _run method and make sure it is safe that the analyzer will be killed
    after the timeout happened
    """

    timeout: float = 120

    def run(
        self,
        scenario: Scenario,
        obstacles: Dict[str, Optional[DynamicObstacle]],
        obstacles_extra_info: Dict[str, Optional[Vehicle]],
    ) -> Tuple[float, Dict[str, AnalyzerResult]]:
        """
        The run method is the main entry point for your analyzer. It is called by the
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
        :return: A tuple containing the dictionary of analyzer results per obstacle name and the calculation time
        """
        assert dataclass_is_complete(self)

        time_start = time.time()

        result_dict = Manager().dict()
        process = Process(
            target=self.__run,
            args=(scenario, obstacles, obstacles_extra_info, result_dict),
            daemon=True,
        )
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
                exception_text=exception_text, traceback_text=""
            )
            results = {o_name: result for o_name in obstacles.keys()}
        else:
            results = dict(result_dict)
        return exec_time, results

    def __run(
        self,
        scenario: Scenario,
        obstacles: Dict[str, Optional[DynamicObstacle]],
        obstacles_extra_info: Dict[str, Optional[Vehicle]],
        result_dict: Dict[str, AnalyzerResult],
    ):
        result_dict.update(self._run(scenario, obstacles, obstacles_extra_info))

    @abstractmethod
    def _run(
        self,
        scenario: Scenario,
        obstacles: Dict[str, Optional[DynamicObstacle]],
        obstacles_extra_info: Dict[str, Optional[Vehicle]],
    ) -> Dict[str, AnalyzerResult]:
        """
        The _run method is the method where the actual work of the analyzer happens

        :param scenario:Scenario: Get the current scenario
        :param obstacles:Dict[str, Optional[DynamicObstacle]]: Obstacles per name
        :param obstacles_extra_info:Dict[str, Optional[Vehicle]]: Extra obstacle info per name
        :return: A dictionary of analyzer results per obstacle name
        """
        raise NotImplementedError
