from dataclasses import dataclass
from typing import Dict, List

from OpenSCENARIO2CR.OpenSCENARIOWrapper.ESimEndingCause import ESimEndingCause
from OpenSCENARIO2CR.OpenSCENARIOWrapper.ScenarioObjectState import SimScenarioObjectState


@dataclass(frozen=True)
class WrapperSimResult:
    """
    Dataclass to store the results of a wrapper simulation run

    Attributes
        ending_cause cause why the simulation ended
        states_per_vehicle List of simulation states per vehicle
        total_simulation_time total time simulated (Not execution time)
        error_message Option
    """
    states: Dict[str, List[SimScenarioObjectState]]
    sim_time: float
    ending_cause: ESimEndingCause

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
