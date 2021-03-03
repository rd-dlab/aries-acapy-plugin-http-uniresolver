"""Integration tests: Test resolution."""

import asyncio
import json
from pathlib import Path

import pytest

from http_uniresolver import HTTPUniversalDIDResolver

CONFIG_PATH = Path(__file__).parent / "uniresolver_config.json"
TEST_CONFIG = json.loads(CONFIG_PATH.read_text())
TEST_DIDS = [
    did
    for driver in TEST_CONFIG["drivers"]
    for did in driver["testIdentifiers"]
]


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def resolver():
    resolver = HTTPUniversalDIDResolver()
    await resolver.setup(None)
    yield resolver


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "did",
    TEST_DIDS
)
async def test_resolve_and_load(resolver, did):
    assert await asyncio.wait_for(resolver.resolve(None, did), timeout=30)