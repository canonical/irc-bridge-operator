# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests fixtures."""

from pathlib import Path

import pytest_asyncio
import yaml
from juju.application import Application
from juju.model import Model
from pytest import Config, fixture
from pytest_operator.plugin import OpsTest

import tests.integration.helpers


@fixture(scope="module", name="matrix_homeserver")
def matrix_homeserver():
    """Provide Matrix homeserver."""
    yield "https://example.com"


@fixture(scope="module", name="metadata")
def fixture_metadata():
    """Provide charm metadata."""
    yield yaml.safe_load(Path("./metadata.yaml").read_text(encoding="UTF-8"))


@fixture(scope="module", name="app_name")
def fixture_app_name(metadata):
    """Provide app name from the metadata."""
    yield metadata["name"]


@fixture(scope="module", name="model")
def model_fixture(ops_test: OpsTest) -> Model:
    """Juju model API client."""
    assert ops_test.model
    return ops_test.model


@pytest_asyncio.fixture(scope="module", name="app")
async def app_fixture(
    ops_test: OpsTest,
    app_name: str,
    pytestconfig: Config,
    model: Model,
):
    """Build the charm and deploys it."""
    use_existing = pytestconfig.getoption("--use-existing", default=False)
    if use_existing:
        yield model.applications[app_name]
        return

    if charm := pytestconfig.getoption("--charm-file"):
        application = await model.deploy(f"./{charm}", application_name=app_name)
    else:
        charm = await ops_test.build_charm(".")
        application = await model.deploy(charm, application_name=app_name)

    yield application


@pytest_asyncio.fixture(scope="module", name="app_integrated")
async def app_integrated_fixture(ops_test: OpsTest, app: Application, model: Model):
    """Integrate the charm with PostgreSQL and AnyCharm as matrix-auth provider."""
    config = {"bridge_admins": "admin:example.com", "bot_nickname": "bot"}
    await app.set_config(config)
    await model.deploy("postgresql", channel="14/stable")
    await model.wait_for_idle(apps=["postgresql"], status="active", timeout=60 * 60)
    await model.add_relation(app.name, "postgresql")
    await tests.integration.helpers.generate_anycharm_relation(
        app, ops_test, "matrix-homeserver", None
    )
    await model.wait_for_idle(
        apps=[f"{app.name}", "postgresql", "matrix-homeserver"],
        status="active",
        idle_period=60,
        timeout=60 * 60,
    )
    yield app
