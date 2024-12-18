#!/usr/bin/env python

import os
from setuptools import setup, find_packages

this_directory = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(this_directory, "README.md"), "r", encoding="utf-8") as f:
    readme = f.read()


setup(
    name="commonroad-openscenario-converter",
    version="0.1.1",
    description="Converter between OpenSCENARIO and CommonRoad formats",
    keywords="scenario description, autonomous driving",
    long_description_content_type="text/markdown",
    long_description=readme,
    url="https://commonroad.in.tum.de/tools/openscenario-converter",
    project_urls={
        "Documentation": "https://cps.pages.gitlab.lrz.de/commonroad/commonroad-openscenario-converter/",
        "Forum": "https://commonroad.in.tum.de/forum/c/dataset-converter/",
        "Source": "https://gitlab.lrz.de/tum-cps/commonroad-openscenario-converter",
    },
    author="Yuanfei Lin, Michael Ratzel, Matthias Althoff",
    author_email="yuanfei.lin@tum.de",
    license="BSD 3-Clause",
    data_files=[(".", ["LICENSE"])],
    packages=find_packages(),
    install_requires=[
        "commonroad-io>=2024.2",
        "commonroad-scenario-designer>=0.8.2",
        "imageio>=2.28.1",
        "numpy>=1.19.0",
        "tqdm>=4.65.0",
        "scenariogeneration>=0.9.0"
    ],
    extras_require={"tests": ["pytest>=7.1"]},
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: Linux",
    ],
)
