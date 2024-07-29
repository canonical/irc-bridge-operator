#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm for irc-bridge."""

import logging
import typing

import ops

from irc import IRCService
from database import DatabaseService
from constants import DATABASE_RELATION_NAME, MATRIX_RELATION_NAME
from charm_types import CharmConfig
from pydantic import ValidationError

logger = logging.getLogger(__name__)



class IRCCharm(ops.CharmBase):
    """Charm the irc bridge service."""

    def __init__(self, *args: typing.Any):
        """Construct.

        Args:
            args: Arguments passed to the CharmBase parent constructor.
        """
        super().__init__(*args)
        self._irc = IRCService()
        self._database = DatabaseObserver(self, DATABASE_RELATION_NAME)
        self._matrix = MatrixObserver(self, MATRIX_RELATION_NAME)
        self.framework.observe(
            self._database.database.on.database_created, self._on_database_created
        )
        self.framework.observe(
            self.on[DATABASE_RELATION_NAME].relation_broken,
            self._on_database_relation_broken
        )
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.install, self._on_install)
        self.framework.observe(self.on.start, self._on_start)
        self.framework.observe(self.on.stop, self._on_stop)

    def _on_database_created(self, _: ops.DatabaseCreatedEvent) -> None:
        """Handle database created."""
        self.reconcile()

    def _on_database_relation_broken(self, _: ops.RelationBrokenEvent) -> None:
        """Handle database relation broken."""
        self.reconcile()

    def _on_config_changed(self, _: ops.ChangedEvent) -> None:
        """Handle config changed."""
        self.reconcile()

    def _on_install(self, _: ops.InstallEvent) -> None:
        """Handle install."""
        self.reconcile()

    def _on_start(self, _: ops.StartEvent) -> None:
        """Handle start."""
        self.reconcile()

    def _on_stop(self, _: ops.StopEvent) -> None:
        """Handle stop."""
        self._irc.stop()

    def _charm_reconcile(self) -> CharmConfig:
        """Reconcile the charm.

        Returns:
            CharmConfig: The reconciled charm configuration.
        """
        return CharmConfig(
                ident_enabled=self.model.config["ident_enabled"],
                bot_nickname=self.model.config["bot_nickname"],
                bridge_admins=self.model.config["bridge_admins"],
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
        try: 
            db = self._database.reconcile()
        except ValidationError as e:
            self.unit.status = ops.BlockedStatus("Database relation not ready")
            return
        matrix = self._matrix.reconcile()
        config = self._charm_reconcile()
        self._irc.reconcile(db, matrix, config)


if __name__ == "__main__":  # pragma: nocover
    ops.main.main(IRCCharm)
