#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Type definitions for the Synapse charm."""

import re
import typing
from abc import ABC, abstractmethod

import ops
from pydantic import BaseModel, Field, validator


class ReconcilingCharm(ops.CharmBase, ABC):
    """An abstract class for a charm that supports reconciliation."""

    @abstractmethod
    def reconcile(self, event: ops.charm.EventBase) -> None:
        """Reconcile the charm state.

        Args:
            event: The event that triggered the reconciliation.
        """


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
            ValueError: if user_id is not as expected.
        """
        # Based on documentation
        # https://spec.matrix.org/v1.10/appendices/#user-identifiers
        userid_regex = r"@[a-z0-9._=/+-]+:\w+(\.\w+)+"
        if value is None:
            return []
        value_list = ["@" + user_id.strip() for user_id in value.split(",")]
        invalid_user_ids = [
            user_id for user_id in value_list if not re.fullmatch(userid_regex, user_id)
        ]
        if invalid_user_ids:
            raise ValueError(f"Invalid user ID format(s): {', '.join(invalid_user_ids)}")
        return value_list
