from dataclasses import fields
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
                for e_analyzer, analysis in result.analysis.items():
                    exec_time, analysis = analysis
                    analyzer_times[e_analyzer].append(exec_time)
                    count(f"{e_analyzer.name} scenario total")
                    scenario_run = True
                    scenario_success = True
                    rules_run = {rule: True for rule in rules}
                    rules_success = {rule: True for rule in rules}
                    for vehicle_name, analyzer_result in analysis.items():
                        count(f"{e_analyzer.name} vehicle total")
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
                                    count(f"{e_analyzer.name} vehicle {rule.upper()} total")
                                    scenario_run = False
                                    scenario_success = False
                                    vehicle_run = False
                                    vehicle_success = False
                                    rules_run[rule] = False
                                    rules_success[rule] = False
                                elif np.min(rule_result) <= 0.0:
                                    count(f"{e_analyzer.name} vehicle {rule.upper()} total")
                                    count(f"{e_analyzer.name} vehicle {rule.upper()} run")
                                    scenario_success = False
                                    vehicle_success = False
                                    rules_success[rule] = False
                                else:
                                    count(f"{e_analyzer.name} vehicle {rule.upper()} total")
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
                                    continue
                                else:
                                    count(f"{e_analyzer.name} single-t run")
                                if len(t_result) != stats.num_obstacle_conversions - 1:
                                    scenario_success = False
                                    vehicle_success = False
                                else:
                                    count(f"{e_analyzer.name} single-t success")

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
            perc("Single timestamps success", f"{e_analyzer.name} single-t success",
                 f"{e_analyzer.name} single-t total")


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
    for scenario_path, result in statistics.items():
        if result.without_exception and isinstance(result.conversion_result, Osc2CrConverterResult):
            analysis = result.conversion_result.analysis
            if analyzer in analysis:
                error = None
                for vehicle_name, analyzer_result in analysis[analyzer][1].items():
                    if isinstance(analyzer_result, AnalyzerErrorResult):
                        error = analyzer_result
                        if granularity == EGranularity.VEHICLE:
                            if not compressed:
                                print(f"{result.conversion_result.source_file}\n{analyzer_result.traceback_text}")
                            else:
                                errors[analyzer_result] = 1 + errors.get(analyzer_result, 0)
                if granularity == EGranularity.SCENARIO and error is not None:
                    if not compressed:
                        print(f"{result.conversion_result.source_file}\n{error.traceback_text}\n\n\n")
                    else:
                        errors[error] = 1 + errors.get(error, 0)

    for error, count in errors.items():
        print(f"{count}\n{error.exception_text}\n{error.traceback_text}")
        print("\n" * 3)


def plot_times(results, n_bins: int = 25, low_pass_filter: float = 50.0):
    global plot_color
    times = []
    for scenario_path, result in results.items():
        if result.without_exception and isinstance(result.conversion_result, Osc2CrConverterResult):
            times.append(result.conversion_result.statistics.sim_time)
    fig, axs = plt.subplots(2, 1, sharey="all", tight_layout=True, figsize=(5, 5))
    axs[0].hist(times, bins=n_bins, color=plot_color)
    axs[0].set_xlabel("t [s]")
    axs[0].set_ylabel("# scenarios")

    axs[1].hist([t for t in times if t <= low_pass_filter], bins=n_bins, color=plot_color)
    axs[1].set_xlabel("t [s]")
    axs[1].set_ylabel("# scenarios")
    fig.show()


def plot_num_obstacles(results, low_pass_filter: int = 10):
    global plot_color
    values = []
    for scenario_path, result in results.items():
        if result.without_exception and isinstance(result.conversion_result, Osc2CrConverterResult):
            values.append(result.conversion_result.statistics.num_obstacle_conversions)
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


def plot_exec_times(results, e_analyzer: EAnalyzer, n_bins: int = 25, low_pass_filter: int = 10):
    global plot_color
    times = []
    for scenario_path, result in results.items():
        if result.without_exception and isinstance(result.conversion_result, Osc2CrConverterResult):
            if e_analyzer in result.conversion_result.analysis:
                times.append(result.conversion_result.analysis[e_analyzer][0])
    fig, axs = plt.subplots(2, 1, sharey="all", tight_layout=True, figsize=(5, 5))
    axs[0].hist(times, bins=n_bins, color=plot_color)
    axs[0].set_xlabel("t [s]")
    axs[0].set_ylabel("# scenarios")

    axs[1].hist([t for t in times if t <= low_pass_filter], bins=n_bins, color=plot_color)
    axs[1].set_xlabel("t [s]")
    axs[1].set_ylabel("# scenarios")
    fig.show()
