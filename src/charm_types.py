#!/usr/bin/env python3

# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Type definitions for the Synapse charm."""

import re
import typing

from pydantic import BaseModel, Field, validator, ValidationError


class DatasourcePostgreSQL(BaseModel):
    """A named tuple representing a Datasource PostgreSQL.

    Attributes:
        user: User.
        password: Password.
        host: Host (IP or DNS without port or protocol).
        port: Port.
        db: Database name.
    """

    user: str = Field(min_length=1, description="User")
    password: str = Field(min_length=1, description="Password")
    host: str = Field(min_length=1, description="Host")
    port: str = Field(min_length=1, description="Port")
    db: str = Field(min_length=1, description="Database name")


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
