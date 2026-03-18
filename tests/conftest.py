"""Pytest configuration.

Sets PLAYGROUND_ENV=development for all tests so that adapter factories
return stub implementations and no Azure credentials are required.
"""

import pytest


@pytest.fixture(autouse=True)
def set_dev_env(monkeypatch):
    """Set PLAYGROUND_ENV=development for every test.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.

    Returns
    -------
    None
    """
    monkeypatch.setenv("PLAYGROUND_ENV", "development")
