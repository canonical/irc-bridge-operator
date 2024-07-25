#!/usr/bin/env python3

# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Type definitions for the Synapse charm."""

import typing
from pydantic import BaseModel, Field


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
    bridge_admins: typing.List[str]
