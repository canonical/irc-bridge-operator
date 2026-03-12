# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "Name of the deployed application."
  value       = juju_application.irc-bridge.name
}

output "requires" {
  value = {
    database      = "database"
    matrix_auth   = "matrix-auth"
    ingress       = "ingress"
    ingress_media = "ingress-media"
  }
}

output "provides" {
  value = {}
}

output "endpoints" {
  value = {
    database      = "database"
    matrix_auth   = "matrix-auth"
    ingress       = "ingress"
    ingress_media = "ingress-media"
  }
}
