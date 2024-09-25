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
    assert unit.workload_status == ops.model.BlockedStatus.name  # type: ignore
    # Assert part of the message
    assert "Missing relation" in unit.workload_status_message
