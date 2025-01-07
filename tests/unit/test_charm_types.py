# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the charm_types module."""

from secrets import token_hex

from charm_types import DatasourcePostgreSQL


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
