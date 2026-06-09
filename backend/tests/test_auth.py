from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

import auth


def _run(coro):
    return asyncio.run(coro)


def test_disabled_when_no_key_configured(monkeypatch):
    monkeypatch.setattr(auth, "API_KEY", "")
    # Should not raise even with nothing provided.
    _run(auth.verify_api_key(x_api_key=None, api_key=None))


def test_accepts_matching_header(monkeypatch):
    monkeypatch.setattr(auth, "API_KEY", "s3cret")
    _run(auth.verify_api_key(x_api_key="s3cret", api_key=None))


def test_accepts_matching_query(monkeypatch):
    monkeypatch.setattr(auth, "API_KEY", "s3cret")
    _run(auth.verify_api_key(x_api_key=None, api_key="s3cret"))


def test_rejects_wrong_key(monkeypatch):
    monkeypatch.setattr(auth, "API_KEY", "s3cret")
    with pytest.raises(HTTPException) as exc:
        _run(auth.verify_api_key(x_api_key="nope", api_key=None))
    assert exc.value.status_code == 401


def test_rejects_missing_key(monkeypatch):
    monkeypatch.setattr(auth, "API_KEY", "s3cret")
    with pytest.raises(HTTPException) as exc:
        _run(auth.verify_api_key(x_api_key=None, api_key=None))
    assert exc.value.status_code == 401
