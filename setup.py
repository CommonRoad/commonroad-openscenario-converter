#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='openscenario-commonroad-converter',
      version='0.0.1',
      description='Converter between OpenSCENARIO and CommonRoad formats',
      keywords="scenario description, autonomous driving",
      author='Yuanfei Lin, Michael Ratzel',
      author_email='yuanfei.lin@tum.de',
      license='BSD 3-Clause',
      packages=find_packages(),
      install_requires=[
          'commonroad-io>=2022.3',
          'matplotlib>=3.5.2',
          'imageio>=2.19.3',
          'enum34>=1.1.10',
          'numpy>=1.8.0',
          'tqdm>=4.64.0',
          'scenariogeneration>=0.9.1',
      ],
      extras_require={
          'tests': [
              'pytest>=7.1'
          ]
      })

