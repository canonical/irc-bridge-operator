#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests."""

import logging

import ops
import pytest
from juju.application import Application
from juju.model import Model
from pytest_operator.plugin import OpsTest

import tests.integration.helpers

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_lifecycle_before_relations(app: Application, ops_test: OpsTest):
    """
    arrange: build and deploy the charm.
    act: nothing.
    assert: that the charm ends up in blocked state because of missing relations.
    """
    # Set config so the charm can start
    config = {"bridge_admins": "admin:example.com", "bot_nickname": "bot"}
    await tests.integration.helpers.set_config(ops_test, app.name, config)
    unit = app.units[0]

    assert unit.workload_status == ops.model.WaitingStatus.name


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_lifecycle_after_relations(app: Application, ops_test: OpsTest, model: Model):
    """
    arrange: build and deploy the charm.
    act: relate to a db and a matrix homeserver.
    assert: that the charm ends up in active state.
    """
    # Set config so the charm can start
    config = {"bridge_admins": "admin:example.com", "bot_nickname": "bot"}
    app.set_config(config)
    unit = app.units[0]

    # Deploy postgresql charm and relate with the charm
    await model.deploy("postgresql", channel="14/stable")
    await model.wait_for_idle(apps=["postgresql"], status="active", timeout=60 * 60)
    await model.add_relation(app.name, "postgresql")

    # Deploy any charm that provides the matrix homeserver interface
    # and relate with the charm
    await tests.integration.helpers.generate_anycharm_relation(
        app, ops_test, "matrix-homeserver", None
    )
    await model.wait_for_idle(
        apps=[f"{app.name}", "postgresql", "matrix-homeserver"], status="active", timeout=60 * 60
    )

    assert unit.workload_status == ops.model.ActiveStatus.name
