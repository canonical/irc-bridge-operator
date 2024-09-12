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


class ReloadDataEvent(ops.charm.EventBase):
    """Event representing a reload-data event."""


class AnyCharm(AnyCharmBase):
    """Execute a simple charm to test the relation."""

    def __init__(self, *args, **kwargs):
        """Init function for the class.

        Args:
            args: Variable list of positional arguments passed to the parent constructor.
            kwargs: Variable list of positional keyword arguments passed to the parent constructor.
        """
        super().__init__(*args, **kwargs)
        self.on.define_event("reload_data", ReloadDataEvent)
        self.matrix = MatrixAuthProvides(self)
        self.framework.observe(self.on.reload_data, self._on_reload_data)

    def _on_reload_data(self, _: ReloadDataEvent) -> None:
        """Handle reload-data events."""
        relation = self.model.get_relation(self.matrix.relation_name)
        self.matrix.update_relation_data(relation, self._test_auth_data())

    def _test_auth_data(self) -> MatrixAuthProviderData:
        """Create test auth data.

        Returns:
            test auth data
        """
        matrix_requirer_data = MatrixAuthProviderData(
            homeserver="https://matrix.org", shared_secret=str(uuid.uuid4())
        )
        return matrix_requirer_data
