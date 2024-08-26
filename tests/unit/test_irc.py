import pytest
from unittest.mock import MagicMock
from charm_types import DatasourcePostgreSQL, DatasourceMatrix, CharmConfig
from irc import IRCBridgeService, InstallError, ReloadError, StartError, StopError

import pathlib
import shutil
import subprocess

import yaml
from charms.operator_libs_linux.v1 import systemd
from charms.operator_libs_linux.v2 import snap
from constants import (
    IRC_BRIDGE_CONFIG_PATH,
    IRC_BRIDGE_CONFIG_TEMPLATE_PATH,
    IRC_BRIDGE_HEALTH_PORT,
    IRC_BRIDGE_SNAP_NAME,
    SNAP_PACKAGES,
)

SYSTEMD_SYSTEM_PATH = "/etc/systemd/system"

@pytest.fixture
def irc_bridge_service():
    return IRCBridgeService()


def test_reconcile_calls_prepare_configure_and_reload_methods(
    irc_bridge_service, mocker
):
    mock_prepare = mocker.patch.object(irc_bridge_service, "prepare")
    mock_configure = mocker.patch.object(irc_bridge_service, "configure")
    mock_reload = mocker.patch.object(irc_bridge_service, "reload")

    db = DatasourcePostgreSQL(
        user="test_user",
        password="test_password",
        host="localhost",
        port="5432",
        db="test_db",
    )
    matrix = DatasourceMatrix(host="matrix.example.com")
    config = CharmConfig(
        ident_enabled=True,
        bot_nickname="my_bot",
        bridge_admins="admin1:example.com,admin2:example.com",
    )

    irc_bridge_service.reconcile(db, matrix, config)

    mock_prepare.assert_called_once()
    mock_configure.assert_called_once_with(db, matrix, config)
    mock_reload.assert_called_once()


def test_prepare_installs_snap_package_and_creates_configuration_files(
    irc_bridge_service, mocker
):
    mock_install_snap_package = mocker.patch.object(
        irc_bridge_service, "_install_snap_package"
    )
    mock_copy = mocker.patch.object(shutil, "copy")
    mock_mkdir = mocker.patch.object(pathlib.Path, "mkdir")
    mock_daemon_reload = mocker.patch.object(systemd, "daemon_reload")
    mock_service_enable = mocker.patch.object(
        systemd, "service_enable"
    )

    irc_bridge_service.prepare()

    mock_install_snap_package.assert_called_once_with(
        snap_name="matrix-appservice-irc", snap_channel="edge"
    )
    mock_mkdir.assert_called_once_with(
        parents=True
    )
    copy_calls = [
        mocker.call(
            pathlib.Path(IRC_BRIDGE_CONFIG_TEMPLATE_PATH) / "config.yaml",
            pathlib.Path(IRC_BRIDGE_CONFIG_PATH),
        ),
        mocker.call(
            pathlib.Path(IRC_BRIDGE_CONFIG_TEMPLATE_PATH) / "matrix-appservice-irc.target",
            pathlib.Path(SYSTEMD_SYSTEM_PATH),
        ),
        mocker.call(
            pathlib.Path(IRC_BRIDGE_CONFIG_TEMPLATE_PATH) / "matrix-appservice-irc.service",
            pathlib.Path(SYSTEMD_SYSTEM_PATH),
        ),
    ]
    mock_copy.assert_has_calls(copy_calls)
    mock_daemon_reload.assert_called_once()
    mock_service_enable.assert_called_once_with("matrix-appservice-irc")


def test_prepare_does_not_copy_files_if_already_exist(
    irc_bridge_service, mocker
):
    mock_install_snap_package = mocker.patch.object(
        irc_bridge_service, "_install_snap_package"
    )
    mock_copy = mocker.patch.object(shutil, "copy")
    mock_mkdir = mocker.patch.object(pathlib.Path, "mkdir")
    mock_daemon_reload = mocker.patch.object(systemd, "daemon_reload")
    mock_service_enable = mocker.patch.object(
        systemd, "service_enable"
    )

    mocker.patch.object(
        pathlib.Path, "exists", return_value=True
    )

    irc_bridge_service.prepare()

    mock_install_snap_package.assert_called_once_with(
        snap_name="matrix-appservice-irc", snap_channel="edge"
    )
    mock_mkdir.assert_not_called()
    mock_copy.assert_not_called()
    mock_daemon_reload.assert_not_called()
    mock_service_enable.assert_not_called()


def test_prepare_raises_install_error_if_snap_installation_fails(
    irc_bridge_service, mocker
):
    mock_install_snap_package = mocker.patch.object(
        irc_bridge_service, "_install_snap_package", side_effect=InstallError("oops")
    )

    with pytest.raises(InstallError):
        irc_bridge_service.prepare()

    mock_install_snap_package.assert_called_once_with(
        snap_name="matrix-appservice-irc", snap_channel="edge"
    )


def test_install_snap_package_installs_snap_if_not_present(
    irc_bridge_service, mocker
):
    mock_snap_cache = mocker.patch.object(snap, "SnapCache")
    mock_snap_package = MagicMock()
    mock_snap_package.present = False
    mock_snap_cache.return_value = {"matrix-appservice-irc": mock_snap_package}
    mock_ensure = mocker.patch.object(mock_snap_package, "ensure")

    irc_bridge_service._install_snap_package(
        snap_name="matrix-appservice-irc", snap_channel="edge"
    )

    mock_snap_cache.assert_called_once()
    mock_ensure.assert_called_once_with(
        snap.SnapState.Latest, channel="edge"
    )


def test_install_snap_package_does_not_install_snap_if_already_present(
    irc_bridge_service, mocker
):
    mock_snap_cache = mocker.patch.object(snap, "SnapCache")
    mock_snap_package = MagicMock()
    mock_snap_package.present = True
    mock_snap_cache.return_value = {"matrix-appservice-irc": mock_snap_package}
    mock_ensure = mocker.patch.object(mock_snap_package, "ensure")

    irc_bridge_service._install_snap_package(
        snap_name="matrix-appservice-irc", snap_channel="edge"
    )

    mock_snap_cache.assert_called_once()
    mock_ensure.assert_not_called()


def test_install_snap_package_refreshes_snap_if_already_present(
    irc_bridge_service, mocker
):
    mock_snap_cache = mocker.patch.object(snap, "SnapCache")
    mock_snap_package = MagicMock()
    mock_snap_package.present = True
    mock_snap_cache.return_value = {"matrix-appservice-irc": mock_snap_package}
    mock_ensure = mocker.patch.object(mock_snap_package, "ensure")

    irc_bridge_service._install_snap_package(
        snap_name="matrix-appservice-irc", snap_channel="edge", refresh=True
    )

    mock_snap_cache.assert_called_once()
    mock_ensure.assert_called_once_with(
        snap.SnapState.Latest, channel="edge"
    )


def test_install_snap_package_raises_install_error_if_snap_installation_fails(
    irc_bridge_service, mocker
):
    mock_snap_cache = mocker.patch.object(snap, "SnapCache")
    mock_snap_package = MagicMock()
    mock_snap_package.present = False
    mock_snap_cache.return_value = {"matrix-appservice-irc": mock_snap_package}
    mock_ensure = mocker.patch.object(
        mock_snap_package, "ensure", side_effect=snap.SnapError
    )

    with pytest.raises(InstallError):
        irc_bridge_service._install_snap_package(
            snap_name="matrix-appservice-irc", snap_channel="edge"
        )

    mock_snap_cache.assert_called_once()
    mock_ensure.assert_called_once_with(
        snap.SnapState.Latest, channel="edge"
    )


def test_configure_generates_pem_file_local(irc_bridge_service, mocker):
    mock_run = mocker.patch.object(irc_bridge_service.subprocess, "run")

    irc_bridge_service._generate_pem_file_local()

    mock_run.assert_called_once_with(
        [
            "/bin/bash",
            "-c",
            f"[[ -f {IRC_BRIDGE_CONFIG_PATH}/irc_passkey.pem ]] || "
            + "openssl genpkey -out {IRC_BRIDGE_CONFIG_PATH}/irc_passkey.pem "
            + "-outform PEM -algorithm RSA -pkeyopt rsa_keygen_bits:2048",
        ],
        shell=True,
        check=True,
        capture_output=True,
    )


def test_configure_generates_app_registration_local(irc_bridge_service, mocker):
    mock_run = mocker.patch.object(irc_bridge_service.subprocess, "run")

    matrix = DatasourceMatrix(host="matrix.example.com")
    config = CharmConfig(
        ident_enabled=True,
        bot_nickname="my_bot",
        bridge_admins=["@admin1:example.com", "@admin2:example.com"],
    )

    irc_bridge_service._generate_app_registration_local(matrix, config)

    mock_run.assert_called_once_with(
        [
            "/bin/bash",
            "-c",
            f"[[ -f {IRC_BRIDGE_CONFIG_PATH}/appservice-registration-irc.yaml ]] || "
            f"matrix-appservice-irc -r -f {IRC_BRIDGE_CONFIG_PATH}/appservice-registration-irc.yaml"
            f" -u http://{matrix.host}:{IRC_BRIDGE_HEALTH_PORT} "
            f"-c {IRC_BRIDGE_CONFIG_PATH}/config.yaml -l {config.bot_nickname}",
        ],
        shell=True,
        check=True,
        capture_output=True,
    )


def test_configure_evaluates_configuration_file_local(irc_bridge_service, mocker):
    mock_open = mocker.patch.object(irc_bridge_service.open, "open")
    mock_safe_load = mocker.patch.object(irc_bridge_service.yaml, "safe_load")
    mock_dump = mocker.patch.object(irc_bridge_service.yaml, "dump")

    db = DatasourcePostgreSQL(
        user="test_user",
        password="test_password",
        host="localhost",
        port="5432",
        db="test_db",
    )
    matrix = DatasourceMatrix(host="matrix.example.com")
    config = CharmConfig(
        ident_enabled=True,
        bot_nickname="my_bot",
        bridge_admins=["@admin1:example.com", "@admin2:example.com"],
    )

    irc_bridge_service._eval_conf_local(db, matrix, config)

    mock_open.assert_called_once_with(
        f"{IRC_BRIDGE_CONFIG_PATH}/config.yaml", "r", encoding="utf-8"
    )
    mock_safe_load.assert_called_once_with(mock_open().__enter__())
    mock_dump.assert_called_once_with(mock_safe_load(), mock_open().__enter__())


def test_reload_reloads_matrix_appservice_irc_service(irc_bridge_service, mocker):
    mock_service_reload = mocker.patch.object(
        irc_bridge_service.systemd, "service_reload"
    )

    irc_bridge_service.reload()

    mock_service_reload.assert_called_once_with("matrix-appservice-irc")


def test_reload_raises_reload_error_if_reload_fails(irc_bridge_service, mocker):
    mock_service_reload = mocker.patch.object(
        irc_bridge_service.systemd, "service_reload", side_effect=systemd.SystemdError
    )

    with pytest.raises(ReloadError):
        irc_bridge_service.reload()

    mock_service_reload.assert_called_once_with("matrix-appservice-irc")


def test_start_starts_matrix_appservice_irc_service(irc_bridge_service, mocker):
    mock_service_start = mocker.patch.object(
        irc_bridge_service.systemd, "service_start"
    )

    irc_bridge_service.start()

    mock_service_start.assert_called_once_with("matrix-appservice-irc")


def test_start_raises_start_error_if_start_fails(irc_bridge_service, mocker):
    mock_service_start = mocker.patch.object(
        irc_bridge_service.systemd, "service_start", side_effect=systemd.SystemdError
    )

    with pytest.raises(StartError):
        irc_bridge_service.start()

    mock_service_start.assert_called_once_with("matrix-appservice-irc")


def test_stop_stops_matrix_appservice_irc_service(irc_bridge_service, mocker):
    mock_service_stop = mocker.patch.object(irc_bridge_service.systemd, "service_stop")

    irc_bridge_service.stop()

    mock_service_stop.assert_called_once_with("matrix-appservice-irc")


def test_stop_raises_stop_error_if_stop_fails(irc_bridge_service, mocker):
    mock_service_stop = mocker.patch.object(
        irc_bridge_service.systemd, "service_stop", side_effect=snap.SnapError
    )

    with pytest.raises(StopError):
        irc_bridge_service.stop()

    mock_service_stop.assert_called_once_with("matrix-appservice-irc")
