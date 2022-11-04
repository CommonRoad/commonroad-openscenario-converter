from dataclasses import dataclass
from typing import Dict, List, Optional

from OpenSCENARIO2CR.OpenSCENARIOWrapper.ESimEndingCause import ESimEndingCause
from OpenSCENARIO2CR.OpenSCENARIOWrapper.ScenarioObjectState import SimScenarioObjectState
from OpenSCENARIO2CR.OpenSCENARIOWrapper.StoryBoardElement import EStoryBoardElementLevel


@dataclass(frozen=True)
class WrapperSimResult:
    """
    Dataclass to store the results of a wrapper simulation run

    Attributes
        ending_cause cause why the simulation ended
        states_per_vehicle List of simulation states per vehicle
        total_simulation_time total time simulated (Not execution time)
        running_storyboard_elements Dict[sim_time, Dict[element level, count active elements]]
    """
    states: Dict[str, List[SimScenarioObjectState]]
    sim_time: float
    ending_cause: ESimEndingCause
    running_storyboard_elements: Optional[Dict[float, Dict[EStoryBoardElementLevel, int]]] = None

    @staticmethod
    def failure() -> "WrapperSimResult":
        """
        The failure function returns a WrapperSimResult with the ending cause set to FAILURE.

        :return: A wrappersimresult object
        """
        return WrapperSimResult(
            ending_cause=ESimEndingCause.FAILURE,
            states={},
            sim_time=0.0,
        )
