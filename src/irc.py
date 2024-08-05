# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""IRC Bridge charm business logic."""

import logging
import pathlib
import shutil
import subprocess

import yaml
from charms.operator_libs_linux.v1 import systemd
from charms.operator_libs_linux.v2 import snap

import exceptions
from charm_types import CharmConfig, DatasourceMatrix, DatasourcePostgreSQL
from constants import (
    IRC_BRIDGE_CONFIG_PATH,
    IRC_BRIDGE_CONFIG_TEMPLATE_PATH,
    IRC_BRIDGE_HEALTH_PORT,
    IRC_BRIDGE_SNAP_NAME,
    SNAP_PACKAGES,
)

logger = logging.getLogger(__name__)


class ReloadError(exceptions.SystemdError):
    """Exception raised when unable to reload the service."""


class StartError(exceptions.SystemdError):
    """Exception raised when unable to start the service."""


class StopError(exceptions.SystemdError):
    """Exception raised when unable to stop the service."""


class InstallError(exceptions.SnapError):
    """Exception raised when unable to install dependencies for the service."""


class IRCBridgeService:
    """IRC Bridge service class.

    This class provides the necessary methods to manage the matrix-appservice-irc service.
    The service requires a connection to a (PostgreSQL) database and to a Matrix homeserver.
    Both of these will be part of the configuration file created by this class.
    Once the configuration file is created, a PEM file will be generated and an app
    registration file.
    The app registration file will be used to register the bridge with the Matrix homeserver.
    PEM and the configuration file will be used by the matrix-appservice-irc service.
    """

    def reconcile(
        self, db: DatasourcePostgreSQL, matrix: DatasourceMatrix, config: CharmConfig
    ) -> None:
        """Reconcile the service.

        Simple flow:
        - Check if the snap is installed
        - Check if we have a database relation
        - Check if we have a matrix relation
        - Check if the configuration files exist
        - Check if the service is running

        Args:
            db: the database configuration
            matrix: the matrix configuration
            config: the charm configuration
        """
        self.prepare()
        self.configure(db, matrix, config)
        self.reload()

    def prepare(self) -> None:
        """Prepare the machine.

        Install the snap package and create the configuration directory and file.
        """
        self._install_snap_package(
            snap_name=IRC_BRIDGE_SNAP_NAME,
            snap_channel=SNAP_PACKAGES[IRC_BRIDGE_SNAP_NAME]["channel"],
        )

        config_destination_path = pathlib.Path(IRC_BRIDGE_CONFIG_PATH)
        if not config_destination_path.exists():
            config_destination_path.mkdir(parents=True)
            logger.info("Created directory %s", config_destination_path)
            template_path = pathlib.Path(IRC_BRIDGE_CONFIG_TEMPLATE_PATH)
            config_path = template_path / "config.yaml"
            shutil.copy(config_path, config_destination_path)

        systemd_destination_path = pathlib.Path("/etc/systemd/system")
        if not pathlib.Path.exists(systemd_destination_path / "matrix-appservice-irc.target"):
            target_path = template_path / "matrix-appservice-irc.target"
            shutil.copy(target_path, systemd_destination_path)
            service_path = template_path / "matrix-appservice-irc.service"
            shutil.copy(service_path, systemd_destination_path)
            systemd.daemon_reload()
            systemd.service_enable("matrix-appservice-irc")

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

    def configure(
        self, db: DatasourcePostgreSQL, matrix: DatasourceMatrix, config: CharmConfig
    ) -> None:
        """Configure the service.

        Args:
            db: the database configuration
            matrix: the matrix configuration
            config: the charm configuration
        """
        self._generate_pem_file_local()
        self._generate_app_registration_local(matrix, config)
        self._eval_conf_local(db, matrix, config)

    def _generate_pem_file_local(self) -> None:
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
            pem_create_command, shell=True, check=True, capture_output=True
        )
        logger.info("PEM create output: %s.", exec_process.stdout)

    def _generate_app_registration_local(
        self, matrix: DatasourceMatrix, config: CharmConfig
    ) -> None:
        """Generate the content of the app registration file.

        Args:
            matrix: the matrix configuration
            config: the charm configuration
        """
        app_reg_create_command = [
            "/bin/bash",
            "-c",
            f"[[ -f {IRC_BRIDGE_CONFIG_PATH}/appservice-registration-irc.yaml ]] || "
            f"matrix-appservice-irc -r -f {IRC_BRIDGE_CONFIG_PATH}/appservice-registration-irc.yaml"
            f" -u http://{matrix.host}:{IRC_BRIDGE_HEALTH_PORT} "
            f"-c {IRC_BRIDGE_CONFIG_PATH}/config.yaml -l {config.bot_nickname}",
        ]
        logger.info("Creating an app registration file for IRC bridge.")
        exec_process = subprocess.run(
            app_reg_create_command, shell=True, check=True, capture_output=True
        )
        logger.info("Application registration create output: %s.", exec_process.stdout)

    def _eval_conf_local(
        self, db: DatasourcePostgreSQL, matrix: DatasourceMatrix, config: CharmConfig
    ) -> None:
        """Generate the content of the irc configuration file.

        Args:
            db: the database configuration
            matrix: the matrix configuration
            config: the charm configuration
        """
        with open(f"{IRC_BRIDGE_CONFIG_PATH}/config.yaml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        db_conn = data["database"]["connectionString"]
        db_string = f"postgres://{db.user}:{db.password}@{db.host}/{db.database}"
        if db_conn == "" or db_conn != db_string:
            db_conn = db_string
        data["homeserver"]["url"] = f"https://{matrix.host}"
        data["ircService"]["ident"] = config["ident_enabled"]
        data["ircService"]["permissions"] = {}
        for admin in config.get("bridge_admins", []):
            data["ircService"]["permissions"][admin] = "admin"
        with open(f"{IRC_BRIDGE_CONFIG_PATH}/config.yaml", "w", encoding="utf-8") as f:
            yaml.dump(data, f)

    def reload(self) -> None:
        """Reload the matrix-appservice-irc service.

        Check if the service is running and reload it.

        Raises:
            ReloadError: when encountering a SnapError
        """
        try:
            systemd.service_reload(IRC_BRIDGE_SNAP_NAME)
        except systemd.SystemdError as e:
            error_msg = f"An exception occurred when reloading {IRC_BRIDGE_SNAP_NAME}. Reason: {e}"
            logger.exception(error_msg)
            raise ReloadError(error_msg) from e

    def start(self) -> None:
        """Start the matrix-appservice-irc service.

        Raises:
            StartError: when encountering a SnapError
        """
        try:
            systemd.service_start(IRC_BRIDGE_SNAP_NAME)
        except systemd.SystemdError as e:
            error_msg = f"An exception occurred when starting {IRC_BRIDGE_SNAP_NAME}. Reason: {e}"
            logger.exception(error_msg)
            raise StartError(error_msg) from e

    def stop(self) -> None:
        """Stop the matrix-appservice-irc service.

        Raises:
            StopError: when encountering a SnapError
        """
        try:
            systemd.service_stop(IRC_BRIDGE_SNAP_NAME)
        except snap.SnapError as e:
            error_msg = f"An exception occurred when stopping {IRC_BRIDGE_SNAP_NAME}. Reason: {e}"
            logger.exception(error_msg)
            raise StopError(error_msg) from e
