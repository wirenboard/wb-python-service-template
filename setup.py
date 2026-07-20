#!/usr/bin/env python3

from setuptools import setup


def get_version():
    with open("debian/changelog", "r", encoding="utf-8") as f:
        return f.readline().split()[1][1:-1].split("~")[0]


setup(
    name="wb-python-service-template",
    version=get_version(),
    maintainer="Wiren Board Team",
    maintainer_email="info@wirenboard.com",
    description="Wiren Board Python Service Template",
    url="https://github.com/wirenboard/wb-python-service-template",
    license="MIT",
    packages=[
        # "wb"                        # Explicitly excluded: provided by base package
        "wb.python_service_template",
    ],
    # Other files (scripts, configs and etc):
    # - Installed by debian/install file
    # Requirements:
    # - Installed from debian/control file
)
