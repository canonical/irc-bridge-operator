#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Helper functions for the integration tests."""

import ipaddress
import json
import pathlib
import random
import string
import tempfile
import typing
from urllib.parse import urlparse

import ops
from juju.application import Application
from juju.client._definitions import FullStatus, UnitStatus
from pytest_operator.plugin import OpsTest
from requests.adapters import DEFAULT_POOLBLOCK, DEFAULT_POOLSIZE, DEFAULT_RETRIES, HTTPAdapter


class ExecutionError(Exception):
    """Exception raised when execution fails.

    Attrs:
        msg (str): Explanation of the error.
    """

    def __init__(self, msg: str):
        """Initialize a new instance of the ExecutionError exception.

        Args:
            msg (str): Explanation of the error.
        """
        self.msg = msg


def _generate_random_filename(length: int = 24, extension: str = "") -> str:
    """Generate a random filename.

    Args:
        length: length of the generated name
        extension: extension of the generated name

    Returns:
        the generated name
    """
    characters = string.ascii_letters + string.digits
    # Disabling sec checking here since we're not looking
    # to generate something cryptographically secure
    random_string = "".join(random.choice(characters) for _ in range(length))  # nosec
    if extension:
        if "." in extension:
            pieces = extension.split(".")
            last_extension = pieces[-1]
            extension = last_extension
        return f"{random_string}.{extension}"
    return random_string


async def run_on_unit(ops_test: OpsTest, unit_name: str, command: str) -> str:
    """Run a command on a specific unit.

    Args:
        ops_test: The ops test framework instance
        unit_name: The name of the unit to run the command on
        command: The command to run

    Returns:
        the command output if it succeeds, otherwise raises an exception.

    Raises:
        ExecutionError: if the command was not successful
    """
    complete_command = ["exec", "--unit", unit_name, "--", *command.split()]
    return_code, stdout, stderr = await ops_test.juju(*complete_command)
    if return_code != 0:
        raise ExecutionError(f"Command {command} failed with code {return_code}: {stderr}")
    return stdout


# pylint: disable=too-many-positional-arguments,too-many-arguments
async def push_to_unit(
    ops_test: OpsTest,
    unit: ops.model.Unit,
    source: str,
    destination: str,
    user: str = "root",
    group: str = "root",
    mode: str = "644",
) -> None:
    """Push a source file to the chosen unit

    Args:
        ops_test: The ops test framework instance
        unit: The unit to push the file to
        source: the content of the file
        destination: the path of the file on the unit
        user: the user that owns the file
        group: the group that owns the file
        mode: the mode of the file
    """
    _, temp_path = tempfile.mkstemp()
    with open(temp_path, "w", encoding="utf-8") as fd:
        fd.writelines(source)

    temp_filename_on_workload = _generate_random_filename()
    # unit does have scp_to
    await unit.scp_to(source=temp_path, destination=temp_filename_on_workload)  # type: ignore
    mv_cmd = f"mv /home/ubuntu/{temp_filename_on_workload} {destination}"
    await run_on_unit(ops_test, unit.name, mv_cmd)
    chown_cmd = f"chown {user}:{group} {destination}"
    await run_on_unit(ops_test, unit.name, chown_cmd)
    chmod_cmd = f"chmod {mode} {destination}"
    await run_on_unit(ops_test, unit.name, chmod_cmd)


async def dispatch_to_unit(
    ops_test: OpsTest,
    unit: ops.model.Unit,
    hook_name: str,
):
    """Dispatch a hook to the chosen unit.

    Args:
        ops_test: The ops test framework instance
        unit: The unit to push the file to
        hook_name: the hook name
    """
    await ops_test.juju(
        "exec",
        "--unit",
        unit.name,
        "--",
        f"export JUJU_DISPATCH_PATH=hooks/{hook_name}; ./dispatch",
    )


async def set_config(ops_test: OpsTest, app_name: str, config: dict):
    """Set the charm configuration.

    Args:
        ops_test: The ops test framework instance
        app_name: the name of the application to set the configuration
        config: the configuration to set
    """
    assert ops_test.model
    await ops_test.model.applications[app_name].set_config(config=config)


async def generate_anycharm_relation(
    app: Application,
    ops_test: OpsTest,
    any_charm_name: str,
    machine: str | None,
):
    """Deploy any-charm with a wanted matrix auth config and integrate it to the bridge app.

    Args:
        app: Deployed irc-bridge app
        ops_test: The ops test framework instance
        any_charm_name: Name of the to be deployed any-charm
        machine: The machine to deploy the any-charm onto
    """
    any_app_name = any_charm_name
    any_charm_content = pathlib.Path("tests/integration/any_charm.py").read_text(encoding="utf-8")
    matrix_auth_content = pathlib.Path("lib/charms/synapse/v1/matrix_auth.py").read_text(
        encoding="utf-8"
    )
    any_charm_src_overwrite = {
        "any_charm.py": any_charm_content,
        "matrix_auth.py": matrix_auth_content,
    }
    assert ops_test.model
    any_charm = await ops_test.model.deploy(
        "any-charm",
        application_name=any_app_name,
        channel="beta",
        config={
            "python-packages": "pydantic",
            "src-overwrite": json.dumps(any_charm_src_overwrite),
        },
        to=machine,
    )
    await ops_test.model.wait_for_idle(apps=[any_charm.name])
    await ops_test.model.add_relation(
        f"{any_charm.name}:provide-matrix-auth", f"{app.name}:matrix-auth"
    )


async def get_unit_address(application: Application) -> str:
    """Get the unit address to make HTTP requests.

    Args:
        application: The deployed application

    Returns:
        The unit address
    """
    status: FullStatus = await application.model.get_status([application.name])
    application = typing.cast(Application, status.applications[application.name])
    unit_status: UnitStatus = next(iter(application.units.values()))
    assert unit_status.public_address, "Invalid unit address"
    address = (
        unit_status.public_address
        if isinstance(unit_status.public_address, str)
        else unit_status.public_address.decode()
    )

    unit_ip_address = ipaddress.ip_address(address)
    url = f"http://{str(unit_ip_address)}"
    if isinstance(unit_ip_address, ipaddress.IPv6Address):
        url = f"http://[{str(unit_ip_address)}]"
    return url


class DNSResolverHTTPSAdapter(HTTPAdapter):
    """A simple mounted DNS resolver for HTTP requests."""

    def __init__(
        self,
        hostname,
        ip,
    ):
        """Initialize the dns resolver.

        Args:
            hostname: DNS entry to resolve.
            ip: Target IP address.
        """
        self.hostname = hostname
        self.ip = ip
        super().__init__(
            pool_connections=DEFAULT_POOLSIZE,
            pool_maxsize=DEFAULT_POOLSIZE,
            max_retries=DEFAULT_RETRIES,
            pool_block=DEFAULT_POOLBLOCK,
        )

    # Ignore pylint rule as this is the parent method signature
    def send(
        self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None
    ):  # pylint: disable=too-many-arguments, too-many-positional-arguments
        """Wrap HTTPAdapter send to modify the outbound request.

        Args:
            request: Outbound HTTP request.
            stream: argument used by parent method.
            timeout: argument used by parent method.
            verify: argument used by parent method.
            cert: argument used by parent method.
            proxies: argument used by parent method.

        Returns:
            Response: HTTP response after modification.
        """
        connection_pool_kwargs = self.poolmanager.connection_pool_kw

        result = urlparse(request.url)
        if result.hostname == self.hostname:
            ip = self.ip
            if result.scheme == "https" and ip:
                request.url = request.url.replace(
                    "https://" + result.hostname,
                    "https://" + ip,
                )
                connection_pool_kwargs["server_hostname"] = result.hostname
                connection_pool_kwargs["assert_hostname"] = result.hostname
                request.headers["Host"] = result.hostname
            else:
                connection_pool_kwargs.pop("server_hostname", None)
                connection_pool_kwargs.pop("assert_hostname", None)

        return super().send(request, stream, timeout, verify, cert, proxies)
