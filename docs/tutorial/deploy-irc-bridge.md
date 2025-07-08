# Deploy IRC bridge

In this tutorial, we will deploy IRC Bridge, add configurations and integrate it
with other charms to set up a working Matrix application.

## Requirements

* A working station, e.g., a laptop, with amd64 architecture.
<!-- vale off -->
* Juju 3 installed and bootstrapped to a LXD and MicroK8s controller. You can accomplish
<!-- vale on -->
this process by using a [Multipass](https://multipass.run/) VM as outlined in this guide: [Set up / Tear down your test environment](https://canonical-juju.readthedocs-hosted.com/en/3.6/user/howto/manage-your-deployment/manage-your-deployment-environment/#set-things-up)
* [Synapse charm](https://charmhub.io/synapse) deployed. Refer to the [Synapse Getting Started](https://charmhub.io/synapse/docs/tutorial-getting-started) tutorial for step-by-step instructions.

:warning: When using a Multipass VM, make sure to replace IP addresses with the
VM IP in steps that assume you're running locally. To get the IP address of the
Multipass instance run ```multipass info my-juju-vm```.


### Set up a tutorial model

To manage resources effectively and to separate this tutorial's workload from
your usual work, create a new model using the following command.

```
juju add-model irc-bridge-tutorial
```

### Deploy IRC bridge

```
juju deploy irc-bridge --channel edge
```

The tutorial uses the edge channel to get the latest updates on the
Matrix-Auth library.

### Configure IRC bridge

IRC Bridge has two mandatory configurations:

- `bridge_admins`: Matrix users that will be Bridge administrators.
- `bot_nickname`: nickname that will be used for creating the Bridge user.

Run the following command to set them.

```
juju configure irc-bridge bridge_admins=admin:example.com bot_nickname=ircappservice
```

:warning: `example.com` refers to the Synapse home server. If you used a different
one, update it accordingly.

### Deploy and integrate PostgreSQL

IRC Bridge requires a PostgreSQL database.

Run the following commands to deploy PostgreSQL charm and relate it to the IRC
Bridge charm.

```
juju deploy postgresql-k8s --channel 14/stable
juju integrate irc-bridge postgresql
```

### Deploy and integrate HAProxy

Synapse needs to communicate with IRC Bridge via an URL. The HAProxy charm will
be used as a proxy to expose the IRC bridge application.

Run the following command to deploy HAProxy and Self Signed Certificates.

```
juju deploy haproxy --channel 2.8/edge
juju deploy self-signed-certificates
juju integrate haproxy self-signed-certificates
juju integrate irc-bridge haproxy
```

### Switch to Synapse in MicroK8s controller

Switch to the MicroK8s controller.

```
juju switch microk8s-localhost
```

:warning: `microk8s-localhost` is the MicroK8s controller.

The command `juju controllers` list all the existing controllers in the environment.

### Create the bridge admin user

The user set in the `bridge_admins` configuration should be created in Synapse and will be used
for managing the bridge.

```
juju run synapse/0 register-user username=admin admin=yes
```

Save the password since it will be used in further steps.

### Create an offer

Since IRC Bridge is running in a different model, the integration between them
should be done via an [Offer](https://canonical-juju.readthedocs-hosted.com/en/latest/user/reference/offer/#offer).

The following command will expose the Matrix Auth endpoint, allowing other
applications to integrate with it.

```
juju offer synapse:matrix-auth
```

### Integrate IRC bridge with Synapse

Now that the user used by IRC is created and the offer is available, change it
back to the LXD controller to integrate IRC Bridge and Synapse.

```
juju switch localhost-localhost
```

:warning: `localhost-localhost` is the LXD controller.

The command `juju controllers` list all the existing controllers in the environment.

```
juju integrate irc-bridge microk8s-localhost:admin/synapse.matrix-auth
```

### Check health endpoint

The IRC Bridge charm will configure the IRC Bridge once the integration is in
place. Check if the charm is active and idle using `juju status` command.

Then, find the HAProxy unit IP address and check if the /health endpoint returns
"OK". This indicates that the IRC Bridge is active.

```
curl https://<HAProxy unit IP address>/irc-bridge-tutorial-irc-bridge/health
```

### Interact with the bridge

Access Synapse via Element with the admin user created previously.

To interact with the Bridge, you can invite the user `ircappservice` to a room or sent a message.

Send a message to the user `ircappservice`. If a warning shows up, ignore and proceed.

The Bridge will show a help menu with all the options available. Try the following to guarantee
that the bridge is working.

```
!bridgeversion
```

To check all available options, send the following command:

```
!help
```

Screenshot example:

![irc-screenshot|690x575](upload://p4AjA75vPFwTcKWKWrzS25eFWEG.jpeg)

### Join a IRC channel

You can send a message to the user `ircappservice` like `!join #python` and
this will be interpreted as a command to join the #python channel.

After this, you can join the room python that corresponds to the IRC python channel.

## Clean up the environment

Well done! You've successfully completed the Deploy IRC Bridge tutorial.
To remove the model environment you created during this tutorial,
use the following command.

```
juju destroy-model irc-bridge-tutorial
```

Refer to the "Clean up the environment" step in [Synapse Getting Started](https://charmhub.io/synapse/docs/tutorial-getting-started#p-29229-clean-up-the-environment) tutorial for detailed instructions on how to clean up the Synapse environment.
