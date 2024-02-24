"""Test __init__.py."""

import idlealign


def extension_exists() -> None:
    assert hasattr(idlealign, "idlealign")
    assert idlealign.__title__ == "idlealign"


def check_installed_exists() -> None:
    assert hasattr(idlealign, "check_installed")
    assert callable(
        idlealign.check_installed,
    )
