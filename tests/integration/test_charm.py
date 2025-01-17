#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests."""

import logging

import ops
import pytest
from juju.application import Application
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
async def test_lifecycle_after_relations(app_integrated: Application):
    """
    arrange: build and deploy the charm.
    act: relate to a db and a matrix homeserver.
    assert: that the charm ends up in active state.
    """
    unit = app_integrated.units[0]
    assert unit.workload_status == ops.model.ActiveStatus.name
