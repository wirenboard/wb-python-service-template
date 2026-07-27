#!/usr/bin/env python3

from pathlib import Path

from setuptools import setup

# Resolved from this file, not from the current directory, so the version reads the same from anywhere
CHANGELOG_FILEPATH = Path(__file__).resolve().parent / "debian" / "changelog"


def get_version():
    with open(CHANGELOG_FILEPATH, "r", encoding="utf-8") as f:
        return f.readline().split()[1][1:-1].split("~")[0]


# Guarded so tests can import this file and reuse get_version() without running the packaging call
if __name__ == "__main__":
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
