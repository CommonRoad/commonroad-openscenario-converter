#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='commonroad-openscenario-converter',
      version='0.0.1',
      description='Converter between OpenSCENARIO and CommonRoad formats',
      keywords="scenario description, autonomous driving",
      author='Yuanfei Lin, Michael Ratzel',
      author_email='yuanfei.lin@tum.de',
      license='BSD 3-Clause',
      packages=find_packages(),
      install_requires=[
          'commonroad-io>=2023.1',
          'commonroad-scenario-designer>=0.7.0',
          'matplotlib>=3.5.2',
          'imageio>=2.28.1',
          'numpy>=1.19.0',
          'tqdm>=4.65.0',
          'scenariogeneration>=0.9.0',
      ],
      extras_require={
          'tests': [
              'pytest>=7.1'
          ]
      },
      classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: Linux",
      ]
)

