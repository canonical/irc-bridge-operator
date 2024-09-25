# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Exceptions used by the irc-bridge charm."""


class SnapError(Exception):
    """Exception raised when an action on the snap fails.

    Attrs:
        msg (str): Explanation of the error.
    """

    def __init__(self, msg: str):
        """Initialize a new instance of the SnapError exception.

        Args:
            msg (str): Explanation of the error.
        """
        self.msg = msg


class SystemdError(Exception):
    """Exception raised when an action on the systemd service fails.

    Attrs:
        msg (str): Explanation of the error.
    """

    def __init__(self, msg: str):
        """Initialize a new instance of the SystemdError exception.

        Args:
            msg (str): Explanation of the error.
        """
        self.msg = msg


class RelationDataError(Exception):
    """Exception raised when we don't have the expected data in the relation or no relation.

    Attrs:
        msg (str): Explanation of the error.
    """

    def __init__(self, msg: str):
        """Initialize a new instance of the RelationDataError exception.

        Args:
            msg (str): Explanation of the error.
        """
        self.msg = msg


class SynapseConfigurationFileError(Exception):
    """Exception raised when we can't parse the synapse configuration file.

    Attrs:
        msg (str): Explanation of the error.
    """

    def __init__(self, msg: str):
        """Initialize a new instance of the SynapseConfigurationFileError exception.

        Args:
            msg (str): Explanation of the error.
        """
        self.msg = msg
