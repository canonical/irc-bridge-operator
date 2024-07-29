# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provide the DatabaseObserver class to handle database relation and state."""

import typing

from ops.charm import CharmBase
from ops.framework import Object

from charm_types import DatasourceMatrix


class MatrixObserver(Object):
    """The Matrix relation observer."""

    def __init__(self, charm: CharmBase, relation_name: str):
        """Initialize the oserver and register event handlers.

        Args:
            charm: The parent charm to attach the observer to.
            relation_name: The name of the relation to observe
        """
        super().__init__(charm, "matrix-observer")
        self._charm = charm
        self.relation_name = relation_name

    def _get_relation_data(self) -> typing.Optional[DatasourceMatrix]:
        """Get matrix data from relation.

        Returns:
            Dict: Information needed for setting environment variables.
        """
        return DatasourceMatrix(host="localhost")

    def reconcile(self) -> typing.Optional[DatasourceMatrix]:
        """Reconcile the database relation.

        Returns:
            Dict: Information needed for setting environment variables.
        """
        return self._get_relation_data()
