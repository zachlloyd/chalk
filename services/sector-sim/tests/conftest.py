"""Shared fixtures for sector-sim tests."""

import json
import pathlib

import pytest

BASE = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def catalog():
    with open(BASE / "data" / "catalog.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def schema():
    with open(BASE / "schemas" / "catalog.schema.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def fallbacks():
    with open(BASE / "render" / "fallbacks.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def semantics():
    with open(BASE / "sim" / "semantics.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def neon_def(catalog):
    return catalog["primitives"]["neon_light_strip_v2"]
