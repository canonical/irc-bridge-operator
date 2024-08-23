# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Database observer unit tests."""

import ops
import pytest
from ops.testing import Harness
from unittest.mock import patch

from database_observer import DatabaseObserver
from charm_types import DatasourcePostgreSQL

from pydantic import ValidationError

REQUIRER_METADATA = """
name: observer-charm
requires:
  database:
    interface: postgresql_client
"""


class ObservedCharm(ops.CharmBase):
    """Class for requirer charm testing."""

    def __init__(self, *args):
        """Construct.

        Args:
            args: Variable list of positional arguments passed to the parent constructor.
        """
        super().__init__(*args)
        self.database = DatabaseObserver(self, "database")

    def reconcile(self):
        """Reconcile method."""
        pass


def test_database_created_calls_reconcile():
    """
    arrange: set up a charm and a database relation.
    act: trigger a database created event.
    assert: the reconcile method is called.
    """
    harness = Harness(ObservedCharm, meta=REQUIRER_METADATA)
    harness.begin()
    harness.add_relation("database", "database-provider")
    relation = harness.charm.framework.model.get_relation("database", 0)


    with patch.object(harness.charm.database._charm, "reconcile") as mock_reconcile:
        harness.charm.database.database.on.database_created.emit(relation)
        assert mock_reconcile.called


def test_uri():
    """
    arrange: set up a charm and a database relation with an empty databag.
    act: populate the relation databag.
    assert: the uri matches the databag content.
    """
    harness = Harness(ObservedCharm, meta=REQUIRER_METADATA)
    harness.begin()
    harness.add_relation(
        "database",
        "database-provider",
        app_data={
            "database": "ircbridge",
            "endpoints": "postgresql-k8s-primary.local:5432",
            "password": "somepass",
            "username": "user1",
        },
    )

    assert harness.charm.database.uri == (
        DatasourcePostgreSQL(user='user1', password='somepass', host='postgresql-k8s-primary.local', port='5432', db='ircbridge')
    )


def test_uri_when_no_relation_data():
    """
    arrange: set up a charm and a database relation with an empty databag.
    act:.
    assert: the uri is None.
    """
    harness = Harness(ObservedCharm, meta=REQUIRER_METADATA)
    harness.begin()
    harness.add_relation("database", "database-provider")

    with pytest.raises(ValidationError):
        harness.charm.database.uri
