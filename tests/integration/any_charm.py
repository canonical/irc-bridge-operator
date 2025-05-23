# Copyright 2025 Canonical Ltd.
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

        self.plugin_auth = MatrixAuthProvides(self, relation_name="provide-matrix-auth")
        self.framework.observe(
            self.on.provide_matrix_auth_relation_created, self._on_relation_created
        )
        self.framework.observe(
            self.plugin_auth.on.matrix_auth_request_received, self._on_matrix_auth_request_received
        )

    def _on_relation_created(self, _):
        """Create the relation and set the relation data."""
        relation = self.model.get_relation("provide-matrix-auth")
        secret = token_hex(16)
        if relation is not None:
            logger.info("Setting relation data")
            matrix_auth_data = MatrixAuthProviderData(
                homeserver="https://example.com", shared_secret=secret
            )
            self.plugin_auth.update_relation_data(relation, matrix_auth_data)

    def _on_matrix_auth_request_received(self, _):
        """Get the relation data and log it."""
        relation = self.model.get_relation("provide-matrix-auth")
        if relation is not None:
            logger.info("Getting relation data")
            remote_data = self.plugin_auth.get_remote_relation_data()
            logger.info("Remote data: %s", remote_data)
