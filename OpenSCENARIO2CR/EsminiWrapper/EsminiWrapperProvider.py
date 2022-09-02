import os
import re
import sys
from io import BytesIO
from os import path
from typing import Optional
from zipfile import ZipFile

import requests

from OpenSCENARIO2CR.EsminiWrapper.EsminiWrapper import EsminiWrapper


class EsminiWrapperProvider:

    def __init__(self, storage_prefix: Optional[str] = None):
        self.storage_prefix = path.abspath(path.dirname(__file__))
        if storage_prefix is not None:
            self.storage_prefix = storage_prefix

    @property
    def storage_prefix(self) -> str:
        return self._path_prefix

    @storage_prefix.setter
    def storage_prefix(self, new_path_prefix: str):
        if path.exists(new_path_prefix):
            self._path_prefix = new_path_prefix

    def provide_esmini_wrapper(self, version: Optional[str] = None) -> Optional[EsminiWrapper]:
        if version is not None and False:
            if self._try_loading_version(version):
                return EsminiWrapper(self._bin_path(self._esmini_path(version)))
            else:
                print("Failed loading specified esmini version: {}".format(version))
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

    def _bin_path(self, esmini_path: str) -> str:
        return path.abspath(path.join(self.storage_prefix, esmini_path, "esmini", "bin"))

    def _download_esmini(self, version: str) -> bool:
        archive_name = ""
        if sys.platform.startswith("linux"):
            archive_name = "EsminiWrapper-bin_ubuntu.zip"
        elif sys.platform.startswith("darwin"):
            archive_name = "EsminiWrapper-bin_mac_catalina.zip"
        elif sys.platform.startswith("win32"):
            archive_name = "EsminiWrapper-bin_win_x64.zip"
        else:
            print("Unsupported platform: {}".format(sys.platform))
            quit()
        try:
            r = requests.get("/".join(["https://github.com/esmini/esmini/releases/download", version, archive_name]))
            with ZipFile(BytesIO(r.content), "r") as zipObj:
                zipObj.extractall(self._esmini_path(version))
        except requests.exceptions.ConnectionError:
            return False
        return True
