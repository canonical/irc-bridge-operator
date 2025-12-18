#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
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
    unit_address = unit_address.removeprefix("http://")
    response = requests.get(f"http://{unit_address}:8090/health", timeout=30)
    assert response.status_code == 200
    assert response.text == "OK"
    haproxy_application = await model.deploy("haproxy", channel="2.8/edge")
    self_signed_application = await model.deploy("self-signed-certificates", channel="1/edge")
    await model.wait_for_idle(
        apps=[self_signed_application.name, haproxy_application.name],
        status="active",
        raise_on_error=True,
        timeout=300,
    )
    external_hostname = "haproxy.internal"
    await haproxy_application.set_config({"external-hostname": external_hostname})
    await model.wait_for_idle(
        apps=[self_signed_application.name, haproxy_application.name], status="active", timeout=300
    )
    await model.add_relation(
        f"{self_signed_application.name}:certificates", f"{haproxy_application.name}:certificates"
    )
    await model.wait_for_idle(
        apps=[self_signed_application.name, haproxy_application.name], status="active", timeout=300
    )
    await model.add_relation(f"{app_integrated.name}:ingress", haproxy_application.name)
    await model.wait_for_idle(
        apps=[app_integrated.name, haproxy_application.name], status="active", timeout=300
    )

    unit_address = await tests.integration.helpers.get_unit_address(haproxy_application)
    unit_address = unit_address.removeprefix("http://")
    session = Session()
    session.mount("https://", DNSResolverHTTPSAdapter(external_hostname, str(unit_address)))
    response = session.get(
        f"https://{unit_address}/{model.name}-{app_integrated.name}/health",
        headers={"Host": external_hostname},
        verify=False,  # nosec - calling charm ingress URL
        timeout=30,
    )

    assert response.status_code == 200
    assert response.text == "OK"


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_ingress_media_integration(app_integrated: Application, model: Model):
    """
    arrange: assert IRC Media /health is ok, deploy haproxy and relate it to
        self-signed-certificates. Relate haproxy with IRC bridge.
    act: request /health via haproxy.
    assert: request is successful.
    """
    unit_address = await tests.integration.helpers.get_unit_address(app_integrated)
    unit_address = unit_address.removeprefix("http://")
    response = requests.get(f"http://{unit_address}:11111/health", timeout=30)
    assert response.status_code == 200
    assert response.headers.get("Content-Type") == "application/json; charset=utf-8"
    assert response.json() == {"ok": True}
    haproxy_application = await model.deploy(
        "haproxy", application_name="haproxy-media", channel="2.8/edge"
    )
    self_signed_application = await model.deploy(
        "self-signed-certificates",
        application_name="self-signed-certificates-media",
        channel="1/edge",
    )
    external_hostname = "haproxy-media.internal"
    await model.wait_for_idle(
        apps=[self_signed_application.name, haproxy_application.name],
        status="active",
        raise_on_error=True,
        timeout=300,
    )
    await haproxy_application.set_config({"external-hostname": external_hostname})
    await model.wait_for_idle(
        apps=[self_signed_application.name, haproxy_application.name], status="active", timeout=300
    )
    await model.add_relation(self_signed_application.name, haproxy_application.name)
    await model.wait_for_idle(
        apps=[self_signed_application.name, haproxy_application.name], status="active", timeout=300
    )
    await model.add_relation(f"{app_integrated.name}:ingress-media", haproxy_application.name)
    await model.wait_for_idle(
        apps=[app_integrated.name, haproxy_application.name], status="active", timeout=300
    )

    unit_address = await tests.integration.helpers.get_unit_address(haproxy_application)
    unit_address = unit_address.removeprefix("http://")
    session = Session()
    session.mount("https://", DNSResolverHTTPSAdapter(external_hostname, str(unit_address)))
    response = session.get(
        f"https://{unit_address}/{model.name}-{app_integrated.name}/health",
        headers={"Host": external_hostname},
        verify=False,  # nosec - calling charm ingress URL
        timeout=30,
    )

    assert response.status_code == 200
    assert response.headers.get("Content-Type") == "application/json; charset=utf-8"
    assert response.json() == {"ok": True}
