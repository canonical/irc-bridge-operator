# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the charm_types module."""

from secrets import token_hex

import pytest
from pydantic import ValidationError

from charm_types import CharmConfig, DatasourcePostgreSQL


def test_datasource_postgresql():
    """Test the DatasourcePostgreSQL class.

    arrange: Create a DatasourcePostgreSQL instance.
    act: Access the instance attributes.
    assert: The attributes are the same as the input values
    """
    user = "test_user"
    password = token_hex(16)
    host = "localhost"
    port = "5432"
    db = "test_db"
    uri = f"postgres://{user}:{password}@{host}:{port}/{db}"

    datasource = DatasourcePostgreSQL(
        user=user, password=password, host=host, port=port, db=db, uri=uri
    )

    assert datasource.user == user
    assert datasource.password == password
    assert datasource.host == host
    assert datasource.port == port
    assert datasource.db == db
    assert datasource.uri == uri


@pytest.mark.parametrize(
    "data, expected_output, expect_error",
    [
        # Success case
        pytest.param(
            {
                "ident_enabled": True,
                "bot_nickname": "test_bot",
                "bridge_admins": "user1:example.com,user2:banana.test.fruits.com",
            },
            {
                "ident_enabled": True,
                "bot_nickname": "test_bot",
                "bridge_admins": ["@user1:example.com", "@user2:banana.test.fruits.com"],
            },
            False,
            id="valid_user_ids",
        ),
        # Validation error case
        pytest.param(
            {
                "ident_enabled": True,
                "bot_nickname": "test_bot",
                "bridge_admins": "invalid_user_id,user2:example.com",
            },
            None,
            True,
            id="invalid_user_id",
        ),
    ],
)
def test_charm_config(data, expected_output, expect_error):
    """Test the CharmConfig class.

    arrange: Create a CharmConfig instance.
    act: Change attributes.
    assert: The attributes are validate and the same as the input values.
    """
    if expect_error:
        try:
            CharmConfig(**data)
        except ValidationError as e:
            error_message = str(e)
            assert "Invalid user ID format" in error_message
        else:
            assert False, "ValidationError was not raised for invalid user ID."
    else:
        charm_config = CharmConfig(**data)
        assert charm_config.ident_enabled == expected_output["ident_enabled"]
        assert charm_config.bot_nickname == expected_output["bot_nickname"]
        assert charm_config.bridge_admins == expected_output["bridge_admins"]
