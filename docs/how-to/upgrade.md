# How to upgrade
Before upgrading make sure to backup the postgresql database by following the [official documentation](https://canonical-charmed-postgresql.readthedocs-hosted.com/14/how-to/back-up-and-restore/create-a-backup/)

Once that's done, you can upgrade the charm by running the following command:
```
juju refresh irc-bridge
```