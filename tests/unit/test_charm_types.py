import pytest
from charm_types import DatasourcePostgreSQL

def test_datasource_postgresql():
    # Arrange
    user = "test_user"
    password = "test_password"
    host = "localhost"
    port = "5432"
    db = "test_db"

    # Act
    datasource = DatasourcePostgreSQL(
        user=user,
        password=password,
        host=host,
        port=port,
        db=db
    )

    # Assert
    assert datasource.user == user
    assert datasource.password == password
    assert datasource.host == host
    assert datasource.port == port
    assert datasource.db == db