# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""IRC Bridge charm business logic."""

import logging
import os
import pathlib
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


class IRCBRidgeService:
    """IRC Bridge service class.

    This class provides the necessary methods to manage the matrix-appservice-irc service.
    The service requires a connection to a (PostgreSQL) database and to a Matrix homeserver.
    Both of these will be part of the configuration file created by this class.
    Once the configuration file is created, a PEM file will be generated and an app registration file.
    The app registration file will be used to register the bridge with the Matrix homeserver.
    PEM and the configuration file will be used by the matrix-appservice-irc service.
    """

    def reload(self) -> None:
        """Reload the matrix-appservice-irc service.

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
            logger.error(error_msg)
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
            logger.error(error_msg)
            raise StartError(error_msg) from e

    def stop(self) -> None:
        """Stop the matrix-appservice-irc service.

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
            logger.error(error_msg)
            raise StopError(error_msg) from e

    def prepare(self) -> None:
        """Prepare the machine."""
        self._install_snap_package(
            snap_name=constants.IRC_BRIDGE_SNAP_NAME,
            snap_channel=constants.SNAP_PACKAGES[constants.IRC_BRIDGE_SNAP_NAME]["channel"],
        )

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
            logger.error(error_msg)
            raise InstallError(error_msg) from e

    def _write(self, path: pathlib.Path, source: str) -> None:
        """Pushes a file to the unit.

        Args:
            path: The path of the file
            source: The contents of the file to be pushed
        """
        with open(path, "w", encoding="utf-8") as write_file:
            write_file.write(source)
            logger.info("Pushed file %s", path)

    def _generate_PEM_file_local(self) -> str:
        """Generate the PEM file content.

        Returns:
            A string
        """
        pass

    def _generate_conf_local(self) -> str:
        """Generate the content of the irc configuration file.

        Returns:
            A string
        """
        pass

    def _generate_app_registration_local(self) -> str:
        """Generate the content of the app registration file.

        Returns:
            A string
        """
        pass

    def handle_new_db_relation_data(self) -> str:
        """Handle new DB relation data.

        Returns:
            A string
        """
        pass

    def handle_new_matrix_relation_data(self) -> str:
        """Handle new Matrix relation data.

        Returns:
            A string
        """
        pass
