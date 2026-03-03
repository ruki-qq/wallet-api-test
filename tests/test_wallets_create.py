import uuid

import pytest

from .conftest import API_URL


@pytest.mark.asyncio
async def test_create_wallet_default_balance(client):
    resp = await client.post(API_URL, json={})
    assert resp.status_code == 201

    data = resp.json()
    assert "wallet_uuid" in data
    assert data["balance"] == 0

    wallet_id = data["wallet_uuid"]
    resp2 = await client.get(f"{API_URL}/{wallet_id}")
    assert resp2.status_code == 200
    assert resp2.json()["balance"] == 0


@pytest.mark.asyncio
async def test_create_wallet_with_custom_uuid_and_balance(client):
    wallet_id = str(uuid.uuid4())

    resp = await client.post(API_URL, json={"wallet_uuid": wallet_id, "balance": 123})
    assert resp.status_code == 201
    assert resp.json()["wallet_uuid"] == wallet_id
    assert resp.json()["balance"] == 123


@pytest.mark.asyncio
async def test_create_wallet_duplicate_uuid_returns_409(client):
    wallet_id = str(uuid.uuid4())

    r1 = await client.post(API_URL, json={"wallet_uuid": wallet_id})
    assert r1.status_code == 201

    r2 = await client.post(API_URL, json={"wallet_uuid": wallet_id})
    assert r2.status_code == 409
