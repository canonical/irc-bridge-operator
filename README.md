# IRC Bridge Operator

A [Juju](https://juju.is/) [charm](https://juju.is/docs/olm/charmed-operators)
deploying and managing an IRC Bridge (with Ident server) Integrator on bare metal.

This charm is meant to be used in conjunction with [Synapse](https://github.com/canonical/synapse-operator) and related
to it.

## Get started

IRC Bridge requires a PostgreSQL database and an integration with a Synapse server.

Also, since Synapse needs to interact with IRC Bridge, the charm should be
integrated with HAProxy exposing the application.

## Requirements

* A working station, e.g., a laptop, with amd64 architecture.
* Juju 3 installed and bootstrapped to a LXD and Microk8s controller. You can accomplish
this process by using a [Multipass](https://multipass.run/) VM as outlined in this guide: [Set up / Tear down your test environment](https://juju.is/docs/juju/set-up--tear-down-your-test-environment)

:warning: When using a Multipass VM, make sure to replace IP addresses with the
VM IP in steps that assume you're running locally. To get the IP address of the
Multipass instance run ```multipass info my-juju-vm```.

### Set up a Tutorial Model

To manage resources effectively and to separate this tutorial's workload from
your usual work, create a new model using the following command.

```
juju add-model irc-bridge-tutorial
```

### Deploy IRC Bridge

```
juju deploy irc-bridge --channel edge
```

### Configure IRC Bridge

The bridge_admins are the Matrix users that will be Bridge administrators.

The bot_nickname will be used for creating the Bridge user.

```
juju configure irc-bridge bridge_admins=admin:example.com bot_nickname=ircappservice
```

### Deploy and integrate PostgreSQL

```
juju deploy postgresql --channel 14/stable
juju relate irc-bridge postgresql
```

### Deploy and integrate HAProxy

```
juju deploy haproxy --channel 2.8/edge
juju deploy self-signed-certificates
juju integrate haproxy self-signed-certificates
juju integrate irc-bridge hap
```

### Deploy Synapse in Microk8s controller

Switch to the MicroK8S controller and refer to the [Synapse Getting Started](https://charmhub.io/synapse/docs/tutorial-getting-started) tutorial for step-by-step instructions.

To switch, run the following command:

```
juju switch microk8s-localhost
```

Note: microk8s-localhost is the Microk8s controller.
The command `juju controllers` list all the existings controllers in the environment.

### Create the bridge admin user

```
juju run-action synapse/0 register-user username=admin admin=yes
```

Save the password since will be used in further steps.

### Create an offer

```
juju offer synapse:matrix-auth
```

### Integrate IRC Bridge with Synapse

```
juju switch localhost-localhost
```

Note: localhost-localhost is the LXD controller.
The command `juju controllers` list all the existings controllers in the environment.

### Check health endpoint

```
juju status
```

```
curl https://.../stg-irc-bridge-synapse-staging-irc-bridge/health
OK
```

### Interact with the bridge

Access Synapse via Element with the admin user created previously.

To interact with the Bridge, you can invite the user "ircappservice" to a room or sent a message.

Send a message to the user (if a warning shows up, ignore and proceed) ircappservice.

The Bridge will show a help menu with all the options available. Try the following to guarantee
that the bridge is working.

### Join a IRC channel

You can use send a message to the user "ircappservice" like `!join #python` and
this will be interpreted as a command to join the #python channel.

After this, you can join the room python that corresponds to the IRC python channel.

### Basic operations

#### Enable identd

## Integrations

### PostgreSQL

### Synapse

### Haproxy

## Learn more
* [Read more]() <!--Link to the charm's official documentation-->
* [Developer documentation]() <!--Link to any developer documentation-->
* [Official webpage]() <!--(Optional) Link to official webpage/blog/marketing content--> 
* [Troubleshooting]() <!--(Optional) Link to a page or section about troubleshooting/FAQ-->

## Project and community
* [Issues]() <!--Link to GitHub issues (if applicable)-->
* [Contributing]() <!--Link to any contribution guides--> 
* [Matrix]() <!--Link to contact info (if applicable), e.g. Matrix channel-->
* [Launchpad]() <!--Link to Launchpad (if applicable)-->

====================================
## Project and community

The IRC Bridge Operator is a member of the Ubuntu family. It's an open source
project that warmly welcomes community projects, contributions, suggestions,
fixes and constructive feedback.
* [Code of conduct](https://ubuntu.com/community/code-of-conduct)
* [Get support](https://discourse.charmhub.io/)
* [Join our online chat](https://chat.charmhub.io/charmhub/channels/charm-dev)
* [Contribute](https://charmhub.io/irc-bridge/docs/how-to-contribute)
Thinking about using the IRC Bridge Operator for your next project? [Get in touch](https://chat.charmhub.io/charmhub/channels/charm-dev)!

## Contributing to this documentation

Documentation is an important part of this project, and we take the same open-source approach to the documentation as the code. As such, we welcome community contributions, suggestions and constructive feedback on our documentation. Our documentation is hosted on the [Charmhub forum](https://charmhub.io/irc-bridge/docs) to enable easy collaboration. Please use the "Help us improve this documentation" links on each documentation page to either directly change something you see that's wrong, ask a question, or make a suggestion about a potential change via the comments section.

If there's a particular area of documentation that you'd like to see that's missing, please [file a bug](https://github.com/canonical/irc-bridge-operator/issues).

---

For further details,
[see the charm's detailed documentation](https://charmhub.io/irc-bridge/docs).
