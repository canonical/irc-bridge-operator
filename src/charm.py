#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm for irc-bridge."""

import logging
import typing

import ops
from pydantic import ValidationError

from charm_types import CharmConfig
from constants import DATABASE_RELATION_NAME, MATRIX_RELATION_NAME
from database_observer import DatabaseObserver
from irc import IRCBridgeService
from matrix_observer import MatrixObserver

logger = logging.getLogger(__name__)


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

    def _charm_config(self) -> CharmConfig:
        """Reconcile the charm.

        Returns:
            CharmConfig: The reconciled charm configuration.
        """
        return CharmConfig(
            ident_enabled=self.model.config.get("ident_enabled", None),
            bot_nickname=self.model.config.get("bot_nickname", None),
            bridge_admins=self.model.config.get("bridge_admins", None),
        )

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
            logger.info("DB Reconciling charm")
            db = self._database.get_db()
            if db is None:
                self.unit.status = ops.BlockedStatus("Database relation not found")
                return
        except ValidationError:
            self.unit.status = ops.MaintenanceStatus(
                "Database configuration missing username, password or URI"
            )
            return
        logger.info("Matrix Reconciling charm")
        matrix = self._matrix.reconcile()
        try:
            logger.info("Config Reconciling charm")
            config = self._charm_config
        except ValidationError as e:
            self.unit.status = ops.MaintenanceStatus(f"Invalid configuration: {e}")
            logger.exception("Invalid configuration: {%s}", e)
            return
        logger.info("IRC Reconciling charm")
        self._irc.reconcile(db, matrix, config)
        self.unit.status = ops.ActiveStatus()


if __name__ == "__main__":  # pragma: nocover
    ops.main.main(IRCCharm)
