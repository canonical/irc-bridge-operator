# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the IRC bridge service."""

import builtins
import subprocess  # nosec
from pathlib import Path
from secrets import token_hex
from unittest.mock import MagicMock, patch

import pytest
import yaml
from charms.operator_libs_linux.v1 import systemd
from charms.operator_libs_linux.v2 import snap
from requests.exceptions import RequestException

from charm_types import CharmConfig, DatasourcePostgreSQL
from constants import (
    IRC_BRIDGE_CONFIG_FILE_PATH,
    IRC_BRIDGE_KEY_ALGO,
    IRC_BRIDGE_KEY_OPTS,
    IRC_BRIDGE_PEM_FILE_PATH,
    IRC_BRIDGE_SERVICE_NAME,
    IRC_BRIDGE_SNAP_NAME,
)
from irc import (
    InstallError,
    IRCBridgeParams,
    IRCBridgeService,
    ReloadError,
    StartError,
    StopError,
    get_matrix_domain,
)
from lib.charms.synapse.v1.matrix_auth import MatrixAuthProviderData


@pytest.fixture(name="irc_bridge_service")
def irc_bridge_service_fixture():
    """Return a new instance of the IRCBridgeService."""
    return IRCBridgeService()


def test_reconcile_calls_prepare_configure_and_reload_methods(irc_bridge_service, mocker):
    """Test that the reconcile method calls the prepare, configure, and reload methods.

    arrange: Prepare mocks for the prepare, configure, and reload methods.
    act: Call the reconcile method.
    assert: Ensure that the prepare, configure, and reload methods were called
    exactly once.
    """
    mock_prepare = mocker.patch.object(irc_bridge_service, "prepare")
    mock_configure = mocker.patch.object(irc_bridge_service, "configure")
    mock_reload = mocker.patch.object(irc_bridge_service, "reload")

    password = token_hex(16)
    db = DatasourcePostgreSQL(
        user="test_user",
        password=password,
        host="localhost",
        port="5432",
        db="test_db",
        uri=f"postgres://test_user:{password}@localhost:5432/test_db",
    )
    matrix = MatrixAuthProviderData(homeserver="matrix.example.com")
    config = CharmConfig(
        ident_enabled=True,
        bot_nickname="my_bot",
        bridge_admins="admin1:example.com,admin2:example.com",
    )

    url = "http://localhost:8090"
    params = IRCBridgeParams(
        db=db,
        matrix=matrix,
        config=config,
        external_url=url,
        media_external_url="10.10.10.10",
    )
    irc_bridge_service.reconcile(params)

    mock_prepare.assert_called_once()
    mock_configure.assert_called_once()
    mock_reload.assert_called_once()


def test_prepare_installs_snap_package_and_creates_configuration_files(mocker, tmp_path: Path):
    """Test that the prepare method installs the snap package and creates configuration files.

    arrange: Prepare mocks for the _install_snap_package, shutil.copy, pathlib.Path.mkdir,
    systemd.daemon_reload, and systemd.service_enable methods.
    act: Call the prepare method.
    assert: Ensure that the SNAP_MATRIX_APPSERVICE_ARGS was added to environment
        and config.yaml exists.
    """
    config_file_path = tmp_path / "config"
    environment_file_path = tmp_path / "environment"
    environment_file_path.touch()
    with (
        patch("irc.IRC_BRIDGE_CONFIG_DIR_PATH", config_file_path),
        patch("irc.ENVIRONMENT_OS_FILE", environment_file_path),
    ):
        irc_bridge_service = IRCBridgeService()
        mock_install_snap_package = mocker.patch.object(
            irc_bridge_service, "_install_snap_package"
        )
        mock_generate_media_proxy_key = mocker.patch.object(
            irc_bridge_service, "_generate_media_proxy_key"
        )

        irc_bridge_service.prepare()

        mock_install_snap_package.assert_called_once_with(
            snap_name=IRC_BRIDGE_SNAP_NAME, snap_channel="edge"
        )
        mock_generate_media_proxy_key.assert_called_once()
        with open(environment_file_path, encoding="utf-8") as env_file:
            content = env_file.read()
        assert "SNAP_MATRIX_APPSERVICE_ARGS" in content
        config_yaml_file = config_file_path / "config.yaml"
        assert config_yaml_file.exists()


def test_prepare_raises_install_error_if_snap_installation_fails(irc_bridge_service, mocker):
    """Test that the prepare method raises an InstallError if the snap installation fails.

    arrange: Prepare a mock for the _install_snap_package method that raises an InstallError.
    act: Call the prepare method.
    assert: Ensure that an InstallError is raised.
    """
    mock_install_snap_package = mocker.patch.object(
        irc_bridge_service, "_install_snap_package", side_effect=InstallError("oops")
    )

    with pytest.raises(InstallError):
        irc_bridge_service.prepare()

    mock_install_snap_package.assert_called_once_with(
        snap_name=IRC_BRIDGE_SNAP_NAME, snap_channel="edge"
    )


def test_install_snap_package_installs_snap_if_not_present(irc_bridge_service, mocker):
    """Test that the _install_snap_package method installs the snap package if it is not present.

    arrange: Prepare mocks for the SnapCache and SnapPackage classes and the ensure method.
    act: Call the _install_snap_package method.
    assert: Ensure that the SnapCache and SnapPackage classes were called exactly once and that
    the ensure method was called with the correct arguments.
    """
    mock_snap_cache = mocker.patch.object(snap, "SnapCache")
    mock_snap_package = MagicMock()
    mock_snap_package.present = False
    mock_snap_cache.return_value = {IRC_BRIDGE_SNAP_NAME: mock_snap_package}
    mock_ensure = mocker.patch.object(mock_snap_package, "ensure")

    irc_bridge_service._install_snap_package(  # pylint: disable=protected-access
        snap_name=IRC_BRIDGE_SNAP_NAME, snap_channel="edge"
    )

    mock_snap_cache.assert_called_once()
    mock_ensure.assert_called_once_with(snap.SnapState.Latest, channel="edge")


def test_install_snap_package_does_not_install_snap_if_already_present(irc_bridge_service, mocker):
    """Test that the _install_snap_package method does not install the snap package if present.

    arrange: Prepare mocks for the SnapCache and SnapPackage classes and the ensure method.
    act: Call the _install_snap_package method.
    assert: Ensure that the SnapCache and SnapPackage classes were called exactly once and that
    the ensure method was not called.
    """
    mock_snap_cache = mocker.patch.object(snap, "SnapCache")
    mock_snap_package = MagicMock()
    mock_snap_package.present = True
    mock_snap_cache.return_value = {IRC_BRIDGE_SNAP_NAME: mock_snap_package}
    mock_ensure = mocker.patch.object(mock_snap_package, "ensure")

    irc_bridge_service._install_snap_package(  # pylint: disable=protected-access
        snap_name=IRC_BRIDGE_SNAP_NAME, snap_channel="edge"
    )

    mock_snap_cache.assert_called_once()
    mock_ensure.assert_not_called()


def test_install_snap_package_refreshes_snap_if_already_present(irc_bridge_service, mocker):
    """Test that the _install_snap_package method refreshes the snap if it is already present.

    arrange: Prepare mocks for the SnapCache and SnapPackage classes and the ensure method.
    act: Call the _install_snap_package method with the refresh argument set to True.
    assert: Ensure that the SnapCache and SnapPackage classes were called exactly once and that
    the ensure method was called with the correct arguments.
    """
    mock_snap_cache = mocker.patch.object(snap, "SnapCache")
    mock_snap_package = MagicMock()
    mock_snap_package.present = True
    mock_snap_cache.return_value = {IRC_BRIDGE_SNAP_NAME: mock_snap_package}
    mock_ensure = mocker.patch.object(mock_snap_package, "ensure")

    irc_bridge_service._install_snap_package(  # pylint: disable=protected-access
        snap_name=IRC_BRIDGE_SNAP_NAME, snap_channel="edge", refresh=True
    )

    mock_snap_cache.assert_called_once()
    mock_ensure.assert_called_once_with(snap.SnapState.Latest, channel="edge")


def test_install_snap_package_raises_install_error_if_snap_installation_fails(
    irc_bridge_service, mocker
):
    """Test that the _install_snap_package method raises an InstallError if the snap install fails.

    arrange: Prepare mocks for the SnapCache and SnapPackage classes and the ensure method.
    act: Call the _install_snap_package method with the refresh argument set to True.
    assert: Ensure that an InstallError is raised.
    """
    mock_snap_cache = mocker.patch.object(snap, "SnapCache")
    mock_snap_package = MagicMock()
    mock_snap_package.present = False
    mock_snap_cache.return_value = {IRC_BRIDGE_SNAP_NAME: mock_snap_package}
    mock_ensure = mocker.patch.object(mock_snap_package, "ensure", side_effect=snap.SnapError)

    with pytest.raises(InstallError):
        irc_bridge_service._install_snap_package(  # pylint: disable=protected-access
            snap_name=IRC_BRIDGE_SNAP_NAME, snap_channel="edge"
        )

    mock_snap_cache.assert_called_once()
    mock_ensure.assert_called_once_with(snap.SnapState.Latest, channel="edge")


def test_configure_generates_pem_file_local(irc_bridge_service, mocker):
    """Test that the _generate_pem_file_local method generates the PEM file.

    arrange: Prepare a mock for the subprocess.run method.
    act: Call the _generate_pem_file_local method.j
    assert: Ensure that the subprocess.run method was called with the correct arguments.
    """
    mock_run = mocker.patch.object(subprocess, "run")

    irc_bridge_service._generate_pem_file_local()  # pylint: disable=protected-access

    # pylint: disable=duplicate-code
    mock_run.assert_called_once_with(
        [
            "/bin/bash",
            "-c",
            f"openssl genpkey -out {IRC_BRIDGE_PEM_FILE_PATH} "
            f"-outform PEM -algorithm {IRC_BRIDGE_KEY_ALGO} -pkeyopt {IRC_BRIDGE_KEY_OPTS}",
        ],
        check=True,
        capture_output=True,
    )
    # pylint: enable=duplicate-code


def test_configure_generates_app_registration_local(irc_bridge_service, mocker, tmp_path: Path):
    """Test that the _generate_app_registration_local method generates the app registration file.

    arrange: Prepare a mock for the subprocess.run method.
    act: Call the _generate_app_registration_local method.
    assert: Ensure that the subprocess.run method was called with the correct arguments.
    """
    registration_file_path = tmp_path / "appservice-registration-irc.yaml"
    Path(str(registration_file_path) + ".tmp").touch()
    with patch("irc.IRC_BRIDGE_REGISTRATION_FILE_PATH", registration_file_path):
        mock_run = mocker.patch.object(subprocess, "run")
        config = CharmConfig(
            ident_enabled=True,
            bot_nickname="my_bot",
            bridge_admins="admin1:example.com,admin2:example.com",
        )
        assert not registration_file_path.exists(), (
            f"Expected {registration_file_path} not to exist before running the command"
        )

        params = IRCBridgeParams(
            db=None,
            matrix=None,
            config=config,
            external_url="http://localhost:8090",
            media_external_url="10.10.10.10",
        )
        irc_bridge_service.set_parameters(params)
        irc_bridge_service._generate_app_registration_local()  # pylint: disable=protected-access

        # pylint: disable=duplicate-code
        mock_run.assert_called_once_with(
            [
                "/bin/bash",
                "-c",
                f"snap run matrix-appservice-irc -r -f {registration_file_path}.tmp"
                f" -u http://localhost:8090 "
                f"-c {IRC_BRIDGE_CONFIG_FILE_PATH} -l {config.bot_nickname}",
            ],
            check=True,
            capture_output=True,
        )
        # pylint: enable=duplicate-code
        assert registration_file_path.exists(), f"Expected {registration_file_path} to exist"


def test_skip_media_proxy_key(irc_bridge_service, mocker, tmp_path: Path):
    """Test that the _generate_media_proxy_key method not generates the key file
        if already exists.

    arrange: Prepare a mock for the subprocess.run method.
    act: Call the _generate_media_proxy_key method.
    assert: Ensure that the subprocess.run method was not called.
    """
    signing_key_file_path = tmp_path / "signing.key"
    signing_key_file_path.touch()
    with patch("irc.IRC_BRIDGE_SIGNING_KEY_FILE_PATH", signing_key_file_path):
        mock_run = mocker.patch.object(subprocess, "run")

        irc_bridge_service._generate_media_proxy_key()  # pylint: disable=protected-access

        mock_run.assert_not_called()


def test_configure_evaluates_configuration_file_local(irc_bridge_service, mocker):
    """Test that the _eval_conf_local method evaluates the configuration file.

    arrange: Prepare mocks for the open, yaml.safe_load, and yaml.dump methods.
    act: Call the _eval_conf_local method.
    assert: Ensure that the open, yaml.safe_load, and yaml.dump methods were called as expected.
    """
    mock_builtin_open = mocker.patch.object(builtins, "open")
    mock_safe_load = mocker.patch.object(yaml, "safe_load")
    mock_dump = mocker.patch.object(yaml, "dump")

    password = token_hex(16)
    db = DatasourcePostgreSQL(
        user="test_user",
        password=password,
        host="localhost",
        port="5432",
        db="test_db",
        uri=f"postgres://test_user:{password}@localhost:5432/test_db",
    )
    matrix = MatrixAuthProviderData(homeserver="matrix.example.com")
    config = CharmConfig(
        ident_enabled=True,
        bot_nickname="my_bot",
        bridge_admins="admin1:example.com,admin2:example.com",
    )

    params = IRCBridgeParams(
        db=db,
        matrix=matrix,
        config=config,
        external_url="http://localhost:8090",
        media_external_url="10.10.10.10",
    )
    irc_bridge_service.set_parameters(params)
    irc_bridge_service._eval_conf_local()  # pylint: disable=protected-access

    calls = [
        mocker.call(f"{IRC_BRIDGE_CONFIG_FILE_PATH.absolute()}", "r", encoding="utf-8"),
        mocker.call(f"{IRC_BRIDGE_CONFIG_FILE_PATH.absolute()}", "w", encoding="utf-8"),
    ]

    mock_builtin_open.assert_has_calls(calls, any_order=True)
    mock_safe_load.assert_called_once_with(
        mock_builtin_open().__enter__()  # pylint: disable=unnecessary-dunder-call
    )
    mock_dump.assert_called_once_with(
        mock_safe_load(),
        mock_builtin_open().__enter__(),  # pylint: disable=unnecessary-dunder-call
    )


def test_reload_restarts_matrix_appservice_irc_service(irc_bridge_service, mocker):
    """Test that the reload method reloads the matrix-appservice-irc service.

    arrange: Prepare a mock for the systemd.service_restart method.
    act: Call the reload method.
    assert: Ensure that the systemd.service_restart method was called with the correct arguments.
    """
    mock_systemd_daemon_reload = mocker.patch.object(systemd, "daemon_reload")
    mock_service_enable = mocker.patch.object(systemd, "service_enable")
    mock_service_restart = mocker.patch.object(systemd, "service_restart")

    irc_bridge_service.reload()

    mock_systemd_daemon_reload.assert_called_once()
    mock_service_enable.assert_called_once_with(IRC_BRIDGE_SERVICE_NAME)
    mock_service_restart.assert_called_once_with(IRC_BRIDGE_SERVICE_NAME)


def test_reload_raises_reload_error_if_reload_fails(irc_bridge_service, mocker):
    """Test that the reload method raises a ReloadError if the service reload fails.

    arrange: Prepare a mock for the systemd.service_reload method that raises a SystemdError.
    act: Call the reload method.
    assert: Ensure that a ReloadError is raised.
    """
    mock_systemd_daemon_reload = mocker.patch.object(systemd, "daemon_reload")
    mock_service_enable = mocker.patch.object(systemd, "service_enable")
    mock_service_restart = mocker.patch.object(
        systemd, "service_restart", side_effect=systemd.SystemdError
    )

    with pytest.raises(ReloadError):
        irc_bridge_service.reload()

    mock_systemd_daemon_reload.assert_called_once()
    mock_service_enable.assert_called_once_with(IRC_BRIDGE_SERVICE_NAME)
    mock_service_restart.assert_called_once_with(IRC_BRIDGE_SERVICE_NAME)


def test_start_starts_matrix_appservice_irc_service(irc_bridge_service, mocker):
    """Test that the start method starts the matrix-appservice-irc service.

    arrange: Prepare a mock for the systemd.service_start method.
    act: Call the start method.
    assert: Ensure that the systemd.service_start method was called with the correct arguments.
    """
    mock_service_start = mocker.patch.object(systemd, "service_start")

    irc_bridge_service.start()

    mock_service_start.assert_called_once_with(IRC_BRIDGE_SERVICE_NAME)


def test_start_raises_start_error_if_start_fails(irc_bridge_service, mocker):
    """Test that the start method raises a StartError if the service start fails.

    arrange: Prepare a mock for the systemd.service_start method that raises a SystemdError.
    act: Call the start method.
    assert: Ensure that a StartError is raised.
    """
    mock_service_start = mocker.patch.object(
        systemd, "service_start", side_effect=systemd.SystemdError
    )

    with pytest.raises(StartError):
        irc_bridge_service.start()

    mock_service_start.assert_called_once_with(IRC_BRIDGE_SERVICE_NAME)


def test_stop_stops_matrix_appservice_irc_service(irc_bridge_service, mocker):
    """Test that the stop method stops the matrix-appservice-irc service.

    arrange: Prepare a mock for the systemd.service_stop method.
    act: Call the stop method.
    assert: Ensure that the systemd.service_stop method was called with the correct arguments.
    """
    mock_service_stop = mocker.patch.object(systemd, "service_stop")

    irc_bridge_service.stop()

    mock_service_stop.assert_called_once_with(IRC_BRIDGE_SNAP_NAME)


def test_stop_raises_stop_error_if_stop_fails(irc_bridge_service, mocker):
    """Test that the stop method raises a StopError if the service stop fails.

    arrange: Prepare a mock for the systemd.service_stop method that raises a SystemdError.
    act: Call the stop method.
    assert: Ensure that a StopError is raised.
    """
    mock_service_stop = mocker.patch.object(systemd, "service_stop", side_effect=snap.SnapError)

    with pytest.raises(StopError):
        irc_bridge_service.stop()

    mock_service_stop.assert_called_once_with(IRC_BRIDGE_SNAP_NAME)


@patch("requests.get")
def test_get_matrix_domain_success(mock_get):
    """Test that the get_matrix_domain method returns the server_name value.

    arrange: Prepare a mock for the API call.
    act: Call get_matrix_domain.
    assert: Ensure that the domain is the one expected (example.org).
    """
    mock_response = MagicMock()
    expected_domain = "example.org"
    mock_response.json.return_value = {"server_name": expected_domain}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    assert get_matrix_domain("https://chat-server.example.org") == expected_domain


@patch("requests.get")
def test_get_matrix_domain_error(mock_get):
    """Test that the get_matrix_domain method returns the URL domain value in
        case of error.

    arrange: Prepare a mock for the API call that raises Exception.
    act: Call get_matrix_domain.
    assert: Ensure that the domains is the one expected
        (chat-server.example.org).
    """
    mock_get.side_effect = RequestException("Mocked exception")

    expected_domain = "chat-server.example.org"
    assert get_matrix_domain("https://chat-server.example.org") == expected_domain
