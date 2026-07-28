import re

import pytest

from wb.python_service_template import main
from wb.python_service_template.version import get_version

# WB Debian packaging expects exactly MAJOR.MINOR.PATCH. Neither dpkg nor PEP 440 enforces it,
# both accept 1.0 and 1.2.3.4, so this test is the only thing that does.
RELEASE_VERSION_PATTERN = re.compile(r"\d+\.\d+\.\d+")


def _is_release_version(package_version):
    return RELEASE_VERSION_PATTERN.fullmatch(package_version) is not None


def test_installed_version_is_release_version():
    package_version = get_version()
    assert _is_release_version(
        package_version
    ), f"version '{package_version}' from debian/changelog is not MAJOR.MINOR.PATCH"


@pytest.mark.parametrize("package_version", ["1.0.0", "10.20.300"])
def test_release_versions_are_accepted(package_version):
    assert _is_release_version(package_version)


@pytest.mark.parametrize("package_version", ["1.0", "1.0.0.1", "1.0.0~exp~branch~2~gdeadbee"])
def test_other_versions_are_rejected(package_version):
    assert not _is_release_version(package_version)


def test_version_argument_prints_version_and_exits(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main.main(["wb-python-service-template", "--version"])

    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == get_version()
