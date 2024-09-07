# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provide the DatabaseObserver class to handle database relation and state."""

import typing

from ops.charm import CharmBase
from ops.framework import Object
from pydantic import SecretStr

from lib.charms.synapse.v0.matrix_auth import (
    MatrixAuthProviderData,
    MatrixAuthRequirerData,
    MatrixAuthRequires,
)


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
        self.matrix = MatrixAuthRequires(
            self._charm,
            relation_name=relation_name,
        )

    def get_matrix(self) -> typing.Optional[MatrixAuthProviderData]:
        """Return a Matrix authentication datasource model.

        Returns:
            MatrixAuthProviderData: The datasource model.
        """
        return self.matrix.get_remote_relation_data()

    def set_irc_registration(self, content: str) -> None:
        """Set the IRC registration details.

        Args:
            content: The registration content.
        """
        registration = typing.cast(SecretStr, content)
        irc_data = MatrixAuthRequirerData(registration=registration)
        relation = self.model.get_relation(self.matrix.relation_name)
        if relation:
            irc_data.set_registration_id(model=self.model, relation=relation)
            self.matrix.update_relation_data(relation=relation, matrix_auth_requirer_data=irc_data)
