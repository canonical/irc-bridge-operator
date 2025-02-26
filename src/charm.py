#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm for irc-bridge."""

import logging
import socket
import typing

import ops
from charms.traefik_k8s.v2.ingress import IngressPerAppRequirer
from pydantic import ValidationError

from charm_types import CharmConfig
from constants import DATABASE_RELATION_NAME, MATRIX_RELATION_NAME
from database_observer import DatabaseObserver
from irc import IRCBridgeService
from matrix_observer import MatrixObserver

logger = logging.getLogger(__name__)

IRC_BIND_PORT = 8090
IRC_MEDIA_BIND_PORT = 11111

IDENT_PORT = 113


class IRCCharm(ops.CharmBase):
    """Charm the irc bridge service."""

    def __init__(self, *args: typing.Any):
        """Construct.

        Args:
            args: Arguments passed to the CharmBase parent constructor.
        """
        super().__init__(*args)
        self._irc = IRCBridgeService()
        self._database = DatabaseObserver(self, DATABASE_RELATION_NAME)
        self._matrix = MatrixObserver(self, MATRIX_RELATION_NAME)
        # 8090 is used for Synapse -> IRC Bridge communication
        self.ingress = IngressPerAppRequirer(
            self, port=IRC_BIND_PORT, strip_prefix=True, relation_name="ingress"
        )
        self.ingress_media = IngressPerAppRequirer(
            self, port=IRC_MEDIA_BIND_PORT, strip_prefix=True, relation_name="ingress-media"
        )
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.install, self._on_install)
        self.framework.observe(self.on.upgrade_charm, self._on_upgrade_charm)
        self.framework.observe(self.on.start, self._on_start)
        self.framework.observe(self.on.stop, self._on_stop)

    def _on_config_changed(self, _: ops.ConfigChangedEvent) -> None:
        """Handle config changed."""
        self.reconcile()

    def _on_install(self, _: ops.InstallEvent) -> None:
        """Handle install."""
        self.reconcile()

    def _on_upgrade_charm(self, _: ops.UpgradeCharmEvent) -> None:
        """Handle upgrade charm."""
        self.reconcile()

    def _on_start(self, _: ops.StartEvent) -> None:
        """Handle start."""
        self.reconcile()

    def _on_stop(self, _: ops.StopEvent) -> None:
        """Handle stop."""
        self.unit.status = ops.MaintenanceStatus("Stopping charm")
        self._irc.stop()

    def _get_charm_config(self) -> CharmConfig:
        """Reconcile the charm.

        Returns:
            CharmConfig: The reconciled charm configuration.
        """
        return CharmConfig(
            ident_enabled=self.model.config.get("ident_enabled", None),
            bot_nickname=self.model.config.get("bot_nickname", None),
            bridge_admins=self.model.config.get("bridge_admins", None),
        )

    def _get_external_url(self) -> str:
        """Return URL to access IRC Bridge from Matrix."""
        # Default: FQDN
        external_url = f"http://{socket.getfqdn()}:{IRC_BIND_PORT}"
        # If can connect to juju-info, get unit IP
        if binding := self.model.get_binding("juju-info"):
            unit_ip = str(binding.network.bind_address)
            external_url = f"http://{unit_ip}:{IRC_BIND_PORT}"
        # If ingress is set, get ingress url
        if self.ingress.url:
            external_url = self.ingress.url
        return external_url

    def _get_media_external_url(self) -> str:
        """Return URL to access media."""
        # Default: FQDN
        external_url = f"http://{socket.getfqdn()}:{IRC_MEDIA_BIND_PORT}"
        # If can connect to juju-info, get unit IP
        if binding := self.model.get_binding("juju-info"):
            unit_ip = str(binding.network.bind_address)
            external_url = f"http://{unit_ip}:{IRC_MEDIA_BIND_PORT}"
        # If ingress media is set, get ingress url
        if self.ingress_media:
            external_url = self.ingress_media.url
        return external_url

    def reconcile(self) -> None:
        """Reconcile the charm.

        This is a more simple approach to reconciliation,
        adapted from Charming Complexity sans state and observers.

        Being a simple charm, we don't need to do much here.

        Ensure we have a database relation,
        ensure we have a relation to matrix,
        populate database connection string and matrix homeserver URL
        in the config template and (re)start the service.
        """
        ops.MaintenanceStatus("Reconciling charm")
        try:
            db = self._database.get_db()
            if db is None:
                self.unit.status = ops.BlockedStatus("Database relation not found")
                return
        except ValidationError:
            self.unit.status = ops.MaintenanceStatus(
                "Database configuration missing username, password or URI"
            )
            return
        try:
            matrix = self._matrix.get_matrix()
            if matrix is None:
                self.unit.status = ops.BlockedStatus("Matrix relation not found")
                return
        except ValidationError:
            self.unit.status = ops.MaintenanceStatus("Matrix configuration not correct")
            return
        try:
            config = self._get_charm_config()
        except ValidationError as e:
            self.unit.status = ops.MaintenanceStatus(f"Invalid configuration: {e}")
            logger.exception("Invalid configuration: {%s}", e)
            return
        if config.ident_enabled:
            logger.info("Ident is enabled, exposing port %d", IDENT_PORT)
            self.unit.set_ports(IDENT_PORT)
        self._irc.reconcile(
            db, matrix, config, self._get_external_url(), self._get_media_external_url()
        )
        self._matrix.set_irc_registration(self._irc.get_registration())
        self.unit.status = ops.ActiveStatus()


if __name__ == "__main__":  # pragma: nocover
    ops.main(IRCCharm)
