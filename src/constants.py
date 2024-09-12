# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""File containing constants to be used in the charm."""

import pathlib

# App
IRC_BRIDGE_HEALTH_PORT = 5446
IRC_BRIDGE_KEY_ALGO = "RSA"
IRC_BRIDGE_KEY_OPTS = "rsa_keygen_bits:2048"

# Database
DATABASE_NAME = "ircbridge"
DATABASE_RELATION_NAME = "database"

# Paths
IRC_BRIDGE_CONFIG_DIR_PATH = pathlib.Path("/etc/matrix-appservice-irc")
IRC_BRIDGE_TEMPLATE_DIR_PATH = pathlib.Path("templates")
SYSTEMD_DIR_PATH = pathlib.Path("/etc/systemd/system")
IRC_BRIDGE_CONFIG_FILE_PATH = IRC_BRIDGE_CONFIG_DIR_PATH / "config.yaml"
IRC_BRIDGE_TEMPLATE_CONFIG_FILE_PATH = IRC_BRIDGE_TEMPLATE_DIR_PATH / "config.yaml"
IRC_BRIDGE_UNIT_FILE_PATH = SYSTEMD_DIR_PATH / "matrix-appservice-irc.service"
IRC_BRIDGE_TARGET_FILE_PATH = SYSTEMD_DIR_PATH / "matrix-appservice-irc.target"
IRC_BRIDGE_TEMPLATE_UNIT_FILE_PATH = IRC_BRIDGE_TEMPLATE_DIR_PATH / "matrix-appservice-irc.service"
IRC_BRIDGE_TEMPLATE_TARGET_FILE_PATH = (
    IRC_BRIDGE_TEMPLATE_DIR_PATH / "matrix-appservice-irc.target"
)
IRC_BRIDGE_PEM_FILE_PATH = IRC_BRIDGE_CONFIG_DIR_PATH / "irc_passkey.pem"
IRC_BRIDGE_REGISTRATION_FILE_PATH = IRC_BRIDGE_CONFIG_DIR_PATH / "appservice-registration-irc.yaml"

# Charm
MATRIX_RELATION_NAME = "require-irc-bridge"

# Snap
IRC_BRIDGE_SNAP_NAME = "matrix-appservice-irc"
SNAP_PACKAGES = {
    IRC_BRIDGE_SNAP_NAME: {"channel": "edge"},
}
