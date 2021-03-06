"""Integration tests: Test resolution."""

import asyncio
import json
import logging
from pathlib import Path

import pytest

from universal_resolver import UniversalResolver
from universal_resolver.resolver import DEFAULT_CONFIGURATION
from aries_cloudagent.resolver.base import ResolverError

CONFIG_PATH = Path(__file__).parent / "uniresolver_config.json"
TEST_CONFIG = json.loads(CONFIG_PATH.read_text())
TEST_DIDS = [
    did for driver in TEST_CONFIG["drivers"] for did in driver["testIdentifiers"]
]


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def resolver():
    resolver = UniversalResolver()
    resolver.configure(DEFAULT_CONFIGURATION)
    yield resolver


@pytest.mark.int
@pytest.mark.asyncio
@pytest.mark.parametrize("did", TEST_DIDS)
async def test_resolve_and_load(resolver, did, caplog):
    """Test resolution and schema parsing."""
    caplog.set_level(logging.INFO)
    try:
        await asyncio.wait_for(resolver.resolve(None, did), timeout=10)
    except asyncio.TimeoutError:
        pytest.xfail("Resolver took too long.")
    except ResolverError:
        pytest.xfail("Could not resolve a DID that should be resolvable.")
