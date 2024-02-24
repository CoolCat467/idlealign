"""Test __init__.py."""

import idlealign

assert hasattr(idlealign, "idlealign")
assert idlealign.__title__ == "idlealign"
assert hasattr(idlealign, "check_installed")
assert callable(
    idlealign.check_installed,
)
