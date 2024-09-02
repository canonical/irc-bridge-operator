# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""IRC Bridge charm business logic."""

import logging
import shutil
import subprocess  # nosec

import yaml
from charms.operator_libs_linux.v1 import systemd
from charms.operator_libs_linux.v2 import snap

import exceptions
from charm_types import CharmConfig, DatasourceMatrix, DatasourcePostgreSQL
from constants import (
    IRC_BRIDGE_CONFIG_DIR_PATH,
    IRC_BRIDGE_CONFIG_FILE_PATH,
    IRC_BRIDGE_HEALTH_PORT,
    IRC_BRIDGE_KEY_ALGO,
    IRC_BRIDGE_KEY_OPTS,
    IRC_BRIDGE_PEM_FILE_PATH,
    IRC_BRIDGE_REGISTRATION_FILE_PATH,
    IRC_BRIDGE_SNAP_NAME,
    IRC_BRIDGE_TARGET_FILE_PATH,
    IRC_BRIDGE_TEMPLATE_CONFIG_FILE_PATH,
    IRC_BRIDGE_TEMPLATE_TARGET_FILE_PATH,
    IRC_BRIDGE_TEMPLATE_UNIT_FILE_PATH,
    IRC_BRIDGE_UNIT_FILE_PATH,
    SNAP_PACKAGES,
    SYSTEMD_DIR_PATH,
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

        if not IRC_BRIDGE_CONFIG_DIR_PATH.exists():
            IRC_BRIDGE_CONFIG_DIR_PATH.mkdir(parents=True)
            logger.info("Created directory %s", IRC_BRIDGE_CONFIG_DIR_PATH)
            shutil.copy(IRC_BRIDGE_TEMPLATE_CONFIG_FILE_PATH, IRC_BRIDGE_CONFIG_DIR_PATH)

        if not IRC_BRIDGE_UNIT_FILE_PATH.exists() or not IRC_BRIDGE_TARGET_FILE_PATH.exists():
            shutil.copy(IRC_BRIDGE_TEMPLATE_UNIT_FILE_PATH, SYSTEMD_DIR_PATH)
            shutil.copy(IRC_BRIDGE_TEMPLATE_TARGET_FILE_PATH, SYSTEMD_DIR_PATH)
            systemd.daemon_reload()
            systemd.service_enable(IRC_BRIDGE_SNAP_NAME)

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
            f"[[ -f {IRC_BRIDGE_PEM_FILE_PATH} ]] || "
            f"openssl genpkey -out {IRC_BRIDGE_PEM_FILE_PATH} "
            f"-outform PEM -algorithm {IRC_BRIDGE_KEY_ALGO} -pkeyopt {IRC_BRIDGE_KEY_OPTS}",
        ]
        logger.info("Creating PEM file for IRC bridge.")
        subprocess.run(pem_create_command, shell=True, check=True, capture_output=True)  # nosec

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
            f"[[ -f {IRC_BRIDGE_REGISTRATION_FILE_PATH} ]] || "
            f"matrix-appservice-irc -r -f {IRC_BRIDGE_REGISTRATION_FILE_PATH}"
            f" -u https://{matrix.host}:{IRC_BRIDGE_HEALTH_PORT} "
            f"-c {IRC_BRIDGE_CONFIG_FILE_PATH} -l {config.bot_nickname}",
        ]
        logger.info("Creating an app registration file for IRC bridge.")
        subprocess.run(
            app_reg_create_command, shell=True, check=True, capture_output=True
        )  # nosec

    def _eval_conf_local(
        self, db: DatasourcePostgreSQL, matrix: DatasourceMatrix, config: CharmConfig
    ) -> None:
        """Generate the content of the irc configuration file.

        Args:
            db: the database configuration
            matrix: the matrix configuration
            config: the charm configuration
        """
        with open(f"{IRC_BRIDGE_CONFIG_FILE_PATH}", "r", encoding="utf-8") as config_file:
            data = yaml.safe_load(config_file)
        db_conn = data["database"]["connectionString"]
        db_string = f"postgres://{db.user}:{db.password}@{db.host}/{db.db}"
        if db_conn == "" or db_conn != db_string:
            db_conn = data["database"]["connectionString"]
        data["homeserver"]["url"] = f"https://{matrix.host}"
        data["ircService"]["ident"] = config.ident_enabled
        data["ircService"]["permissions"] = {}
        for admin in config.bridge_admins:
            data["ircService"]["permissions"][admin] = "admin"
        with open(f"{IRC_BRIDGE_CONFIG_FILE_PATH}", "w", encoding="utf-8") as config_file:
            yaml.dump(data, config_file)

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
