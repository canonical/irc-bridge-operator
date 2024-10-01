#!/usr/bin/env python3

# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Type definitions for the Synapse charm."""

import re
import typing

import ops
from pydantic import BaseModel, Field, ValidationError, validator


class DatasourcePostgreSQL(BaseModel):
    """A named tuple representing a Datasource PostgreSQL.

    Attributes:
        user: User.
        password: Password.
        host: Host (IP or DNS without port or protocol).
        port: Port.
        db: Database name.
        uri: Database connection URI.
    """

    user: str = Field(min_length=1, description="User")
    password: str = Field(min_length=1, description="Password")
    host: str = Field(min_length=1, description="Host")
    port: str = Field(min_length=1, description="Port")
    db: str = Field(min_length=1, description="Database name")
    uri: str = Field(min_length=1, description="Database connection URI")

    @classmethod
    def from_relation(cls, relation: ops.Relation) -> "DatasourcePostgreSQL":
        """Create a DatasourcePostgreSQL from a relation.

        Args:
            relation: The relation to get the data from.

        Returns:
            A DatasourcePostgreSQL instance.
        """
        relation_data = relation.data[relation.app]
        user = relation_data.get("username", "")
        password = relation_data.get("password", "")
        host, port = relation_data.get("endpoints", ":").split(":")
        db = relation_data.get("database", "")
        uri = f"postgres://{user}:{password}@{host}:{port}/{db}"

        return DatasourcePostgreSQL(
            user=user,
            password=password,
            host=host,
            port=port,
            db=db,
            uri=uri,
        )


class DatasourceMatrix(BaseModel):
    """A named tuple representing a Datasource Matrix.

    Attributes:
        host: Host (IP or DNS without port or protocol).
    """

    host: str


class CharmConfig(BaseModel):
    """A named tuple representing an IRC configuration.

    Attributes:
        ident_enabled: Whether IRC ident is enabled.
        bot_nickname: Bot nickname.
        bridge_admins: Bridge admins.
    """

    ident_enabled: bool
    bot_nickname: str
    bridge_admins: str

    @validator("bridge_admins")
    @classmethod
    def userids_to_list(cls, value: str) -> typing.List[str]:
        """Convert a comma separated list of users to list.

        Args:
            value: the input value.

        Returns:
            The string converted to list.

        Raises:
            ValidationError: if user_id is not as expected.
        """
        # Based on documentation
        # https://spec.matrix.org/v1.10/appendices/#user-identifiers
        userid_regex = r"@[a-z0-9._=/+-]+:\w+\.\w+"
        if value is None:
            return []
        value_list = ["@" + user_id.strip() for user_id in value.split(",")]
        for user_id in value_list:
            if not re.fullmatch(userid_regex, user_id):
                raise ValidationError(f"Invalid user ID format: {user_id}", cls)
        return value_list
