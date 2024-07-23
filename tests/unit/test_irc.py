import pytest
from unittest.mock import MagicMock

from irc import IRCBRidgeService, ReloadError, StartError, StopError, InstallError
from charms.operator_libs_linux.v2 import snap


def test_reload_success():
    service = IRCBRidgeService()
    cache_mock = MagicMock()
    cache_mock.__getitem__.return_value = MagicMock()
    snap.SnapCache = MagicMock(return_value=cache_mock)

    service.reload()

    cache_mock.__getitem__.assert_called_once_with("matrix-appservice-irc")


def test_reload_snap_error():
    service = IRCBRidgeService()
    cache_mock = MagicMock()
    cache_mock.__getitem__.return_value = MagicMock()
    restart_mock = MagicMock(side_effect=snap.SnapError("SnapError"))
    snap.SnapCache = MagicMock(return_value=cache_mock)
    snap.SnapCache.restart = MagicMock(return_value=restart_mock)

    with pytest.raises(ReloadError):
        service.reload()

    cache_mock.__getitem__.assert_called_once_with("matrix-appservice-irc")


def test_start_success():
    service = IRCBRidgeService()
    service._install_snap_package = MagicMock()
    service._write = MagicMock()
    cache_mock = MagicMock()
    cache_mock.__getitem__.return_value = MagicMock()
    service.snap.SnapCache = MagicMock(return_value=cache_mock)

    service.start()

    cache_mock.__getitem__.assert_called_once_with("irc-bridge-snap")
    service._write.assert_called_once()
    service._install_snap_package.assert_called_once_with(
        snap_name="irc-bridge-snap", snap_channel="stable", refresh=True
    )


def test_start_snap_error():
    service = IRCBRidgeService()
    service._install_snap_package = MagicMock(side_effect=InstallError("SnapError"))
    service._write = MagicMock()
    cache_mock = MagicMock()
    cache_mock.__getitem__.return_value = MagicMock()
    service.snap.SnapCache = MagicMock(return_value=cache_mock)

    with pytest.raises(StartError):
        service.start()

    cache_mock.__getitem__.assert_called_once_with("irc-bridge-snap")
    service._write.assert_not_called()
    service._install_snap_package.assert_called_once_with(
        snap_name="irc-bridge-snap", snap_channel="stable", refresh=True
    )


def test_stop_success():
    service = IRCBRidgeService()
    service._install_snap_package = MagicMock()
    service._write = MagicMock()
    cache_mock = MagicMock()
    cache_mock.__getitem__.return_value = MagicMock()
    service.snap.SnapCache = MagicMock(return_value=cache_mock)

    service.stop()

    cache_mock.__getitem__.assert_called_once_with("irc-bridge-snap")
    service._write.assert_called_once()
    service._install_snap_package.assert_called_once_with(
        snap_name="irc-bridge-snap", snap_channel="stable", refresh=True
    )


def test_stop_snap_error():
    service = IRCBRidgeService()
    service._install_snap_package = MagicMock(side_effect=InstallError("SnapError"))
    service._write = MagicMock()
    cache_mock = MagicMock()
    cache_mock.__getitem__.return_value = MagicMock()
    service.snap.SnapCache = MagicMock(return_value=cache_mock)

    with pytest.raises(StopError):
        service.stop()

    cache_mock.__getitem__.assert_called_once_with("irc-bridge-snap")
    service._write.assert_not_called()
    service._install_snap_package.assert_called_once_with(
        snap_name="irc-bridge-snap", snap_channel="stable", refresh=True
    )
