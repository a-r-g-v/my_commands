#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import sys
from shutil import rmtree

from setuptools import find_packages, setup, Command

# Package meta-data.
NAME = 'daily_report'
DESCRIPTION = 'Daily Reporter'
URL = 'https://github.com/a-r-g-v/mycommands'
EMAIL = 'info@arg.vc'
AUTHOR = 'Yuki Mukasa'
REQUIRES_PYTHON = '>=3.4.0'

# What packages are required for this module to be executed?
REQUIRED = [
        "requests", "click", "selenium", "chromedriver-binary", "arrow"
]

# Where the magic happens:
setup(
    name=NAME,
    description=DESCRIPTION,
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    py_modules=['daily_report'],
    entry_points={
        'console_scripts': ['daily_report=daily_report:main'],
    },
    install_requires=REQUIRED,
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
)
