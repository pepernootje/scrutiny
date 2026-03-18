"""Tests for scrutiny.config."""

import pytest

from scrutiny.adapters.stub_classification import StubClassificationAdapter
from scrutiny.adapters.stub_search import StubSearchAdapter
from scrutiny.config import (
    RunConfig,
    make_classification_adapter,
    make_search_adapter,
    resolve_config,
)


class TestResolveConfig:
    def test_development_mode(self, monkeypatch):
        monkeypatch.setenv("PLAYGROUND_ENV", "development")
        config = resolve_config()
        assert config.env == "development"
        assert config.is_production is False

    def test_production_mode(self, monkeypatch):
        monkeypatch.setenv("PLAYGROUND_ENV", "production")
        config = resolve_config()
        assert config.env == "production"
        assert config.is_production is True

    def test_unknown_env_defaults_to_development(self, monkeypatch):
        monkeypatch.setenv("PLAYGROUND_ENV", "bogus")
        config = resolve_config()
        assert config.env == "development"
        assert config.is_production is False

    def test_missing_env_defaults_to_development(self, monkeypatch):
        monkeypatch.delenv("PLAYGROUND_ENV", raising=False)
        config = resolve_config()
        assert config.env == "development"

    def test_azure_env_vars(self, monkeypatch):
        monkeypatch.setenv("PLAYGROUND_ENV", "development")
        monkeypatch.setenv("AZURE_SEARCH_ENDPOINT", "https://search.example.com")
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://openai.example.com")
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "secret-key")
        config = resolve_config()
        assert config.azure_search_endpoint == "https://search.example.com"
        assert config.azure_openai_endpoint == "https://openai.example.com"
        assert config.azure_openai_api_key == "secret-key"


class TestMakeSearchAdapter:
    def test_dev_mode_returns_stub(self):
        run_config = RunConfig(
            env="development",
            is_production=False,
            azure_search_endpoint="",
            azure_openai_endpoint="",
            azure_openai_api_key="",
            azure_openai_api_version="2024-02-01",
        )
        adapter = make_search_adapter(run_config)
        assert isinstance(adapter, StubSearchAdapter)

    def test_demo_mode_returns_stub(self):
        run_config = RunConfig(
            env="development",
            is_production=False,
            azure_search_endpoint="",
            azure_openai_endpoint="",
            azure_openai_api_key="",
            azure_openai_api_version="2024-02-01",
        )
        adapter = make_search_adapter(run_config, demo_mode=True)
        assert isinstance(adapter, StubSearchAdapter)


class TestMakeClassificationAdapter:
    def test_dev_mode_returns_stub(self):
        run_config = RunConfig(
            env="development",
            is_production=False,
            azure_search_endpoint="",
            azure_openai_endpoint="",
            azure_openai_api_key="",
            azure_openai_api_version="2024-02-01",
        )
        adapter = make_classification_adapter(run_config)
        assert isinstance(adapter, StubClassificationAdapter)
