#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm for irc-bridge."""

import logging
import typing

import ops

from irc import IRCService
from database import DatabaseService
from constants import DATABASE_RELATION_NAME

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
        self.framework.observe(
            self._database.database.on.database_created, self.reconcile
        )
        self.framework.observe(
            self.on[DATABASE_RELATION_NAME].relation_broken,
            self.reconcile
        )
        self.framework.observe(self.on.config_changed, self.reconcile)
        self.framework.observe(self.on.install, self.reconcile)
        self.framework.observe(self.on.start, self.reconcile)
        self.framework.observe(self.on.stop, self._on_stop)

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
        self._irc.reconcile()

    def _on_stop(self, _: ops.StopEvent) -> None:
        """Handle stop."""
        self._irc.stop()


if __name__ == "__main__":  # pragma: nocover
    ops.main.main(IRCCharm)
