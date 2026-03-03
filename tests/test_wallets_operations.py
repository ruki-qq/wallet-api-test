import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Operation
from .conftest import API_URL


async def create_wallet_via_api(
    client, wallet_uuid: uuid.UUID | None = None, balance: int | None = None
):
    payload: dict = {}
    if wallet_uuid is not None:
        payload["wallet_uuid"] = str(wallet_uuid)
    if balance is not None:
        payload["balance"] = balance
    return await client.post(API_URL, json=payload)


@pytest.mark.asyncio
async def test_get_wallet_not_found(client):
    wallet_id = uuid.uuid4()
    resp = await client.get(f"{API_URL}/{wallet_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_deposit_and_get_balance(client):
    r = await create_wallet_via_api(client, balance=0)
    assert r.status_code == 201
    wallet_id = r.json()["wallet_uuid"]

    resp = await client.post(
        f"{API_URL}/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 1000},
        headers={"Idempotency-Key": "k-dep-1"},
    )
    assert resp.status_code == 200
    assert resp.json()["balance"] == 1000

    resp = await client.get(f"{API_URL}/{wallet_id}")
    assert resp.status_code == 200
    assert resp.json()["balance"] == 1000


@pytest.mark.asyncio
async def test_withdraw_success(client):
    r = await create_wallet_via_api(client, balance=1000)
    assert r.status_code == 201
    wallet_id = r.json()["wallet_uuid"]

    resp = await client.post(
        f"{API_URL}/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": 400},
        headers={"Idempotency-Key": "k-wd-ok"},
    )
    assert resp.status_code == 200
    assert resp.json()["balance"] == 600


@pytest.mark.asyncio
async def test_withdraw_insufficient_funds(client, test_session: AsyncSession):
    r = await create_wallet_via_api(client, balance=500)
    assert r.status_code == 201
    wallet_id = r.json()["wallet_uuid"]

    resp = await client.post(
        f"{API_URL}/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": 600},
        headers={"Idempotency-Key": "k-wd-bad"},
    )
    assert resp.status_code == 409

    resp2 = await client.get(f"{API_URL}/{wallet_id}")
    assert resp2.status_code == 200
    assert resp2.json()["balance"] == 500

    wallet_uuid = uuid.UUID(wallet_id)
    ops_count = await test_session.scalar(
        select(func.count())
        .select_from(Operation)
        .where(
            Operation.wallet_id == wallet_uuid,
            Operation.idempotency_key == "k-wd-bad",
        )
    )
    assert ops_count == 0


@pytest.mark.asyncio
async def test_idempotency_deposit_only_applied_once(
    client, test_session: AsyncSession
):
    r = await create_wallet_via_api(client, balance=0)
    assert r.status_code == 201
    wallet_id = r.json()["wallet_uuid"]
    wallet_uuid = uuid.UUID(wallet_id)

    payload = {"operation_type": "DEPOSIT", "amount": 1000}
    headers = {"Idempotency-Key": "same-key"}

    r1 = await client.post(
        f"{API_URL}/{wallet_id}/operation", json=payload, headers=headers
    )
    r2 = await client.post(
        f"{API_URL}/{wallet_id}/operation", json=payload, headers=headers
    )

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["balance"] == 1000
    assert r2.json()["balance"] == 1000

    ops_count = await test_session.scalar(
        select(func.count())
        .select_from(Operation)
        .where(
            Operation.wallet_id == wallet_uuid,
            Operation.idempotency_key == "same-key",
        )
    )
    assert ops_count == 1


@pytest.mark.asyncio
async def test_idempotency_withdraw_only_applied_once(
    client, test_session: AsyncSession
):
    r = await create_wallet_via_api(client, balance=1000)
    assert r.status_code == 201
    wallet_id = r.json()["wallet_uuid"]
    wallet_uuid = uuid.UUID(wallet_id)

    payload = {"operation_type": "WITHDRAW", "amount": 400}
    headers = {"Idempotency-Key": "wd-key"}

    r1 = await client.post(
        f"{API_URL}/{wallet_id}/operation", json=payload, headers=headers
    )
    r2 = await client.post(
        f"{API_URL}/{wallet_id}/operation", json=payload, headers=headers
    )

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["balance"] == 600
    assert r2.json()["balance"] == 600

    ops_count = await test_session.scalar(
        select(func.count())
        .select_from(Operation)
        .where(
            Operation.wallet_id == wallet_uuid,
            Operation.idempotency_key == "wd-key",
        )
    )
    assert ops_count == 1
