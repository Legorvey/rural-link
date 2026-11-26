import importlib
import sys

import pytest

PKGS = ["numpy", "scipy", "pandas", "matplotlib"]


def test_python_version():
    assert (3, 11) <= sys.version_info[:2] < (3, 13)


@pytest.mark.parametrize("pkg", PKGS)
def test_imports(pkg):
    importlib.import_module(pkg)


def test_modules_import():
    for m in ["propagation", "link_budget", "modulation", "channels", "adaptive", "metrics"]:
        importlib.import_module(f"src.{m}")


def test_config_flags_engine_implemented():
    import config

    assert config.SCIENTIFIC_ENGINE_IMPLEMENTED is True
