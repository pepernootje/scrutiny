"""Runtime configuration and adapter factory functions.

``PLAYGROUND_ENV`` is read **only** in this module — nowhere else.
Azure SDK classes are imported lazily inside factory functions — never at
module top level.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_VALID_ENVS = {"production", "development"}


@dataclass
class RunConfig:
    """Runtime configuration resolved from environment variables.

    Parameters
    ----------
    env : str
        One of ``"production"`` or ``"development"``.
    is_production : bool
        ``True`` when running in production mode.
    azure_search_endpoint : str
        Azure AI Search endpoint URL.  Empty in development mode.
    azure_openai_endpoint : str
        Azure OpenAI endpoint URL.  Empty in development mode.
    azure_openai_api_key : str
        Azure OpenAI API key.  Empty in development mode.
    azure_openai_api_version : str
        Azure OpenAI API version.
    """

    env: str
    is_production: bool
    azure_search_endpoint: str
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_api_version: str


def resolve_config() -> RunConfig:
    """Resolve runtime configuration from environment variables.

    Reads ``PLAYGROUND_ENV`` (default ``"development"``) and the Azure
    service environment variables.

    Parameters
    ----------
    None

    Returns
    -------
    RunConfig
        Resolved runtime configuration.
    """
    env = os.environ.get("PLAYGROUND_ENV", "development").lower()
    if env not in _VALID_ENVS:
        logger.warning(
            "Unknown PLAYGROUND_ENV=%r; defaulting to 'development'", env
        )
        env = "development"

    is_production = env == "production"

    config = RunConfig(
        env=env,
        is_production=is_production,
        azure_search_endpoint=os.environ.get("AZURE_SEARCH_ENDPOINT", ""),
        azure_openai_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
        azure_openai_api_key=os.environ.get("AZURE_OPENAI_API_KEY", ""),
        azure_openai_api_version=os.environ.get(
            "AZURE_OPENAI_API_VERSION", "2024-02-01"
        ),
    )
    logger.debug("Resolved config: env=%s, is_production=%s", env, is_production)
    return config


def make_search_adapter(
    run_config: RunConfig, demo_mode: bool = False
):
    """Create and return the appropriate search adapter.

    Parameters
    ----------
    run_config : RunConfig
        Resolved runtime configuration.
    demo_mode : bool
        When ``True``, returns a stub adapter in demo mode.

    Returns
    -------
    SearchAdapter
        An instance of either ``AzureSearchAdapter`` or ``StubSearchAdapter``.
    """
    if run_config.is_production and not demo_mode:
        from azure.identity import DefaultAzureCredential  # noqa: PLC0415

        from scrutiny.adapters.azure_search import (  # noqa: PLC0415
            AzureSearchAdapter,
        )

        credential = DefaultAzureCredential()
        logger.debug(
            "Creating AzureSearchAdapter endpoint=%s",
            run_config.azure_search_endpoint,
        )
        return AzureSearchAdapter(
            endpoint=run_config.azure_search_endpoint,
            credential=credential,
        )

    from scrutiny.adapters.stub_search import StubSearchAdapter  # noqa: PLC0415

    logger.debug(
        "Creating StubSearchAdapter demo_mode=%s", demo_mode
    )
    return StubSearchAdapter(demo_mode=demo_mode)


def make_classification_adapter(
    run_config: RunConfig, demo_mode: bool = False
):
    """Create and return the appropriate classification adapter.

    Parameters
    ----------
    run_config : RunConfig
        Resolved runtime configuration.
    demo_mode : bool
        When ``True``, returns a stub adapter in demo mode.

    Returns
    -------
    ClassificationAdapter
        An instance of either ``AzureClassificationAdapter`` or
        ``StubClassificationAdapter``.
    """
    if run_config.is_production and not demo_mode:
        from scrutiny.adapters.azure_classification import (  # noqa: PLC0415
            AzureClassificationAdapter,
        )

        logger.debug(
            "Creating AzureClassificationAdapter endpoint=%s",
            run_config.azure_openai_endpoint,
        )
        return AzureClassificationAdapter(
            endpoint=run_config.azure_openai_endpoint,
            api_key=run_config.azure_openai_api_key,
            api_version=run_config.azure_openai_api_version,
        )

    from scrutiny.adapters.stub_classification import (  # noqa: PLC0415
        StubClassificationAdapter,
    )

    logger.debug(
        "Creating StubClassificationAdapter demo_mode=%s", demo_mode
    )
    return StubClassificationAdapter(demo_mode=demo_mode)
