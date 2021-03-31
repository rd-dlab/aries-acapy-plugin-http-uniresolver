"""HTTP Universal DID Resolver."""

import logging
import json
import os
from pathlib import Path
from typing import Sequence

import aiohttp
import yaml
from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.connections.models.diddoc_v2 import DIDDoc
from aries_cloudagent.core.profile import Profile
from aries_cloudagent.resolver.base import (
    BaseDIDResolver, DIDNotFound, ResolverError, ResolverType
)
from aries_cloudagent.resolver.did import DID

LOGGER = logging.getLogger(__name__)


class HTTPUniversalDIDResolver(BaseDIDResolver):
    """Universal DID Resolver with HTTP bindings."""

    def __init__(self):
        """Initialize HTTPUniversalDIDResolver."""
        super().__init__(ResolverType.NON_NATIVE)
        self._endpoint = None
        self._supported_methods = None

    async def setup(self, _context: InjectionContext):
        """Preform setup, populate supported method list, configuration."""
        config_file = os.environ.get(
            "UNI_RESOLVER_CONFIG",
            Path(__file__).parent / "default_config.yml"
        )
        try:
            with open(config_file) as input_yaml:
                configuration = yaml.load(input_yaml, Loader=yaml.SafeLoader)
        except FileNotFoundError as err:
            raise ResolverError(
                f"Failed to load configuration file for {self.__class__.__name__}"
            ) from err
        assert isinstance(configuration, dict)
        self.configure(configuration)

    def configure(self, configuration: dict):
        """Configure this instance of the resolver from configuration dict."""
        try:
            self._endpoint = configuration["endpoint"]
            self._supported_methods = configuration["methods"]
        except KeyError as err:
            raise ResolverError(
                f"Failed to configure {self.__class__.__name__}, "
                "missing attribute in configuration: {err}"
            ) from err

    @property
    def supported_methods(self) -> Sequence[str]:
        """Return supported methods.

        By determining methods from config file, we preserve the ability to not
        use the universal resolver for a given method, even if the universal
        is capable of resolving that method.
        """
        return self._supported_methods

    async def _resolve(self, _profile: Profile, did: DID) -> DIDDoc:
        """Resolve DID through remote universal resolver."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self._endpoint}/{did}") as resp:
                if resp.status == 200:
                    doc = await resp.json()
                    LOGGER.info("Retrieved doc: %s", json.dumps(doc["didDocument"], indent=2))
                    return DIDDoc.deserialize(doc["didDocument"])
                if resp.status == 404:
                    raise DIDNotFound(f"{did} not found by {self.__class__.__name__}")

                text = await resp.text()
                raise ResolverError(
                    f"Unexecpted status from universal resolver ({resp.status}): {text}"
                )
