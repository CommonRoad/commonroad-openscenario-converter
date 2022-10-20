from dataclasses import fields
from enum import Enum
from typing import Union, Dict, List, Optional

import numpy as np
from matplotlib import pyplot as plt

from BatchConversion.BatchConverter import BatchConversionResult
from OpenSCENARIO2CR.ConversionAnalyzer.AnalyzerErrorResult import AnalyzerErrorResult
from OpenSCENARIO2CR.ConversionAnalyzer.DrivabilityAnalyzer import DrivabilityAnalyzerResult
from OpenSCENARIO2CR.ConversionAnalyzer.EAnalyzer import EAnalyzer
from OpenSCENARIO2CR.ConversionAnalyzer.STLAnalyzer import STLAnalyzerResult
from OpenSCENARIO2CR.ConversionAnalyzer.SpotAnalyzer import SpotAnalyzerResult
from OpenSCENARIO2CR.Osc2CrConverter import EFailureReason
from OpenSCENARIO2CR.Osc2CrConverterResult import Osc2CrConverterResult

plot_color = "#0065BD"


class EGranularity(Enum):
    SCENARIO = 1
    VEHICLE = 2


def analyze_statistics(statistics: Dict[str, BatchConversionResult]):
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
    analyzer_times = {e_analyzer: [] for e_analyzer in list(EAnalyzer)}
    rules = [rule.name for rule in fields(STLAnalyzerResult) if rule.type == Optional[np.ndarray]]

    for scenario_path, result in statistics.items():
        count("total")
        if not result.without_exception:
            count("exception")
        else:
            result = result.conversion_result
            if isinstance(result, EFailureReason):
                count("failed")
                count(f"failed {result.name}")
            elif isinstance(result, Osc2CrConverterResult):
                count("success")
                stats = result.statistics
                times.append(stats.sim_time)
                count("vehicle total", stats.num_obstacle_conversions)
                count("vehicle failed", len(stats.failed_obstacle_conversions))
                if result.xodr_file is not None:
                    count("odr conversions run")
                    if result.xodr_conversion_error is None:
                        count("odr conversions success")

                for e_analyzer, analysis in result.analysis.items():
                    exec_time, analysis = analysis
                    analyzer_times[e_analyzer].append(exec_time)
                    count(f"{e_analyzer.name} scenario total")
                    count(f"{e_analyzer.name} vehicle total", stats.num_obstacle_conversions)
                    for rule in rules:
                        count(f"{e_analyzer.name} vehicle {rule.upper()} total", stats.num_obstacle_conversions)
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
                        elif e_analyzer == EAnalyzer.STL:
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
                                    count(f"{e_analyzer.name} vehicle {rule.upper()} run")
                                    scenario_success = False
                                    vehicle_success = False
                                    rules_success[rule] = False
                                else:
                                    count(f"{e_analyzer.name} vehicle {rule.upper()} run")
                                    count(f"{e_analyzer.name} vehicle {rule.upper()} success")
                        elif e_analyzer == EAnalyzer.DRIVABILITY:
                            assert isinstance(analyzer_result, DrivabilityAnalyzerResult)
                            if analyzer_result.collision or not analyzer_result.feasibility:
                                scenario_success = False
                                vehicle_success = False
                        elif e_analyzer == EAnalyzer.SPOT:
                            assert isinstance(analyzer_result, SpotAnalyzerResult)
                            for t, t_result in analyzer_result.predictions.items():
                                count(f"{e_analyzer.name} single-t total")
                                if isinstance(t_result, AnalyzerErrorResult):
                                    scenario_run = False
                                    scenario_success = False
                                    vehicle_run = False
                                    vehicle_success = False
                                else:
                                    count(f"{e_analyzer.name} single-t run")

                        if vehicle_run:
                            count(f"{e_analyzer.name} vehicle run")
                        if vehicle_success:
                            count(f"{e_analyzer.name} vehicle success")

                    if scenario_run:
                        count(f"{e_analyzer.name} scenario run")
                    if scenario_success:
                        count(f"{e_analyzer.name} scenario success")

                    if e_analyzer == EAnalyzer.STL:
                        for rule in rules:
                            count(f"{e_analyzer.name} scenario {rule.upper()} total")
                            if rules_run[rule]:
                                count(f"{e_analyzer.name} scenario {rule.upper()} run")
                            if rules_success[rule]:
                                count(f"{e_analyzer.name} scenario {rule.upper()} success")
            else:
                raise ValueError

    print(f"{'Total num scenarios':<50s} {counts['total']:5d}")
    print(f"{'Average time':<50s} {np.mean(times):}")
    print("\n" + "#" * 80)
    print("Granularity SCENARIO")
    print("-" * 80)
    perc("Conversion success rate", "success", "total")
    perc("Conversion failure rate", "failed", "total")
    for reason in EFailureReason:
        perc(f" | {reason.name}", f"failed {reason.name}", "failed")
    perc("Conversion exception rate", "exception", "total")
    print("-" * 80)
    perc("OpenDRIVE Conversion run rate", "odr conversions run", "success")
    perc("OpenDRIVE Conversion success rate", "odr conversions success", "success")
    perc("", "odr conversions success", "odr conversions run")
    for e_analyzer in EAnalyzer:
        print("-" * 80)
        print(f"{e_analyzer.name}")
        print(f"{'Average time':<50s} {np.mean(analyzer_times[e_analyzer]):}")
        perc("run rate", f"{e_analyzer.name} scenario run", f"{e_analyzer.name} scenario total")
        perc("success rate", f"{e_analyzer.name} scenario success", f"{e_analyzer.name} scenario total")
        perc("", f"{e_analyzer.name} scenario success", f"{e_analyzer.name} scenario run")
        if e_analyzer == EAnalyzer.STL:
            for rule in rules:
                print()
                perc(f"{rule.upper()} run rate", f"{e_analyzer.name} scenario {rule.upper()} run",
                     f"{e_analyzer.name} scenario {rule.upper()} total")
                perc(f"{rule.upper()} success rate", f"{e_analyzer.name} scenario {rule.upper()} success",
                     f"{e_analyzer.name} scenario {rule.upper()} total")
                perc("", f"{e_analyzer.name} scenario {rule.upper()} success",
                     f"{e_analyzer.name} scenario {rule.upper()} run")
    print("\n" + "#" * 80)
    print("Granularity VEHICLE")
    print("-" * 80)
    perc("Conversion success rate", "vehicle failed", "vehicle total", invert=True)
    print("-" * 80)
    for e_analyzer in EAnalyzer:
        print("-" * 80)
        print(f"{e_analyzer.name}")
        perc("run rate", f"{e_analyzer.name} vehicle run", f"{e_analyzer.name} vehicle total")
        perc("success rate", f"{e_analyzer.name} vehicle success", f"{e_analyzer.name} vehicle total")
        perc("", f"{e_analyzer.name} vehicle success", f"{e_analyzer.name} vehicle run")
        if e_analyzer == EAnalyzer.STL:
            for rule in rules:
                print()
                perc(f"{rule.upper()} run rate", f"{e_analyzer.name} vehicle {rule.upper()} run",
                     f"{e_analyzer.name} vehicle {rule.upper()} total")
                perc(f"{rule.upper()} success rate", f"{e_analyzer.name} vehicle {rule.upper()} success",
                     f"{e_analyzer.name} vehicle {rule.upper()} total")
                perc("", f"{e_analyzer.name} vehicle {rule.upper()} success",
                     f"{e_analyzer.name} vehicle {rule.upper()} run")
        elif e_analyzer == EAnalyzer.SPOT:
            print()
            perc("Single timestamps run", f"{e_analyzer.name} single-t run", f"{e_analyzer.name} single-t total")


def print_exception_tracebacks(
        statistics: Dict[str, BatchConversionResult],
        compressed=True,
):
    errors: Dict[AnalyzerErrorResult, int] = {}
    for scenario_path, result in statistics.items():
        if not result.without_exception:
            if not compressed:
                print(f"{scenario_path}\n{result.exception.traceback_text}\n\n\n")
            else:
                errors[result.exception] = 1 + errors.get(result.exception, 0)

    for error, count in errors.items():
        print(f"{count}\n{error.traceback_text}")
        print("\n" * 3)


def print_exception_tracebacks_for_analyzer(
        statistics: Dict[str, BatchConversionResult], analyzer: EAnalyzer,
        granularity: EGranularity = EGranularity.SCENARIO,
        compressed=True,
):
    errors: Dict[AnalyzerErrorResult, int] = {}

    def handle_error(source_file, found_error: AnalyzerErrorResult):
        if not compressed:
            print(f"{source_file}: {found_error.exception_text}\n{found_error.traceback_text}")
        else:
            errors[found_error] = 1 + errors.get(found_error, 0)

    for scenario_path, result in statistics.items():
        if result.without_exception and isinstance(result.conversion_result, Osc2CrConverterResult):
            analysis = result.conversion_result.analysis
            if analyzer in analysis:
                error = None
                for vehicle_name, analyzer_result in analysis[analyzer][1].items():
                    if isinstance(analyzer_result, AnalyzerErrorResult):
                        error = analyzer_result
                        if granularity == EGranularity.VEHICLE:
                            handle_error(result.conversion_result.xosc_file, error)
                    elif analyzer == EAnalyzer.SPOT and isinstance(analyzer_result, SpotAnalyzerResult):
                        for t, result_at_t in analyzer_result.predictions.items():
                            if isinstance(result_at_t, AnalyzerErrorResult):
                                error = result_at_t
                                if granularity == EGranularity.VEHICLE:
                                    handle_error(result.conversion_result.xosc_file, error)

                if granularity == EGranularity.SCENARIO and error is not None:
                    handle_error(result.conversion_result.xosc_file, error)

    for error, count in errors.items():
        print(f"{count}\n{error.exception_text}\n{error.traceback_text}")
        print("\n" * 3)


def _plot_times(times, n_bins: int, low_pass_filter: Optional[float], path: Optional[str]):
    global plot_color
    if low_pass_filter is None:
        fig = plt.figure(figsize=(5, 2.5), tight_layout=True)
        plt.hist(times, bins=n_bins, color=plot_color)
        plt.xlabel("t [s]")
        plt.ylabel("# scenarios")
        plt.show()
    else:
        fig, axs = plt.subplots(2, 1, sharey="all", tight_layout=True, figsize=(5, 5))
        axs[0].hist(times, bins=n_bins, color=plot_color)
        axs[0].set_xlabel("t [s]")
        axs[0].set_ylabel("# scenarios")

        axs[1].hist([t for t in times if t <= low_pass_filter], bins=n_bins, color=plot_color)
        axs[1].set_xlabel("t [s]")
        axs[1].set_ylabel("# scenarios")
        axs[1].set_xlim((0, low_pass_filter))
        fig.show()

    if path is not None:
        fig.savefig(path)


def plot_sim_times(results, n_bins: int = 25, low_pass_filter: float = None, path: Optional[str] = None):
    times = []
    for scenario_path, result in results.items():
        if result.without_exception and isinstance(result.conversion_result, Osc2CrConverterResult):
            times.append(result.conversion_result.statistics.sim_time)
    _plot_times(times, n_bins, low_pass_filter, path)


def plot_exec_times(results: dict, e_analyzer: EAnalyzer, n_bins: int = 25, low_pass_filter: Optional[float] = None,
                    path: Optional[str] = None):
    times = []
    for scenario_path, result in results.items():
        if result.without_exception and isinstance(result.conversion_result, Osc2CrConverterResult):
            if e_analyzer in result.conversion_result.analysis:
                times.append(result.conversion_result.analysis[e_analyzer][0])
    _plot_times(times, n_bins, low_pass_filter, path)


def plot_num_obstacles(results, low_pass_filter: Optional[int] = None, path: Optional[str] = None):
    global plot_color
    values = []
    for scenario_path, result in results.items():
        if result.without_exception and isinstance(result.conversion_result, Osc2CrConverterResult):
            values.append(result.conversion_result.statistics.num_obstacle_conversions)

    if low_pass_filter is not None:
        fig, axs = plt.subplots(2, 1, sharey="all", tight_layout=True, figsize=(5, 5))

        x = list(range(max(values) + 1))[1:]
        y = [len([None for v in values if v == x_val]) for x_val in x]
        axs[0].bar(x, y, color=plot_color)
        axs[0].set_xlabel("# obstacles")
        axs[0].set_ylabel("# scenarios")

        filtered = [v for v in values if v <= low_pass_filter]
        x = list(range(max(filtered) + 1))[1:]
        y = [len([None for v in filtered if v == x_val]) for x_val in x]
        axs[1].bar(x, y, color=plot_color)
        axs[1].set_xlabel("# obstacles")
        axs[1].set_ylabel("# scenarios")

        fig.show()
    else:
        fig = plt.figure(figsize=(5, 2.5), tight_layout=True)
        x = list(range(max(values) + 1))[1:]
        y = [len([None for v in values if v == x_val]) for x_val in x]
        plt.bar(x, y, color=plot_color)
        plt.xlabel("# obstacles")
        plt.ylabel("# scenarios")
        fig.show()
    if path is not None:
        fig.savefig(path)
