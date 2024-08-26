# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""File containing constants to be used in the charm."""

DATABASE_NAME = "ircbridge"
DATABASE_RELATION_NAME = "database"
IRC_BRIDGE_SNAP_NAME = "matrix-appservice-irc"
IRC_BRIDGE_CONFIG_PATH = "/etc/matrix-appservice-irc"
IRC_BRIDGE_CONFIG_TEMPLATE_PATH = "templates"
IRC_BRIDGE_HEALTH_PORT = 5446
MATRIX_RELATION_NAME = "matrix-plugins"
SNAP_PACKAGES = {
    IRC_BRIDGE_SNAP_NAME: {"channel": "edge"},
}
