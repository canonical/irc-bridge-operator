# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provide the DatabaseObserver class to handle database relation and state."""

import typing

from charms.data_platform_libs.v0.data_interfaces import DatabaseRequires
from ops.charm import CharmBase
from ops.framework import Object

from constants import DATABASE_NAME
from charm_types import DatasourcePostgreSQL

class DatabaseObserver(Object):
    """The Database relation observer."""

    def __init__(self, charm: CharmBase, relation_name: str):
        """Initialize the oserver and register event handlers.

        Args:
            charm: The parent charm to attach the observer to.
        """
        super().__init__(charm, "database-observer")
        self._charm = charm
        self.relation_name = relation_name
        self.database = DatabaseRequires(
            self._charm,
            relation_name=self.relation_name,
            database_name=DATABASE_NAME,
        )

    def _get_relation_data(self) -> typing.Optional[DatasourcePostgreSQL]:
        """Get database data from relation.

        Returns:
            Dict: Information needed for setting environment variables.
        """
        if endpoints := self.database.endpoints() is not None:
            primary_endpoint = endpoints.split(",")[0].split(":")
            return DatasourcePostgreSQL(
                user=relation_data.get("username"),
                password=relation_data.get("password"),
                host=primary_endpoint[0],
                port=primary_endpoint[1],
                db=relation_data.get("database"),
            )
        return None

    def reconcile(self) -> typing.Optional[DatasourcePostgreSQL]:
        """Reconcile the database relation."""
        return self._get_relation_data()
