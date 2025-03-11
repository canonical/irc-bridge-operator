# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provide the DatabaseObserver class to handle database relation and state."""

import typing

from charms.data_platform_libs.v0.data_interfaces import (
    DatabaseCreatedEvent,
    DatabaseEndpointsChangedEvent,
    DatabaseRequires,
)
from ops.framework import Object

from charm_types import DatasourcePostgreSQL, ReconcilingCharm
from constants import DATABASE_NAME


class DatabaseObserver(Object):
    """The Database relation observer.

    Attributes:
        relation_name: The name of the relation to observe.
        database: The database relation interface.
    """

    def __init__(self, charm: ReconcilingCharm, relation_name: str):
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
        self._charm.reconcile()

    def _on_endpoints_changed(self, _: DatabaseEndpointsChangedEvent) -> None:
        """Handle endpoints changed."""
        self._charm.reconcile()

    def get_db(self) -> typing.Optional[DatasourcePostgreSQL]:
        """Return a postgresql datasource model.

        Returns:
            DatasourcePostgreSQL: The datasource model.
        """
        relation_data = list(
            self.database.fetch_relation_data(
                fields=["uris", "endpoints", "username", "password", "database"]
            ).values()
        )
        if not relation_data:
            return None

        # There can be only one database integrated at a time
        # with the same interface name. See: metadata.yaml
        data = relation_data[0]

        # Check that the relation data is well formed according to the following json_schema:
        # https://github.com/canonical/charm-relation-interfaces/blob/main/interfaces/postgresql_client/v0/schemas/provider.json
        if not all(data.get(key) for key in ("endpoints", "username", "password")):
            return None

        database_name = data.get("database", self.database.database)
        endpoint = data["endpoints"].split(",")[0]
        user = data["username"]
        password = data["password"]
        host, port = endpoint.split(":")

        if "uris" in data:
            uri = data["uris"].split(",")[0]
        else:
            uri = f"postgres://{user}:{password}@{endpoint}/{database_name}"

        return DatasourcePostgreSQL(
            user=user,
            password=password,
            host=host,
            port=port,
            db=database_name,
            uri=uri,
        )
