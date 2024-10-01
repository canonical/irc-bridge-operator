# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

# pylint: disable=import-error,consider-using-with,no-member,too-few-public-methods

"""This code should be loaded into any-charm which is used for integration tests."""

import logging
import uuid

import ops
from any_charm_base import AnyCharmBase
from matrix_auth import MatrixAuthProviderData, MatrixAuthProvides

logger = logging.getLogger(__name__)

class AnyCharm(AnyCharmBase):
    """Execute a simple charm to test the relation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.plugin_auth = MatrixAuthProvides(self, relation_name="provide-irc-bridge")
        self.framework.observe(self.on.provide_irc_bridge_relation_created, self._on_relation_created)
        self.framework.observe(self.plugin_auth.on.matrix_auth_request_received, self._on_matrix_auth_request_received)
        #self.framework.observe(self.on.provide_irc_bridge_relation_changed, self._on_relation_changed)

    def _on_relation_created(self, _):
        relation = self.model.get_relation("provide-irc-bridge")
        if relation is not None:
            logger.info(f"Setting relation data")
            matrix_auth_data = MatrixAuthProviderData(
                homeserver="https://example.com",
                shared_secret="foobar"
            )
            matrix_auth_data.set_shared_secret_id(model=self.model, relation=relation)
            self.plugin_auth.update_relation_data(relation, matrix_auth_data)

    def _on_matrix_auth_request_received(self, _):
        relation = self.model.get_relation("provide-irc-bridge")
        if relation is not None:
            logger.info(f"Getting relation data")
            remote_data = self.plugin_auth.get_remote_relation_data()
            logger.info(f"Remote data: {remote_data}")

    def _on_relation_changed(self, _):
        relation = self.model.get_relation("provide-irc-bridge")
        logger.info(f"Relation: {relation}")
        return
        relation = self.model.get_relation("provide-irc-bridge")
        logger.info(f"Relation: {relation}")
        if relation is not None:
            try:
                logger.info(f"Getting relation data")
                matrix_auth_data = MatrixAuthProviderData.from_relation(model=self.model, relation=relation)
            except Exception as e:
                logger.error(f"Failed to get relation data: {e}")
                logger.info(f"Setting relation data")
                matrix_auth_data = MatrixAuthProviderData(
                    homeserver="https://example.com",
                    shared_secret="foobar"
                )
            matrix_auth_data.set_shared_secret_id(model=self.model, relation=relation)
            self.plugin_auth.update_relation_data(relation, matrix_auth_data)
            remote_data = self.plugin_auth.get_remote_relation_data()
            logger.info(f"Remote data: {remote_data}")
