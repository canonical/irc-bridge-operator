# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provide the DatabaseObserver class to handle database relation and state."""

import typing

from charms.data_platform_libs.v0.data_interfaces import DatabaseCreatedEvent, DatabaseRequires
from ops.charm import CharmBase
from ops.framework import Object

from charm_types import DatasourcePostgreSQL
from constants import DATABASE_NAME


class DatabaseObserver(Object):
    """The Database relation observer.

    Attrs:
        db_connection: The database connection.
        relation_name: The name of the relation to observe.
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

    def _on_database_created(self, _: DatabaseCreatedEvent) -> None:
        """Handle database created.

        Args:
            event: The database created event.
        """
        self._charm.reconcile()

    @property
    def uri(self) -> typing.Optional[DatasourcePostgreSQL]:
        """Reconcile the database relation."""
        # not using get_relation due this issue
        # https://github.com/canonical/operator/issues/1153
        if not self.model.relations.get(self.database.relation_name):
            return None

        relation_id = self.database.relations[0].id
        relation_data = self.database.fetch_relation_data()[relation_id]

        endpoint = relation_data.get("endpoints", ":")

        return DatasourcePostgreSQL(
            user=relation_data.get("username", ""),
            password=relation_data.get("password", ""),
            host=endpoint.split(":")[0],
            port=endpoint.split(":")[1],
            db=DATABASE_NAME,
        )
