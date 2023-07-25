__author__ = "Michael Ratzel, Yuanfei Lin"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["KoSi"]
__version__ = "0.1.0"
__maintainer__ = "Yuanfei Lin"
__email__ = "commonroad@lists.lrz.de"
__status__ = "beta"

import os
import re
import sys
import warnings
from io import BytesIO
from os import path
from typing import Optional
from zipfile import ZipFile

import requests

from osc_cr_converter.wrapper.esmini.esmini_wrapper import EsminiWrapper
from osc_cr_converter.utility.configuration import ConverterParams


class EsminiWrapperProvider:

    """
    This class downloads the wanted esmini version from GitHub and creates an EsminiWrapper from it.

    It works on Mac Windows and Linux
    """

    def __init__(self, config: ConverterParams):
        self.storage_prefix = None
        self.preferred_version = config.esmini.version
        self.config = config

    @property
    def storage_prefix(self) -> str:
        """
        Path prefix where the downloaded binaries shall be stored
        """
        return self._path_prefix

    @storage_prefix.setter
    def storage_prefix(self, new_path_prefix: Optional[str]):
        if new_path_prefix is None:
            self._path_prefix = path.abspath(path.dirname(__file__))
        elif path.exists(new_path_prefix):
            self._path_prefix = new_path_prefix
        else:
            warnings.warn(
                f"<EsminiWrapperProvider/storage_prefix> Path not found {new_path_prefix}"
            )

    @property
    def preferred_version(self) -> Optional[str]:
        """
        The Preferred version of esmini with v2.29.3 being the default, as this is the latest tested version
        """
        return self._preferred_version

    @preferred_version.setter
    def preferred_version(self, new_preferred_version: Optional[str]):
        r = re.compile(r"v\d+\.\d+\.\d+")
        if new_preferred_version is None:
            self._preferred_version = None
        elif new_preferred_version.lower() == "default":
            self._preferred_version = "v2.29.3"
        elif r.fullmatch(new_preferred_version) is not None:
            self._preferred_version = new_preferred_version
        else:
            warnings.warn(
                f"<EsminiWrapperProvider/preferred_version> New version {new_preferred_version} not match {r.pattern}"
            )

    def provide_esmini_wrapper(self) -> Optional[EsminiWrapper]:
        if self.preferred_version is not None:
            if self._try_loading_version(self.preferred_version):
                return EsminiWrapper(
                    self._bin_path(self._esmini_path(self.preferred_version)),
                    self.config,
                )
            else:
                print(
                    "Failed loading specified esmini version: {}".format(
                        self.preferred_version
                    )
                )
                quit()

        try:
            r = requests.get("https://github.com/esmini/esmini/releases/latest")
            version = r.url.split("/")[-1]
            if self._try_loading_version(version):
                return EsminiWrapper(
                    self._bin_path(self._esmini_path(version)), self.config
                )
        except requests.exceptions.ConnectionError:
            pass

        available_versions = sorted(
            [
                dir_path
                for dir_path in os.listdir(self.storage_prefix)
                if re.match(self._esmini_path(""), dir_path)
                and os.path.exists(self._bin_path(dir_path))
            ]
        )

        if len(available_versions) > 0:
            return EsminiWrapper(self._bin_path(available_versions[-1]), self.config)

        return None

    def _try_loading_version(self, version: str) -> bool:
        if not path.exists(self._bin_path(self._esmini_path(version))):
            return self._download_esmini(version)
        return True

    @staticmethod
    def _esmini_path(version: str) -> str:
        return "esmini_{}".format(version)

    def _abs_path(self, rel_path: str) -> str:
        return path.abspath(path.join(self.storage_prefix, rel_path))

    def _bin_path(self, esmini_path: str) -> str:
        return self._abs_path(path.join(esmini_path, "esmini", "bin"))

    def _download_esmini(self, version: str) -> bool:
        archive_name = ""
        if sys.platform.startswith("linux"):
            archive_name = "esmini-bin_ubuntu.zip"
        elif sys.platform.startswith("darwin"):
            archive_name = "esmini-bin_mac_catalina.zip"
        elif sys.platform.startswith("win32"):
            archive_name = "esmini-bin_win_x64.zip"
        else:
            print("Unsupported platform: {}".format(sys.platform))
            quit()
        try:
            r = requests.get(
                "/".join(
                    [
                        "https://github.com/esmini/esmini/releases/download",
                        version,
                        archive_name,
                    ]
                )
            )
            with ZipFile(BytesIO(r.content), "r") as zipObj:
                zipObj.extractall(self._abs_path(self._esmini_path(version)))
        except requests.exceptions.ConnectionError:
            return False
        return True
