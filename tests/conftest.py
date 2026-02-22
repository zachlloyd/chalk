import json
import os
import sys

import pytest

# Ensure services are importable
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

CATALOG_PATH = os.path.join(
    ROOT, "services", "sector-sim", "data", "catalog.json"
)
SCHEMA_PATH = os.path.join(
    ROOT, "services", "sector-sim", "schemas", "catalog_schema.json"
)


@pytest.fixture
def catalog():
    with open(CATALOG_PATH, "r") as f:
        return json.load(f)


@pytest.fixture
def catalog_schema():
    with open(SCHEMA_PATH, "r") as f:
        return json.load(f)
