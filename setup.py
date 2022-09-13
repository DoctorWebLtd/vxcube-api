#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from collections import OrderedDict

from setuptools import find_packages, setup

__pckg__ = "vxcube-api"
__dpckg__ = __pckg__.replace("-", "_")
__version__ = "unknown"
exec(open(__dpckg__ + "/version.py").read())
print(__pckg__ + " version: " + __version__)


def load_requirements():
    with open(os.path.join(os.getcwd(), "requirements", "requirements.txt")) as requirements:
        return requirements.read().splitlines()


def load_long_description():
    with open(os.path.join(os.getcwd(), "README.md")) as f:
        return f.read()


setup(name=__pckg__,
      version=__version__,
      description="Dr.Web vxCube API Client",
      long_description=load_long_description(),
      long_description_content_type="text/markdown",
      license="Dr.Web",
      author="Doctor Web",
      url="https://www.drweb.com/",
      packages=find_packages(),
      include_package_data=True,
      install_requires=load_requirements(),
      python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*",
      project_urls=OrderedDict((("Code", "https://github.com/DoctorWebLtd/vxcube-api"),
                                ("Issue tracker", "https://github.com/DoctorWebLtd/vxcube-api/issues"))),
      classifiers=[
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: 3.7",
          "Programming Language :: Python :: 3.8",
          "Programming Language :: Python :: 3.9",
      ],
      entry_points={
          "console_scripts": [
              "vxcube_client = vxcube_api.__main__:main",
          ],
      })
