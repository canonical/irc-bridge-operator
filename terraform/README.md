# IRC Bridge Terraform Module

This Terraform module deploys the [irc-bridge](https://charmhub.io/irc-bridge) charm on a Juju model.

## Usage

```hcl
module "irc-bridge" {
  source     = "git::https://github.com/canonical/irc-bridge-operator//terraform"
  model_uuid = juju_model.my_model.uuid
}
```

## Integrations

The irc-bridge charm requires the following integrations:

- `database`: PostgreSQL database (interface: `postgresql_client`)
- `matrix-auth`: Matrix authentication (interface: `matrix_auth`)
- `ingress`: Ingress for the bridge (interface: `ingress`)
- `ingress-media`: Ingress for media (interface: `ingress`)

## Requirements

| Name | Version |
|------|---------|
| terraform | ~> 1.12 |
| juju | ~> 1.0 |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| app\_name | Name of the application in the Juju model. | `string` | `"irc-bridge"` | no |
| base | The operating system on which to deploy. | `string` | `"ubuntu@22.04"` | no |
| channel | The channel to use when deploying a charm. | `string` | `"latest/stable"` | no |
| config | Application config. | `map(string)` | `{}` | no |
| constraints | Juju constraints to apply for this application. | `string` | `""` | no |
| model\_uuid | UUID of the Juju model where the application will be deployed. | `string` | n/a | yes |
| revision | Revision number of the charm. | `number` | `null` | no |
| units | Number of units to deploy. | `number` | `1` | no |

## Outputs

| Name | Description |
|------|-------------|
| app\_name | Name of the deployed application. |
| requires | Map of required relation endpoints. |
| provides | Map of provided relation endpoints. |
| endpoints | Map of all relation endpoints. |
