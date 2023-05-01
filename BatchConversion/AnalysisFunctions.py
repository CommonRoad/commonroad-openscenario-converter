from dataclasses import fields
from enum import Enum
from typing import Union, Dict, List, Optional, Type

import numpy as np
from commonroad.visualization.mp_renderer import MPRenderer
from matplotlib import pyplot as plt

from BatchConversion.BatchConverter import BatchConversionResult
from BatchConversion.Serializable import Serializable
from OpenSCENARIO2CR.analyzer.base import Analyzer
from OpenSCENARIO2CR.analyzer.error import AnalyzerErrorResult
from OpenSCENARIO2CR.analyzer.DrivabilityAnalyzer import DrivabilityAnalyzerResult, DrivabilityAnalyzer
from OpenSCENARIO2CR.analyzer.STLAnalyzer import STLAnalyzerResult, STLAnalyzer
from OpenSCENARIO2CR.analyzer.SpotAnalyzer import SpotAnalyzerResult, SpotAnalyzer
from OpenSCENARIO2CR.wrapper.ending_cause import ESimEndingCause
from OpenSCENARIO2CR.Osc2CrConverter import EFailureReason
from OpenSCENARIO2CR.Osc2CrConverterResult import Osc2CrConverterResult

dark_blue = "#005293"
middle_blue = "#64A0C8"
blue = "#0065BD"
orange = "#E37222"
green = "#A2AD00"
ivory = "#DAD7CB"
gray = "#999999"


def _get_colors(input_data):
    """
    Returning a color palette with the same length as the input_data
    """
    if isinstance(input_data[0], list):
        if len(input_data) == 1:
            return blue
        elif len(input_data) == 2:
            return [blue, orange]
        elif len(input_data) == 3:
            return [blue, orange, green]
        elif len(input_data) == 4:
            return [dark_blue, orange, middle_blue, green]
        elif len(input_data) == 5:
            return [dark_blue, orange, middle_blue, green, gray]
    else:
        return blue


class EGranularity(Enum):
    SCENARIO = 1
    VEHICLE = 2


def analyze_results(results: Dict[str, BatchConversionResult]):
    """
    Analyze a dictionary of BatchConversionResults. This will print many general statistics how many scenarios were
    converted successfully, and about the run Analyzers
    """
    counts = {}

    def count(name: str, amount: int = 1):
        if name in counts:
            counts[name] += amount
        else:
            counts[name] = amount

    def perc(
            description: str,
            part_str: Union[str, List[str]],
            total_str: Union[str, List[str]],
            invert: bool = False
    ):
        if isinstance(part_str, str):
            part = counts.get(part_str, 0)
        else:
            part = sum([counts.get(single_part, 0) for single_part in part_str])
        if isinstance(total_str, str):
            total = counts.get(total_str, 0)
        else:
            total = sum([counts.get(single_total, 0) for single_total in total_str])
        if invert:
            part = total - part
        if total != 0:
            res = f"{100 * part / total:5.1f} %"
        else:
            res = "  NaN  "
        print(f"{description:<50s} {res} ({part}/{total})")

    times = []
    analyzer_times = {}
    failed_scenarios = {}
    rules = [rule.name for rule in fields(STLAnalyzerResult) if rule.type == Optional[np.ndarray]]

    for scenario_path, result in results.items():
        count("total")
        if not result.without_exception:
            count("exception")
        else:
            result = result.get_result()
            if isinstance(result, EFailureReason):
                count("failed")
                count(f"failed {result.name}")
                failed_scenarios[scenario_path] = result.name
            elif isinstance(result, Osc2CrConverterResult):
                count("success")
                stats = result.statistics
                times.append(stats.sim_time)
                count("vehicle total", stats.num_obstacle_conversions)
                count("vehicle failed", len(stats.failed_obstacle_conversions))
                count(f"sim ending cause {stats.sim_ending_cause.name}")
                if result.xodr_file is not None:
                    count("odr conversions run")
                    if result.xodr_conversion_error is None:
                        count("odr conversions success")

                for t_analyzer, analysis in result.analysis.items():
                    exec_time, analysis = analysis
                    if t_analyzer not in analyzer_times:
                        analyzer_times[t_analyzer] = []
                    analyzer_times[t_analyzer].append(exec_time)
                    count(f"{t_analyzer.__name__} scenario total")
                    count(f"{t_analyzer.__name__} vehicle total", stats.num_obstacle_conversions)
                    for rule in rules:
                        count(f"{t_analyzer.__name__} vehicle {rule.upper()} total", stats.num_obstacle_conversions)
                    scenario_run = True
                    scenario_success = True
                    rules_run = {rule: True for rule in rules}
                    rules_success = {rule: True for rule in rules}
                    for vehicle_name, analyzer_result in analysis.items():
                        vehicle_run = True
                        vehicle_success = True
                        if isinstance(analyzer_result, AnalyzerErrorResult):
                            scenario_run = False
                            scenario_success = False
                            vehicle_run = False
                            vehicle_success = False
                            for rule in rules:
                                rules_run[rule] = False
                                rules_success[rule] = False
                        elif t_analyzer == STLAnalyzer:
                            assert isinstance(analyzer_result, STLAnalyzerResult)
                            for rule in rules:
                                rule_result = getattr(analyzer_result, rule)
                                if rule_result is None:
                                    scenario_run = False
                                    scenario_success = False
                                    vehicle_run = False
                                    vehicle_success = False
                                    rules_run[rule] = False
                                    rules_success[rule] = False
                                elif np.min(rule_result) <= 0.0:
                                    count(f"{t_analyzer.__name__} vehicle {rule.upper()} run")
                                    scenario_success = False
                                    vehicle_success = False
                                    rules_success[rule] = False
                                else:
                                    count(f"{t_analyzer.__name__} vehicle {rule.upper()} run")
                                    count(f"{t_analyzer.__name__} vehicle {rule.upper()} success")
                        elif t_analyzer == DrivabilityAnalyzer:
                            assert isinstance(analyzer_result, DrivabilityAnalyzerResult)
                            if analyzer_result.collision or not analyzer_result.feasibility:
                                scenario_success = False
                                vehicle_success = False
                        elif t_analyzer == SpotAnalyzer:
                            assert isinstance(analyzer_result, SpotAnalyzerResult)
                            for t, t_result in analyzer_result.predictions.items():
                                count(f"{t_analyzer.__name__} single-t total")
                                if isinstance(t_result, AnalyzerErrorResult):
                                    scenario_run = False
                                    scenario_success = False
                                    vehicle_run = False
                                    vehicle_success = False
                                else:
                                    count(f"{t_analyzer.__name__} single-t run")

                        if vehicle_run:
                            count(f"{t_analyzer.__name__} vehicle run")
                        if vehicle_success:
                            count(f"{t_analyzer.__name__} vehicle success")

                    if scenario_run:
                        count(f"{t_analyzer.__name__} scenario run")
                    if scenario_success:
                        count(f"{t_analyzer.__name__} scenario success")

                    if t_analyzer == STLAnalyzer:
                        for rule in rules:
                            count(f"{t_analyzer.__name__} scenario {rule.upper()} total")
                            if rules_run[rule]:
                                count(f"{t_analyzer.__name__} scenario {rule.upper()} run")
                            if rules_success[rule]:
                                count(f"{t_analyzer.__name__} scenario {rule.upper()} success")
            else:
                raise ValueError

    print(f"{'Total num scenarios':<50s} {counts['total']:5d}")
    print(f"{'Average time':<50s} {np.mean(times):}")
    print("-" * 80)
    perc("OpenDRIVE Conversion run rate", "odr conversions run", "success")
    perc("OpenDRIVE Conversion success rate", "odr conversions success", "success")
    perc("", "odr conversions success", "odr conversions run")
    print("-" * 80)
    print("Sim Ending causes:")
    for e_ending_cause in ESimEndingCause:
        perc(f" | {e_ending_cause.name}", f"sim ending cause {e_ending_cause.name}", "success")
    print("\n" + "#" * 80)
    print("Granularity SCENARIO")
    print("-" * 80)
    perc("Conversion success rate", "success", "total")
    perc("Conversion failure rate", "failed", "total")
    for reason in EFailureReason:
        perc(f" | {reason.name}", f"failed {reason.name}", "failed")
    perc("Conversion exception rate", "exception", "total")
    print("-" * 80)
    for path, reason in failed_scenarios.items():
        print(reason, ':', path)
    for t_analyzer in analyzer_times.keys():
        print("-" * 80)
        print(f"{t_analyzer.__name__}")
        print(f"{'Average time':<50s} {np.mean(analyzer_times[t_analyzer]):}")
        perc("run rate", f"{t_analyzer.__name__} scenario run", f"{t_analyzer.__name__} scenario total")
        perc("success rate", f"{t_analyzer.__name__} scenario success", f"{t_analyzer.__name__} scenario total")
        perc("", f"{t_analyzer.__name__} scenario success", f"{t_analyzer.__name__} scenario run")
        if t_analyzer == STLAnalyzer:
            for rule in rules:
                print()
                perc(f"{rule.upper()} run rate", f"{t_analyzer.__name__} scenario {rule.upper()} run",
                     f"{t_analyzer.__name__} scenario {rule.upper()} total")
                perc(f"{rule.upper()} success rate", f"{t_analyzer.__name__} scenario {rule.upper()} success",
                     f"{t_analyzer.__name__} scenario {rule.upper()} total")
                perc("", f"{t_analyzer.__name__} scenario {rule.upper()} success",
                     f"{t_analyzer.__name__} scenario {rule.upper()} run")
    print("\n" + "#" * 80)
    print("Granularity VEHICLE")
    print("-" * 80)
    perc("Conversion success rate", "vehicle failed", "vehicle total", invert=True)
    print("-" * 80)
    for t_analyzer in analyzer_times.keys():
        print("-" * 80)
        print(f"{t_analyzer.__name__}")
        perc("run rate", f"{t_analyzer.__name__} vehicle run", f"{t_analyzer.__name__} vehicle total")
        perc("success rate", f"{t_analyzer.__name__} vehicle success", f"{t_analyzer.__name__} vehicle total")
        perc("", f"{t_analyzer.__name__} vehicle success", f"{t_analyzer.__name__} vehicle run")
        if t_analyzer == STLAnalyzer:
            for rule in rules:
                print()
                perc(f"{rule.upper()} run rate", f"{t_analyzer.__name__} vehicle {rule.upper()} run",
                     f"{t_analyzer.__name__} vehicle {rule.upper()} total")
                perc(f"{rule.upper()} success rate", f"{t_analyzer.__name__} vehicle {rule.upper()} success",
                     f"{t_analyzer.__name__} vehicle {rule.upper()} total")
                perc("", f"{t_analyzer.__name__} vehicle {rule.upper()} success",
                     f"{t_analyzer.__name__} vehicle {rule.upper()} run")
        elif t_analyzer == SpotAnalyzer:
            print()
            perc("Single timestamps run", f"{t_analyzer.__name__} single-t run",
                 f"{t_analyzer.__name__} single-t total")


def print_exception_tracebacks(
        results: Dict[str, BatchConversionResult],
        compressed=True,
):
    """
    Print the exception tracebacks, that raised inside the Converter and caught by the BatchConverter.

    :param results: The result dict returned by the BatchConverter
    :param compressed:bool: If true print only unique errors and a count how often they were raised.
    """
    errors: Dict[AnalyzerErrorResult, int] = {}
    for scenario_path, result in results.items():
        if not result.without_exception:
            if not compressed:
                print(f"{scenario_path}\n{result.exception.traceback_text}\n\n\n")
            else:
                errors[result.exception] = 1 + errors.get(result.exception, 0)

    for error, count in errors.items():
        print(f"{count}\n{error.traceback_text}")
        print("\n" * 3)


def print_exception_tracebacks_for_analyzer(
        results: Dict[str, BatchConversionResult], analyzer: Type[Analyzer],
        granularity: EGranularity = EGranularity.SCENARIO,
        compressed=True,
):
    """
    Print the exception tracebacks, that were raised inside an Analyzer implementation.

    :param results: The result dict returned by the BatchConverter
    :param analyzer:EAnalyzer: Specify of which analyzer the tracebacks shall be printed
    :param granularity: Specify the granularity this shall work on
    :param compressed:bool: If true print only unique errors and a count how often they were raised.
    """
    errors: Dict[AnalyzerErrorResult, int] = {}

    def handle_error(source_file, found_error: AnalyzerErrorResult):
        if not compressed:
            print(f"{source_file}: {found_error.exception_text}\n{found_error.traceback_text}")
        else:
            errors[found_error] = 1 + errors.get(found_error, 0)

    for scenario_path, result in results.items():
        if not result.without_exception:
            continue
        result = result.get_result()
        if isinstance(result, Osc2CrConverterResult):
            analysis = result.analysis
            if analyzer in analysis:
                error = None
                for vehicle_name, analyzer_result in analysis[analyzer][1].items():
                    if isinstance(analyzer_result, AnalyzerErrorResult):
                        error = analyzer_result
                        if granularity == EGranularity.VEHICLE:
                            handle_error(result.xosc_file, error)
                    elif analyzer == SpotAnalyzer and isinstance(analyzer_result, SpotAnalyzerResult):
                        for t, result_at_t in analyzer_result.predictions.items():
                            if isinstance(result_at_t, AnalyzerErrorResult):
                                error = result_at_t
                                if granularity == EGranularity.VEHICLE:
                                    handle_error(result.xosc_file, error)

                if granularity == EGranularity.SCENARIO and error is not None:
                    handle_error(result.xosc_file, error)

    for error, count in errors.items():
        print(f"{count}\n{error.exception_text}\n{error.traceback_text}")
        print("\n" * 3)


def _plot_times(times, n_bins: int, low_pass_filter: Optional[float], path: Optional[str], label=None):
    if low_pass_filter is None:
        fig = plt.figure(figsize=(5, 2.5), tight_layout=True)
        plt.hist(times, bins=n_bins, color=_get_colors(times))
        if label is not None:
            plt.legend(label)
        plt.xlabel("t [s]")
        plt.ylabel("# scenarios")
        plt.show()
    else:
        fig, axs = plt.subplots(2, 1, sharey="all", tight_layout=True, figsize=(10, 5))
        axs[0].hist(times, bins=n_bins, color=_get_colors(times))
        axs[0].set_xlabel("t [s]")
        axs[0].set_ylabel("# scenarios")

        filtered_times = []
        if isinstance(times[0], list):
            for ts in times:
                single_times = []
                for t in ts:
                    if t <= low_pass_filter:
                        single_times.append(t)
                filtered_times.append(single_times)
        else:
            filtered_times = [t for t in times if t <= low_pass_filter]
        axs[1].hist(filtered_times, bins=n_bins, color=_get_colors(times))
        axs[1].set_xlabel("t [s]")
        axs[1].set_ylabel("# scenarios")
        axs[1].set_xlim((0, low_pass_filter))

        if label is not None:
            axs[0].legend(label, loc="upper center")
        fig.show()

    if path is not None:
        fig.savefig(path)


def plot_sim_times(
        results: Union[Dict[str, BatchConversionResult], List[Dict[str, BatchConversionResult]]],
        n_bins: int = 25,
        low_pass_filter: Optional[float] = None,
        path: Optional[str] = None,
        label: Optional[List[str]] = None
):
    """
    Plot the simulation times in a histogram, it can also combine multiple results in one dict, if those are passed as a
    list in the results parameter, resulting in a more colorful dict. See the label param if you want to do this

    :param results: The result dict returned by the BatchConverter or a list of such dicts
    :param n_bins:int: The number of bins used for the histogram
    :param low_pass_filter:float: If present a second plot with only sim times leq than this will be added
    :param path:float: If present the plot will be stored here
    :param label: if multiple results this can be used to specify the labels in the legend of the plot
    """
    times = []
    if isinstance(results, list):
        for res in results:
            times_for_result = []
            for scenario_path, result in res.items():
                if not result.without_exception:
                    continue
                result = result.get_result()
                if isinstance(result, Osc2CrConverterResult):
                    times_for_result.append(result.statistics.sim_time)
            times.append(times_for_result)
    else:
        for scenario_path, result in results.items():
            if not result.without_exception:
                continue
            result = result.get_result()
            if isinstance(result, Osc2CrConverterResult):
                times.append(result.statistics.sim_time)

    _plot_times(times, n_bins, low_pass_filter, path, label)


def plot_exec_times(
        results: Dict[str, BatchConversionResult],
        t_analyzer: Type[Analyzer],
        n_bins: int = 25,
        low_pass_filter: Optional[float] = None,
        path: Optional[str] = None
):
    """
    Plot the execution times for one analyzer in a histogram

    :param results: The result dict returned by the BatchConverter
    :param t_analyzer:EAnalyzer: Specify the analyzer for which the plots shall be drawn
    :param n_bins:int: The number of bins used for the histogram
    :param low_pass_filter:float: If present a second plot with only execution times leq than this will be added
    :param path:float: If present the plot will be stored here
    """
    times = []
    for scenario_path, result in results.items():
        if not result.without_exception:
            continue
        result = result.get_result()
        if isinstance(result, Osc2CrConverterResult):
            if t_analyzer in result.analysis:
                times.append(result.analysis[t_analyzer][0])
    _plot_times(times, n_bins, low_pass_filter, path)


def plot_num_obstacles(
        results: Dict[str, BatchConversionResult],
        low_pass_filter: Optional[int] = None,
        path: Optional[str] = None
):
    """
    Plot how many scenarios have a num of obstacles in them

    :param results: The result dict returned by the BatchConverter
    :param low_pass_filter:float: If present a second plot with only obstacles counts times leq than this will be added
    :param path:float: If present the plot will be stored here
    """
    values = []
    for scenario_path, result in results.items():
        if not result.without_exception:
            continue
        result = result.get_result()
        if isinstance(result, Osc2CrConverterResult):
            values.append(result.statistics.num_obstacle_conversions)

    if low_pass_filter is not None:
        fig, axs = plt.subplots(2, 1, sharey="all", tight_layout=True, figsize=(5, 5))

        x = list(range(max(values) + 1))[1:]
        y = [len([None for v in values if v == x_val]) for x_val in x]
        axs[0].bar(x, y, color=blue)
        axs[0].set_xlabel("# obstacles")
        axs[0].set_ylabel("# scenarios")

        filtered = [v for v in values if v <= low_pass_filter]
        x = list(range(max(filtered) + 1))[1:]
        y = [len([None for v in filtered if v == x_val]) for x_val in x]
        axs[1].bar(x, y, color=blue)
        axs[1].set_xlabel("# obstacles")
        axs[1].set_ylabel("# scenarios")

        fig.show()
    else:
        fig = plt.figure(figsize=(5, 2.5), tight_layout=True)
        x = list(range(max(values) + 1))[1:]
        y = [len([None for v in values if v == x_val]) for x_val in x]
        plt.bar(x, y, color=blue)
        plt.xlabel("# obstacles")
        plt.ylabel("# scenarios")
        fig.show()
    if path is not None:
        fig.savefig(path)


def plot_scenarios(results):
    """
    Plot an overview of all scenarios where:
        - a road network was converted successfully
        - all analyzers ran without an error

    :param results: The result dict returned by the BatchConverter
    """
    prev = Serializable.import_extra_files
    Serializable.import_extra_files = False
    for scenario_path, result in results.items():
        if not result.without_exception:
            continue
        result_without_files = result.get_result()
        if isinstance(result_without_files, Osc2CrConverterResult):
            any_error = False
            for res in result_without_files.analysis.values():
                for r in res[1].values():
                    if isinstance(r, AnalyzerErrorResult):
                        any_error = True
            if any_error:
                continue
            if result_without_files.xodr_conversion_error is not None:
                continue
            Serializable.import_extra_files = True
            result_with_files = result.get_result()
            rnd = MPRenderer()
            if result_with_files.scenario is not None:
                result_with_files.scenario.draw(rnd)
            if result_with_files.planning_problem_set is not None:
                result_with_files.planning_problem_set.draw(rnd)
            plt.show()
            Serializable.import_extra_files = False
    Serializable.import_extra_files = prev
