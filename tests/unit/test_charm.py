# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit tests for the IRC Bridge charm."""

# Ignore similar lines with database_observer.
# Ignore access to _get_media_external_url.
# pylint: disable=R0801, protected-access

import json
from unittest.mock import MagicMock

import ops
from ops.testing import Harness
from pytest import MonkeyPatch

from charm import IDENT_PORT, IRCCharm


def test_irc_bridge_ident(monkeypatch: MonkeyPatch) -> None:
    """
    arrange: start the charm with all integrations and commands mocked.
    act: change ident_enabled config to true.
    assert: The port is exposed and the charm is active.
    """
    harness = Harness(IRCCharm)
    harness.add_network("10.0.0.10")
    harness.add_relation("matrix-auth", "synapse", app_data={"homeserver": "123"})
    harness.add_relation(
        "database",
        "database-provider",
        app_data={
            "database": "ircbridge",
            "endpoints": "postgresql-k8s-primary.local:5432",
            "password": "123",
            "username": "user1",
        },
    )
    harness.begin()
    monkeypatch.setattr(harness.charm, "_irc", MagicMock())
    monkeypatch.setattr(harness.charm, "_matrix", MagicMock())
    harness.set_leader(True)
    harness.update_config({"bot_nickname": "testbot", "bridge_admins": "admin:example.com"})
    assert isinstance(harness.model.unit.status, ops.ActiveStatus)
    # Empty since ident is disabled by default
    assert harness.model.unit.opened_ports() == set()

    harness.update_config({"ident_enabled": True})

    assert isinstance(harness.model.unit.status, ops.ActiveStatus)
    assert ops.Port(protocol="tcp", port=IDENT_PORT) in harness.model.unit.opened_ports()


def test_ingress_media_removed(monkeypatch: MonkeyPatch) -> None:
    """
    arrange: start the charm with all integrations and commands mocked.
    act: remove ingress-media relation.
    assert: The media url points to the unit IP.
    """
    harness = Harness(IRCCharm)
    harness.set_model_name("testmodel")
    harness.add_network("10.0.0.10")
    media_url = "https://media/"
    ingress_id = harness.add_relation(
        "ingress-media", "haproxy", app_data={"ingress": json.dumps({"url": media_url})}
    )
    harness.add_relation("matrix-auth", "synapse", app_data={"homeserver": "123"})
    harness.add_relation(
        "database",
        "database-provider",
        app_data={
            "database": "ircbridge",
            "endpoints": "postgresql-k8s-primary.local:5432",
            "password": "123",
            "username": "user1",
        },
    )
    harness.begin()
    mock_irc = MagicMock()
    monkeypatch.setattr(harness.charm, "_irc", mock_irc)
    monkeypatch.setattr(harness.charm, "_matrix", MagicMock())
    harness.set_leader(True)
    harness.update_config({"bot_nickname": "testbot", "bridge_admins": "admin:example.com"})
    assert isinstance(harness.model.unit.status, ops.ActiveStatus)
    assert harness.charm._get_media_external_url() == media_url

    harness.remove_relation(ingress_id)

    assert harness.charm._get_media_external_url() == "http://10.0.0.10:11111"
    # when running update_config
    # when remove ingress-media relation
    assert mock_irc.reconcile.call_count == 2
