# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""File containing constants to be used in the charm."""

IRC_BRIDGE_SNAP_NAME = "matrix-appservice-irc"
SNAP_PACKAGES = {
    IRC_BRIDGE_SNAP_NAME: {"channel": "edge"},
}
