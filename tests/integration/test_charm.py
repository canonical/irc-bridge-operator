#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests."""

import logging

import ops
import pytest
from pytest_operator.plugin import OpsTest

import tests.integration.helpers

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_lifecycle_before_relations(app: ops.model.Application, ops_test: OpsTest):
    """
    arrange: build and deploy the charm.
    act: nothing.
    assert: that the charm ends up in blocked state because of missing relations.
    """
    # Set config so the charm can start
    config = {"bridge_admins": "admin:example.com", "bot_nickname": "bot"}
    await tests.integration.helpers.set_config(ops_test, app.name, config)
    # Application actually does have units
    unit = app.units[0]  # type: ignore

    # Mypy has difficulty with ActiveStatus
    assert unit.workload_status == ops.model.WaitingStatus.name  # type: ignore


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_lifecycle_after_relations(app: ops.model.Application, ops_test: OpsTest):
    """
    arrange: build and deploy the charm.
    act: relate to a db and a matrix homeserver.
    assert: that the charm ends up in active state.
    """
    # Set config so the charm can start
    config = {"bridge_admins": "admin:example.com", "bot_nickname": "bot"}
    await tests.integration.helpers.set_config(ops_test, app.name, config)
    # await ops_test.model.wait_for_idle(apps=[app.name], status="waiting", timeout=60 * 60)
    # Application actually does have units
    unit = app.units[0]  # type: ignore

    # Deploy postgresql charm
    assert ops_test.model
    await ops_test.model.deploy("postgresql", channel="14/stable")

    # Deploy any charm that provides the matrix homeserver interface
    await tests.integration.helpers.generate_anycharm_relation(
        app, ops_test, "matrix-homeserver", None
    )

    # Add relations
    await ops_test.model.wait_for_idle(
        apps=["postgresql", "matrix-homeserver"], status="active", timeout=60 * 60
    )
    await ops_test.model.add_relation(app.name, "postgresql")

    await ops_test.model.wait_for_idle(
        apps=[f"{app.name}", "postgresql", "matrix-homeserver"], status="active", timeout=60 * 60
    )

    # Mypy has difficulty with ActiveStatus
    assert unit.workload_status == ops.model.BlockedStatus.name  # type: ignore
    # Assert part of the message
    assert ops.BlockedStatus("Database relation not found") == app.status
