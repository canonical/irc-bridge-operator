import json
import subprocess

code_provider = """
import logging
import ops

from any_charm_base import AnyCharmBase
from matrix_auth import MatrixAuthProvides, MatrixAuthProviderData

logger = logging.getLogger(__name__)

class AnyCharm(AnyCharmBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.plugin_auth = MatrixAuthProvides(self, relation_name="provide-irc-bridge")
        self.framework.observe(self.on.provide_irc_bridge_relation_created, self._on_relation_created)
        self.framework.observe(self.plugin_auth.on.matrix_auth_request_received, self._on_matrix_auth_request_received)
        #self.framework.observe(self.on.provide_irc_bridge_relation_changed, self._on_relation_changed)

    def _on_relation_created(self, _):
        relation = self.model.get_relation("provide-irc-bridge")
        if relation is not None:
            logger.info(f"Setting relation data")
            matrix_auth_data = MatrixAuthProviderData(
                homeserver="https://example.com",
                shared_secret="foobar"
            )
            matrix_auth_data.set_shared_secret_id(model=self.model, relation=relation)
            self.plugin_auth.update_relation_data(relation, matrix_auth_data)

    def _on_matrix_auth_request_received(self, _):
        relation = self.model.get_relation("provide-irc-bridge")
        if relation is not None:
            logger.info(f"Getting relation data")
            remote_data = self.plugin_auth.get_remote_relation_data()
            logger.info(f"Remote data: {remote_data}")

    def _on_relation_changed(self, _):
        relation = self.model.get_relation("provide-irc-bridge")
        logger.info(f"Relation: {relation}")
        return
        relation = self.model.get_relation("provide-irc-bridge")
        logger.info(f"Relation: {relation}")
        if relation is not None:
            try:
                logger.info(f"Getting relation data")
                matrix_auth_data = MatrixAuthProviderData.from_relation(model=self.model, relation=relation)
            except Exception as e:
                logger.error(f"Failed to get relation data: {e}")
                logger.info(f"Setting relation data")
                matrix_auth_data = MatrixAuthProviderData(
                    homeserver="https://example.com",
                    shared_secret="foobar"
                )
            matrix_auth_data.set_shared_secret_id(model=self.model, relation=relation)
            self.plugin_auth.update_relation_data(relation, matrix_auth_data)
            remote_data = self.plugin_auth.get_remote_relation_data()
            logger.info(f"Remote data: {remote_data}")
"""

src_overwrite_provider = json.dumps(
    {
        "any_charm.py": code_provider,
        "matrix_auth.py": open("./lib/charms/synapse/v0/matrix_auth.py").read(),
    }
)

subprocess.run(
    [
        "juju",
        "deploy",
        "any-charm",
        "provider",
        "--channel=beta",
        "--config",
        f"src-overwrite={src_overwrite_provider}",
        "--config",
        f"python-packages=pydantic",
    ]
)

code_requirer = """
import logging
import ops

from any_charm_base import AnyCharmBase
from matrix_auth import MatrixAuthRequires, MatrixAuthRequirerData

logger = logging.getLogger(__name__)

class AnyCharm(AnyCharmBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.plugin_auth = MatrixAuthRequires(self, relation_name="require-irc-bridge")
        relation = self.model.get_relation("require-irc-bridge")
        if relation is not None:
            matrix_auth_data = MatrixAuthRequirerData(
                registration="registration example"
            )
            matrix_auth_data.set_registration_id(model=self.model, relation=relation)
            self.plugin_auth.update_relation_data(relation, matrix_auth_data)
            remote_data = self.plugin_auth.get_remote_relation_data()
            logger.info(f"Remote data: {remote_data}")
"""

src_overwrite_requirer = json.dumps(
    {
        "any_charm.py": code_requirer,
        "matrix_auth.py": open("./lib/charms/synapse/v0/matrix_auth.py").read(),
    }
)

#subprocess.run(
#    [
#        "juju",
#        "deploy",
#        "any-charm",
    #        "requirer",
#        "--channel=beta",
#        "--config",
#        f"src-overwrite={src_overwrite_requirer}",
#        "--config",
#        f"python-packages=pydantic",
#    ]
#)

#subprocess.run(
#   [
#       "juju",
#       "config",
#       "provider",
#       f"src-overwrite={src_overwrite_provider}",
#   ]
#)
