# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""IRC Bridge charm business logic."""

import logging
import shutil
import subprocess  # nosec
from urllib.parse import urlparse

import requests
import yaml
from charms.operator_libs_linux.v1 import systemd
from charms.operator_libs_linux.v2 import snap
from charms.synapse.v1.matrix_auth import MatrixAuthProviderData

import exceptions
from charm_types import CharmConfig, DatasourcePostgreSQL
from constants import (
    ENVIRONMENT_OS_FILE,
    IRC_BRIDGE_CONFIG_DIR_PATH,
    IRC_BRIDGE_CONFIG_FILE_PATH,
    IRC_BRIDGE_KEY_ALGO,
    IRC_BRIDGE_KEY_OPTS,
    IRC_BRIDGE_PEM_FILE_PATH,
    IRC_BRIDGE_REGISTRATION_FILE_PATH,
    IRC_BRIDGE_SERVICE_NAME,
    IRC_BRIDGE_SIGNING_KEY_FILE_PATH,
    IRC_BRIDGE_SNAP_NAME,
    IRC_BRIDGE_TEMPLATE_CONFIG_FILE_PATH,
    SNAP_MATRIX_APPSERVICE_ARGS,
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


def get_matrix_domain(matrix_homeserver_url: str) -> str:
    """Fetch the domain (server_name) from the Homeserver URL.

    Args:
        matrix_homeserver_url: Matrix URL provided by matrix-auth integration.

    Returns:
        The content of server_name from the JSON response, or the
            homeserver domain if an error occurs.
    """
    try:
        # This API returns server_name
        # See:
        # https://spec.matrix.org/v1.13/server-server-api/#publishing-keys
        matrix_homeserver_key_url = matrix_homeserver_url.rstrip("/") + "/_matrix/key/v2/server"

        response = requests.get(matrix_homeserver_key_url, timeout=5)
        response.raise_for_status()
        data = response.json()

        return data.get("server_name", urlparse(matrix_homeserver_key_url).netloc)

    except requests.exceptions.RequestException as e:
        logging.exception("Request error for URL %s: %s", matrix_homeserver_key_url, e)
    except ValueError as e:
        logging.error("JSON parsing error for URL %s: %s", matrix_homeserver_key_url, e)
    except KeyError as e:
        logging.error(
            "Missing expected key in response for URL %s: %s", matrix_homeserver_key_url, e
        )

    return urlparse(matrix_homeserver_key_url).netloc


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
        self,
        db: DatasourcePostgreSQL,
        matrix: MatrixAuthProviderData,
        config: CharmConfig,
        external_url: str,
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
            external_url: ingress url (or unit IP)
        """
        self.prepare()
        self.configure(db, matrix, config, external_url)
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

        self._generate_media_proxy_key()

        with open(ENVIRONMENT_OS_FILE, "r+", encoding="utf-8") as env_file:
            lines = env_file.read()
            if "SNAP_MATRIX_APPSERVICE_ARGS" not in lines:
                env_file.write(f'\nSNAP_MATRIX_APPSERVICE_ARGS="{SNAP_MATRIX_APPSERVICE_ARGS}"\n')

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
        self,
        db: DatasourcePostgreSQL,
        matrix: MatrixAuthProviderData,
        config: CharmConfig,
        external_url: str,
    ) -> None:
        """Configure the service.

        Args:
            db: the database configuration
            matrix: the matrix configuration
            config: the charm configuration
            external_url: ingress url (or unit IP)
        """
        self._generate_pem_file_local()
        self._generate_app_registration_local(config, external_url)
        self._eval_conf_local(db, matrix, config)

    def _generate_pem_file_local(self) -> None:
        """Generate the PEM file content."""
        if IRC_BRIDGE_PEM_FILE_PATH.exists():
            logger.info("PEM file already exists. Skipping generation.")
            return
        pem_create_command = [
            "/bin/bash",
            "-c",
            f"openssl genpkey -out {IRC_BRIDGE_PEM_FILE_PATH} "
            f"-outform PEM -algorithm {IRC_BRIDGE_KEY_ALGO} -pkeyopt {IRC_BRIDGE_KEY_OPTS}",
        ]
        logger.info("Creating PEM file for IRC bridge.")
        result = subprocess.run(pem_create_command, check=True, capture_output=True)  # nosec
        logger.info("PEM file creation result: %s", result)

    def _generate_app_registration_local(self, config: CharmConfig, external_url: str) -> None:
        """Generate the content of the app registration file.

        Args:
            config: the charm configuration
            external_url: ingress url (or unit IP)
        """
        temp_registration_file = f"{IRC_BRIDGE_REGISTRATION_FILE_PATH}.tmp"
        app_reg_create_command = [
            "/bin/bash",
            "-c",
            f"snap run matrix-appservice-irc -r -f {temp_registration_file}"
            f" -u {external_url}"
            f" -c {IRC_BRIDGE_CONFIG_FILE_PATH} -l {config.bot_nickname}",
        ]
        logger.info("Creating a temporary app registration file for IRC bridge.")
        result = subprocess.run(app_reg_create_command, check=True, capture_output=True)  # nosec
        logger.info("App registration file creation result: %s", result)
        logger.info("Command succeed, moving temporary file to expected location.")
        shutil.move(temp_registration_file, str(IRC_BRIDGE_REGISTRATION_FILE_PATH))

    def _generate_media_proxy_key(self) -> None:
        """Generate the content of the media proxy key."""
        if IRC_BRIDGE_SIGNING_KEY_FILE_PATH.exists():
            logger.info("Media proxy key file %s already exists, skipping")
            return
        media_proxy_key_command = [
            "/bin/bash",
            "-c",
            f"/snap/matrix-appservice-irc/current/bin/node /snap/matrix-appservice-irc/current/app/lib/generate-signing-key.js > {IRC_BRIDGE_SIGNING_KEY_FILE_PATH}",  # pylint: disable=line-too-long
        ]
        logger.info("Creating an media proxy key for IRC bridge.")
        result = subprocess.run(media_proxy_key_command, check=True)  # nosec
        logger.info("Media proxy key file creation result: %s", result)

    def _eval_conf_local(
        self, db: DatasourcePostgreSQL, matrix: MatrixAuthProviderData, config: CharmConfig
    ) -> None:
        """Generate the content of the irc configuration file.

        Args:
            db: the database configuration
            matrix: the matrix configuration
            config: the charm configuration

        Raises:
            SynapseConfigurationFileError: when encountering a KeyError from the configuration file
        """
        with open(f"{IRC_BRIDGE_CONFIG_FILE_PATH}", "r", encoding="utf-8") as config_file:
            data = yaml.safe_load(config_file)
        try:
            db_conn = data["database"]["connectionString"]
            if db_conn == "" or db_conn != db.uri:
                data["database"]["connectionString"] = db.uri
            data["homeserver"]["url"] = matrix.homeserver
            data["homeserver"]["domain"] = get_matrix_domain(matrix.homeserver)
            data["ircService"]["mediaProxy"][
                "signingKeyPath"
            ] = f"{IRC_BRIDGE_SIGNING_KEY_FILE_PATH}"
            data["ircService"]["passwordEncryptionKeyPath"] = f"{IRC_BRIDGE_PEM_FILE_PATH}"
            data["ircService"]["ident"]["enabled"] = config.ident_enabled
            data["ircService"]["permissions"] = {}
            for admin in config.bridge_admins:
                data["ircService"]["permissions"][admin] = "admin"
        except KeyError as e:
            logger.exception("KeyError: {%s}", e)
            raise exceptions.SynapseConfigurationFileError(
                f"KeyError in configuration file: {e}"
            ) from e
        with open(f"{IRC_BRIDGE_CONFIG_FILE_PATH}", "w", encoding="utf-8") as config_file:
            yaml.dump(data, config_file)

    def get_registration(self) -> str:
        """Return the app registration file content.

        Returns:
            str: the content of the app registration file
        """
        with open(IRC_BRIDGE_REGISTRATION_FILE_PATH, "r", encoding="utf-8") as registration_file:
            return registration_file.read()

    def reload(self) -> None:
        """Reload the matrix-appservice-irc service.

        Check if the service is running and reload it.

        Raises:
            ReloadError: when encountering a SnapError
        """
        try:
            systemd.daemon_reload()
            systemd.service_enable(IRC_BRIDGE_SERVICE_NAME)
            systemd.service_restart(IRC_BRIDGE_SERVICE_NAME)
        except systemd.SystemdError as e:
            error_msg = f"An exception occurred when reloading {IRC_BRIDGE_SNAP_NAME}."
            logger.exception(error_msg)
            raise ReloadError(error_msg) from e

    def start(self) -> None:
        """Start the matrix-appservice-irc service.

        Raises:
            StartError: when encountering a SnapError
        """
        try:
            systemd.service_start(IRC_BRIDGE_SERVICE_NAME)
        except systemd.SystemdError as e:
            error_msg = f"An exception occurred when starting {IRC_BRIDGE_SNAP_NAME}."
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
            error_msg = f"An exception occurred when stopping {IRC_BRIDGE_SNAP_NAME}."
            logger.exception(error_msg)
            raise StopError(error_msg) from e
