#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests."""

import logging
from urllib.parse import urlparse

import ops
import pytest
import yaml
from juju.application import Application
from pytest_operator.plugin import OpsTest

import tests.integration.helpers
from constants import IRC_BRIDGE_CONFIG_FILE_PATH

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


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_config(app_integrated: Application, matrix_homeserver: str):
    """
    arrange: charm has all expected relations.
    act: get configuration file content.
    assert: irc bridge is properly configured.
    """
    unit = app_integrated.units[0]
    assert unit.workload_status == ops.model.ActiveStatus.name

    action = await unit.run(f"cat {IRC_BRIDGE_CONFIG_FILE_PATH}", timeout=60)
    await action.wait()

    code = action.results.get("return-code")
    stdout = action.results.get("stdout")
    assert code == 0
    config = yaml.safe_load(stdout)
    assert config["homeserver"]["url"] == matrix_homeserver
    assert config["homeserver"]["domain"] == urlparse(matrix_homeserver).netloc
