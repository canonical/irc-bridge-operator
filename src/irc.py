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

import constants
import exceptions

logger = logging.getLogger(__name__)


class ReloadError(exceptions.SnapError):
    """Exception raised when unable to reload the service."""


class StartError(exceptions.SnapError):
    """Exception raised when unable to start the service."""


class StopError(exceptions.SnapError):
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
    def __init__(self, charm: CharmBase) -> None:
        super().__init__(charm)
        self._charm = charm

    def reconcile(self) -> None:
        """Reconcile the service.

        Simple flow:
        - Check if the snap is installed
        - Check if we have a database relation
        - Check if we have a matrix relation
        - Check if the configuration files exist
        - Check if the service is running
        """
        self.prepare()
        #self.handle_new_matrix_relation_data()
        self.configure()
        self.reload()

    def reload(self) -> None:
        """Reload the matrix-appservice-irc service.
        Check if the service is running and reload it.

        Raises:
            ReloadError: when encountering a SnapError
        """
        try:
            cache = snap.SnapCache()
            charmed_irc_bridge = cache[constants.IRC_BRIDGE_SNAP_NAME]
            charmed_irc_bridge.restart(reload=True)
        except snap.SnapError as e:
            error_msg = (
                f"An exception occurred when reloading {constants.IRC_BRIDGE_SNAP_NAME}. Reason: {e}"
            )
            logger.exception(error_msg)
            raise ReloadError(error_msg) from e

    def start(self) -> None:
        """Start the matrix-appservice-irc service.

        Raises:
            StartError: when encountering a SnapError
        """
        try:
            cache = snap.SnapCache()
            charmed_irc_bridge = cache[constants.IRC_BRIDGE_SNAP_NAME]
            charmed_irc_bridge.start()
        except snap.SnapError as e:
            error_msg = (
                f"An exception occurred when stopping {constants.IRC_BRIDGE_SNAP_NAME}. Reason: {e}"
            )
            logger.exception(error_msg)
            raise StartError(error_msg) from e

    def stop(self) -> None:
        """Stop the matrix-appservice-irc service.
        Sends a SIGTERM to the service.

        Raises:
            StopError: when encountering a SnapError
        """
        try:
            cache = snap.SnapCache()
            charmed_irc_bridge = cache[constants.IRC_BRIDGE_SNAP_NAME]
            charmed_irc_bridge.stop()
        except snap.SnapError as e:
            error_msg = (
                f"An exception occurred when stopping {constants.IRC_BRIDGE_SNAP_NAME}. Reason: {e}"
            )
            logger.exception(error_msg)
            raise StopError(error_msg) from e

    def prepare(self) -> None:
        """Prepare the machine."""
        self._install_snap_package(
            snap_name=constants.IRC_BRIDGE_SNAP_NAME,
            snap_channel=constants.SNAP_PACKAGES[constants.IRC_BRIDGE_SNAP_NAME]["channel"],
        )
        path = pathlib.Path(constants.IRC_BRIDGE_CONFIG_PATH)
        if not path.exists():
            path.mkdir(parents=True)
            logger.info("Created directory %s", path)
            template_path = pathlib.Path(constants.IRC_BRIDGE_CONFIG_TEMPLATE_PATH)
            destination_path = path / "config.yaml"
            template_path.copy(destination_path)
            logger.info("Copied config.yaml to %s", path)

    def configure(self) -> None:
        """Configure the service."""
        self._generate_PEM_file_local()
        self._generate_app_registration_local()
        self._eval_conf_local()


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

    def _write(self, path: pathlib.Path, source: str) -> None:
        """Pushes a file to the unit.

        Args:
            path: The path of the file
            source: The contents of the file to be pushed
        """
        path.write_text(source, encoding="utf-8")
        logger.info("Pushed file %s", path)

    def _generate_PEM_file_local(self) -> None:
        """Generate the PEM file content.

        Raises:
            
        """
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
        )
        logger.info("PEM create output: %s.", exec_process.stdout)

    def _generate_app_registration_local(self) -> str:
        """Generate the content of the app registration file.

        Returns:
            A string
        """
        app_reg_create_command = [
                "/bin/bash",
                "-c",
                f"[[ -f {IRC_BRIDGE_REGISTRATION_PATH} ]] || "
                f"/bin/node /app/app.js -r -f {IRC_BRIDGE_REGISTRATION_PATH} "
                f"-u http://localhost:{IRC_BRIDGE_HEALTH_PORT} "
                f"-c {IRC_BRIDGE_CONFIG_PATH} -l {IRC_BRIDGE_BOT_NAME}",
            ],
        )

    def _eval_conf_local(self) -> str:
        """Generate the content of the irc configuration file.

        Returns:
            A string to write to the configuration file
        """
        db_string = self._handle_new_db_relation_data()
        matrix_sting = self._handle_new_matrix_relation_data()
        # we ignore the matrix string for now until we have a plugins interface
        with open(f"{IRC_BRIDGE_CONFIG_PATH}/config.yaml", "w") as f:
            data = yaml.load(f)
            db_conn = data["database"]["connectionString"]
            if db_conn == "" or db_conn != db_string:
                db_conn = db_string
            # matrix auth string in here TODO

    def _handle_new_db_relation_data(self) -> str:
        """Handle new DB relation data.

        Returns:
            A string that conforms to
            https://github.com/matrix-org/matrix-appservice-irc/blob/develop/config.sample.yaml#L698
            connectionString: "postgres://username:password@host:port/databasename"
        """
        if self._charm.database.is_relation_ready:
            db_data = self._charm.database.get_relation_data()
            db_connect_string = (
                "postgres://"
                f"{db_data['POSTGRES_USER']}:"
                f"{db_data['POSTGRES_PASSWORD']}@"
                f"{db_data['POSTGRES_HOST']}:"
                f"{db_data['POSTGRES_PORT']}/"
                f"{db_data['POSTGRES_DB']}"
            )
            return db_connect_string
        return ""

    def _handle_new_matrix_relation_data(self) -> str:
        """Handle new Matrix relation data.

        Returns:
            A string
        """
        return ""
