"""Guards the version format in debian/changelog, the single source of the package version.

dpkg would happily build 1.0 or 1.2.3.4, the Wiren Board convention MAJOR.MINOR.PATCH would not.
"""

import importlib.util
import re
from pathlib import Path


def _load_setup():
    # pybuild copies tests/ into .pybuild/*/build without setup.py, so the source root varies in depth
    for parent in Path(__file__).resolve().parents:
        setup_filepath = parent / "setup.py"
        if setup_filepath.is_file():
            spec = importlib.util.spec_from_file_location("_template_setup", setup_filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    raise RuntimeError("setup.py not found above the tests directory")


def test_changelog_version_is_three_numbers():
    version = _load_setup().get_version()
    assert re.match(r"^\d+\.\d+\.\d+$", version), f"expected MAJOR.MINOR.PATCH, got {version!r}"
