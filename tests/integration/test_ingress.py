#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Ingress integration tests."""

import logging

import pytest
import requests
from juju.application import Application
from juju.model import Model
from requests import Session

import tests.integration.helpers
from tests.integration.helpers import DNSResolverHTTPSAdapter

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_ingress_integration(app_integrated: Application, model: Model):
    """
    arrange: assert IRC /health is ok, deploy haproxy and relate it to
        self-signed-certificates. Relate haproxy with IRC bridge.
    act: request /health via haproxy.
    assert: request is successful.
    """
    unit_address = await tests.integration.helpers.get_unit_address(app_integrated)
    response = requests.get(f"http://{unit_address}:8090/health", timeout=30)
    assert response.status_code == 200
    assert response.text == "OK"
    haproxy_application = await model.deploy("haproxy", channel="2.8/edge")
    self_signed_application = await model.deploy("self-signed-certificates", channel="edge")
    external_hostname = "haproxy.internal"
    await haproxy_application.set_config({"external-hostname": external_hostname})
    await model.wait_for_idle(
        apps=[self_signed_application.name, haproxy_application.name], status="active"
    )
    await model.add_relation(self_signed_application.name, haproxy_application.name)
    await model.wait_for_idle(
        apps=[self_signed_application.name, haproxy_application.name], status="active"
    )
    await model.add_relation(app_integrated.name, haproxy_application.name)
    await model.wait_for_idle(
        apps=[app_integrated.name, haproxy_application.name], status="active"
    )

    unit_address = await tests.integration.helpers.get_unit_address(haproxy_application)
    session = Session()
    session.mount("https://", DNSResolverHTTPSAdapter(external_hostname, str(unit_address)))
    response = session.get(
        f"https://{unit_address}/health",
        headers={"Host": external_hostname},
        verify=False,  # nosec - calling charm ingress URL
        timeout=30,
    )

    assert response.status_code == 200
    assert response.text == "OK"
