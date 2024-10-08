# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

# pylint: disable=import-error,consider-using-with,no-member,too-few-public-methods

"""This code should be loaded into any-charm which is used for integration tests."""

import logging
from secrets import token_hex

from any_charm_base import AnyCharmBase
from matrix_auth import MatrixAuthProviderData, MatrixAuthProvides

logger = logging.getLogger(__name__)


class AnyCharm(AnyCharmBase):
    """Execute a simple charm to test the relation."""

    def __init__(self, *args, **kwargs):
        """Initialize the charm and observe the relation events.

        Args:
            args: Arguments to pass to the parent class.
            kwargs: Keyword arguments to pass to the parent class
        """
        super().__init__(*args, **kwargs)

        self.plugin_auth = MatrixAuthProvides(self, relation_name="provide-irc-bridge")
        self.framework.observe(
            self.on.provide_irc_bridge_relation_created, self._on_relation_created
        )
        self.framework.observe(
            self.plugin_auth.on.matrix_auth_request_received, self._on_matrix_auth_request_received
        )
        # self.framework.observe(
        # self.on.provide_irc_bridge_relation_changed, self._on_relation_changed)

    def _on_relation_created(self, _):
        """Create the relation and set the relation data."""
        relation = self.model.get_relation("provide-irc-bridge")
        secret = token_hex(16)
        if relation is not None:
            logger.info("Setting relation data")
            matrix_auth_data = MatrixAuthProviderData(
                homeserver="https://example.com", shared_secret=secret
            )
            matrix_auth_data.set_shared_secret_id(model=self.model, relation=relation)
            self.plugin_auth.update_relation_data(relation, matrix_auth_data)

    def _on_matrix_auth_request_received(self, _):
        """Get the relation data and log it."""
        relation = self.model.get_relation("provide-irc-bridge")
        if relation is not None:
            logger.info("Getting relation data")
            remote_data = self.plugin_auth.get_remote_relation_data()
            logger.info("Remote data: %s", remote_data)

    def _on_relation_changed(self, _):
        """Get the relation data and log it."""
        relation = self.model.get_relation("provide-irc-bridge")
        logger.info("Relation: %s", relation)
        relation = self.model.get_relation("provide-irc-bridge")
        logger.info("Relation: %s", relation)
        if relation is not None:
            try:
                logger.info("Getting relation data")
                matrix_auth_data = MatrixAuthProviderData.from_relation(
                    model=self.model, relation=relation
                )
            except ValueError as e:
                logger.error("Failed to get relation data: %s", e)
                logger.info("Setting relation data")
                secret = token_hex(16)
                matrix_auth_data = MatrixAuthProviderData(
                    homeserver="https://example.com", shared_secret=secret
                )
            matrix_auth_data.set_shared_secret_id(model=self.model, relation=relation)
            self.plugin_auth.update_relation_data(relation, matrix_auth_data)
            remote_data = self.plugin_auth.get_remote_relation_data()
            logger.info("Remote data: %s", remote_data)
