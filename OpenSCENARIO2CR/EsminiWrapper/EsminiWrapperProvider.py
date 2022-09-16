import os
import re
import sys
import warnings
from io import BytesIO
from multiprocessing import Lock
from os import path
from typing import Optional
from zipfile import ZipFile

import requests

from OpenSCENARIO2CR.EsminiWrapper.EsminiWrapper import EsminiWrapper


class EsminiWrapperProvider:
    __lock: Lock = Lock()

    def __init__(self, storage_prefix: Optional[str] = None, preferred_version: Optional[str] = None):
        self.storage_prefix = path.abspath(path.dirname(__file__)) if storage_prefix is None else storage_prefix
        self.preferred_version = preferred_version

    @property
    def storage_prefix(self) -> str:
        return self._path_prefix

    @storage_prefix.setter
    def storage_prefix(self, new_path_prefix: str):
        if path.exists(new_path_prefix):
            self._path_prefix = new_path_prefix
        else:
            warnings.warn(f"<EsminiWrapperProvider/storage_prefix> Path not found {new_path_prefix}")

    @property
    def preferred_version(self) -> Optional[str]:
        return self._preferred_version

    @preferred_version.setter
    def preferred_version(self, new_preferred_version: Optional[str]):
        if new_preferred_version is None:
            self._preferred_version = None
        elif re.fullmatch(r"v\d+\.\d+\.\d+", new_preferred_version) is not None:
            self._preferred_version = new_preferred_version
        else:
            warnings.warn(
                f"<EsminiWrapperProvider/preferred_version> Newversion  {new_preferred_version} not match {r.pattern}")

    @classmethod
    def __get_lock(cls):
        return cls.__lock

    def provide_esmini_wrapper(self) -> Optional[EsminiWrapper]:
        with self.__get_lock():
            if self.preferred_version is not None:
                if self._try_loading_version(self.preferred_version):
                    return EsminiWrapper(self._bin_path(self._esmini_path(self.preferred_version)))
                else:
                    print("Failed loading specified esmini version: {}".format(self.preferred_version))
                    quit()

            try:
                r = requests.get('https://github.com/esmini/esmini/releases/latest')
                version = r.url.split("/")[-1]
                if self._try_loading_version(version):
                    return EsminiWrapper(self._bin_path(self._esmini_path(version)))
            except requests.exceptions.ConnectionError:
                pass

            available_versions = sorted([
                dir_path for dir_path in os.listdir(self.storage_prefix)
                if re.match(self._esmini_path(""), dir_path) and os.path.exists(self._bin_path(dir_path))
            ])

            if len(available_versions) > 0:
                return EsminiWrapper(self._bin_path(available_versions[-1]))

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
            r = requests.get("/".join(["https://github.com/esmini/esmini/releases/download", version, archive_name]))
            with ZipFile(BytesIO(r.content), "r") as zipObj:
                zipObj.extractall(self._abs_path(self._esmini_path(version)))
        except requests.exceptions.ConnectionError:
            return False
        return True
