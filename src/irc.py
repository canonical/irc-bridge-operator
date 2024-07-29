# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""IRC Bridge charm business logic."""

import logging
import os
import pathlib
import subprocess
import shutil
import tempfile
import time
import typing

from charms.operator_libs_linux.v2 import snap
from charms.operator_libs_linux.v1 import systemd
from ops.framework import Object


import constants
import exceptions
from charm_types import DatasourcePostgreSQL, DatasourceMatrix, CharmConfig

logger = logging.getLogger(__name__)


class ReloadError(exceptions.SystemdError):
    """Exception raised when unable to reload the service."""


class StartError(exceptions.SystemdError):
    """Exception raised when unable to start the service."""


class StopError(exceptions.SystemdError):
    """Exception raised when unable to stop the service."""


class InstallError(exceptions.SnapError):
    """Exception raised when unable to install dependencies for the service."""


class IRCBRidgeService(Object):
    """IRC Bridge service class.

    This class provides the necessary methods to manage the matrix-appservice-irc service.
    The service requires a connection to a (PostgreSQL) database and to a Matrix homeserver.
    Both of these will be part of the configuration file created by this class.
    Once the configuration file is created, a PEM file will be generated and an app registration file.
    The app registration file will be used to register the bridge with the Matrix homeserver.
    PEM and the configuration file will be used by the matrix-appservice-irc service.
    """

    def reconcile(self, db: DatasourcePostgreSQL, matrix: DatasourceMatrix, config: CharmConfig) -> None:
        """Reconcile the service.

        Simple flow:
        - Check if the snap is installed
        - Check if we have a database relation
        - Check if we have a matrix relation
        - Check if the configuration files exist
        - Check if the service is running
        """
        self.prepare()
        self.configure(db, matrix, config)
        self.reload()

    def prepare(self) -> None:
        """Prepare the machine.

        Install the snap package and create the configuration directory and file.
        """
        self._install_snap_package(
            snap_name=constants.IRC_BRIDGE_SNAP_NAME,
            snap_channel=constants.SNAP_PACKAGES[constants.IRC_BRIDGE_SNAP_NAME]["channel"],
        )

        config_destination_path = pathlib.Path(constants.IRC_BRIDGE_CONFIG_PATH)
        if not path.exists():
            config_destination_path.mkdir(parents=True)
            logger.info("Created directory %s", config_destination_path)
            template_path = pathlib.Path(constants.IRC_BRIDGE_CONFIG_TEMPLATE_PATH)
            config_path = template_path / "config.yaml"
            shutil.copy(config_path, destination_path)

        systemd_destination_path = pathlib.Path("/etc/systemd/system")
        if not pathlib.Path.exists(systemd_destination_path / "matrix-appservice-irc.target"):
            target_path = template_path / "matrix-appservice-irc.target"
            shutil.copy(target_path, systemd_destination_path)
            service_path = template_path / "matrix-appservice-irc.service"
            shutil.copy(service_path, systemd_destination_path)
            systemd.daemon_reload()
            service_enable("matrix-appservice-irc")

    def _install_snap_package(
        self, snap_name: str, snap_channel: str, refresh: bool = False
    ) -> None:
        """Installs snap package.

        Args:
            snap_name: the snap package to install
            snap_channel: the snap package channel
            refresh: whether to refresh the snap if it's already present.

        Raises:
            InstallError: when encountering a SnapError or a SnapNotFoundError
        """
        try:
            snap_cache = snap.SnapCache()
            snap_package = snap_cache[snap_name]

            if not snap_package.present or refresh:
                snap_package.ensure(snap.SnapState.Latest, channel=snap_channel)

        except (snap.SnapError, snap.SnapNotFoundError) as e:
            error_msg = f"An exception occurred when installing {snap_name}. Reason: {e}"
            logger.exception(error_msg)
            raise InstallError(error_msg) from e

    def configure(self, db: DatasourcePostgreSQL, matrix: DatasourceMatrix, config: CharmConfig) -> None:
        """Configure the service."""
        self._generate_PEM_file_local()
        self._generate_app_registration_local(matrix, config)
        self._eval_conf_local(db, matrix, config)

    def _generate_PEM_file_local(self) -> None:
        """Generate the PEM file content."""
        pem_create_command = [
            "/bin/bash",
            "-c",
            f"[[ -f {IRC_BRIDGE_CONFIG_PATH}/irc_passkey.pem ]] || "
            + "openssl genpkey -out {IRC_BRIDGE_CONFIG_PATH}/irc_passkey.pem "
            + "-outform PEM -algorithm RSA -pkeyopt rsa_keygen_bits:2048",
        ]
        logger.info("Creating PEM file for IRC bridge.")
        exec_process = subprocess.run(
           pem_create_command, shell=True, check=True, capture_output=True)
        logger.info("PEM create output: %s.", exec_process.stdout)

    def _generate_app_registration_local(self, matrix: DatasourceMatrix, config: CharmConfig) -> str:
        """Generate the content of the app registration file.

        Returns:
            A string
        """
        app_reg_create_command = [
            "/bin/bash",
            "-c",
            f"[[ -f {constants.IRC_BRIDGE_CONFIG_PATH}/appservice-registration-irc.yaml ]] || "
            f"matrix-appservice-irc -r -f {constants.IRC_BRIDGE_CONFIG_PATH}/appservice-registration-irc.yaml "
            f"-u http://{matrix['host']}:{constants.IRC_BRIDGE_HEALTH_PORT} "
            f"-c {constants.IRC_BRIDGE_CONFIG_PATH}/config.yaml -l {config['bot_nickname']}",
        ]
        logger.info("Creating an app registration file for IRC bridge.")
        exec_process = subprocess.run(
           app_reg_create_command, shell=True, check=True, capture_output=True)
        logger.info("Application registration create output: %s.", exec_process.stdout)

    def _eval_conf_local(self, db: DatasourcePostgreSQL, matrix: DatasourceMatrix, config: CharmConfig) -> str:
        """Generate the content of the irc configuration file.

        Returns:
            A string to write to the configuration file
        """
        with open(f"{IRC_BRIDGE_CONFIG_PATH}/config.yaml", "w") as f:
            data = yaml.safe_load(f)
            db_conn = data["database"]["connectionString"]
            db_string = f"postgres://postgres:{db['password']}@{db['host']}/{db['database']}"
            if db_conn == "" or db_conn != db_string:
                db_conn = db_string
            data["homeserver"]["url"] = f"https://{matrix['host']}"
            data["ircService"]["ident"] = config["ident_enabled"]

    def reload(self) -> None:
        """Reload the matrix-appservice-irc service.

        Check if the service is running and reload it.

        Raises:
            ReloadError: when encountering a SnapError
        """
        try:
            systemd.service_reload(constants.IRC_BRIDGE_SNAP_NAME)
        except SystemdError as e:
            error_msg = (
                f"An exception occurred when reloading {constants.IRC_BRIDGE_SNAP_NAME}. Reason: {e}"
            )
            logger.exception(error_msg)
            raise ReloadError(error_msg) from e

    def start(self) -> None:
        """Start the matrix-appservice-irc service.

        Raises:
            StartError: when encountering a SnapError
            RelationDataError: when missing relation data
        """
        try:
            systemd.service_start(constants.IRC_BRIDGE_SNAP_NAME)
        except systemd.SystemdError as e:
            error_msg = (
                f"An exception occurred when starting {constants.IRC_BRIDGE_SNAP_NAME}. Reason: {e}"
            )
            logger.exception(error_msg)
            raise StartError(error_msg) from e

    def stop(self) -> None:
        """Stop the matrix-appservice-irc service.

        Raises:
            StopError: when encountering a SnapError
        """
        try:
            systemd.service_stop(constants.IRC_BRIDGE_SNAP_NAME)
        except snap.SnapError as e:
            error_msg = (
                f"An exception occurred when stopping {constants.IRC_BRIDGE_SNAP_NAME}. Reason: {e}"
            )
            logger.exception(error_msg)
            raise StopError(error_msg) from e
