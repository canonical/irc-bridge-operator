# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

resource "juju_application" "irc-bridge" {
  name       = var.app_name
  model_uuid = var.model_uuid

  charm {
    name     = "irc-bridge"
    base     = var.base
    channel  = var.channel
    revision = var.revision
  }

  config      = var.config
  constraints = var.constraints
  units       = var.units
}
