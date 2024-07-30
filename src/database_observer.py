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
        self.db_data = None

    def _on_database_created(self, event: DatabaseCreatedEvent) -> None:
        """Handle database created.

        Args:
            event: The database created event.
        """
        primary_endpoint = event.endpoints.split(",")[0].split(":")
        self.db_data = DatasourcePostgreSQL(
            user=event.username,
            password=event.password,
            host=primary_endpoint[0],
            port=primary_endpoint[1],
            db=event.database,
        )

    @property
    def db_connection(self) -> typing.Optional[DatasourcePostgreSQL]:
        """Reconcile the database relation."""
        return self.db_data
