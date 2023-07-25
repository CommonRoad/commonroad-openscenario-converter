__author__ = "Michael Ratzel, Yuanfei Lin"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["KoSi"]
__version__ = "0.1.0"
__maintainer__ = "Yuanfei Lin"
__email__ = "commonroad@lists.lrz.de"
__status__ = "beta"

import logging
import os
from osc_cr_converter.utility.configuration import ConverterParams


def initialize_logger(config: ConverterParams) -> logging.Logger:
    # create log directory
    os.makedirs(config.general.path_output_log, exist_ok=True)

    # create logger
    logger = logging.getLogger()

    # create file handler (outputs to file)
    path_log = os.path.join(
        config.general.path_output_log, f"convert_{config.general.string_date_time}.log"
    )
    file_handler = logging.FileHandler(path_log)

    # set logging levels
    logger.setLevel(config.debug.logging_level)
    file_handler.setLevel(config.debug.logging_level)

    # create log formatter
    formatter = logging.Formatter(
        "%(levelname)-8s [%(asctime)s] --- %(message)s (%(filename)s:%(lineno)s)",
        "%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)

    # add handlers
    logger.addHandler(file_handler)

    return logger


def print_and_log_debug(logger: logging.Logger, message: str, verbose: bool = False):
    if verbose:
        print(message)
    logger.debug(message)


def print_and_log_info(logger: logging.Logger, message: str, verbose: bool = False):
    if verbose:
        print(message)
    logger.info(message)


def print_and_log_warning(logger: logging.Logger, message: str, verbose: bool = False):
    if verbose:
        print(message)
    logger.warning(message)


def print_and_log_error(logger: logging.Logger, message: str, verbose: bool = False):
    if verbose:
        print(message)
    logger.error(message)
