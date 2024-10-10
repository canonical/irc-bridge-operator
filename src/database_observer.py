# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provide the DatabaseObserver class to handle database relation and state."""

import typing

from charms.data_platform_libs.v0.data_interfaces import (
    DatabaseCreatedEvent,
    DatabaseEndpointsChangedEvent,
    DatabaseRequires,
)
from ops.charm import CharmBase
from ops.framework import Object

from charm_types import DatasourcePostgreSQL
from constants import DATABASE_NAME


class DatabaseObserver(Object):
    """The Database relation observer.

    Attributes:
        relation_name: The name of the relation to observe.
        database: The database relation interface.
    """

    def __init__(self, charm: CharmBase, relation_name: str):
        """Initialize the oserver and register event handlers.

        Args:
            charm: The parent charm to attach the observer to.
            relation_name: The name of the relation to observe.
        """
        super().__init__(charm, "database-observer")
        self._charm = charm
        self.relation_name = relation_name
        self.database = DatabaseRequires(
            self._charm,
            relation_name=self.relation_name,
            database_name=DATABASE_NAME,
        )
        self.framework.observe(self.database.on.database_created, self._on_database_created)
        self.framework.observe(self.database.on.endpoints_changed, self._on_endpoints_changed)

    def _on_database_created(self, _: DatabaseCreatedEvent) -> None:
        """Handle database created."""
        self._charm.reconcile()  # type: ignore

    def _on_endpoints_changed(self, _: DatabaseEndpointsChangedEvent) -> None:
        """Handle endpoints changed."""
        self._charm.reconcile()  # type: ignore

    def get_db(self) -> typing.Optional[DatasourcePostgreSQL]:
        """Return a postgresql datasource model.

        Returns:
            DatasourcePostgreSQL: The datasource model.
        """
        # not using get_relation due this issue
        # https://github.com/canonical/operator/issues/1153
        if not self.model.relations.get(self.database.relation_name):
            return None

        relation = self.model.get_relation(self.relation_name)
        return DatasourcePostgreSQL.from_relation(self.model, relation)
