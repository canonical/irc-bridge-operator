# How to troubleshoot IRC bridge issues

This section will help you troubleshoot various issues with ERC bridge.

## Issue where Synapse stops sending events to the IRC bridge

This section details the issue when Synapse stops sending events to the IRC bridge.

### Symptoms
- Synapse is unable to push `appservice` transactions to the IRC bridge.
- Synapse logs may indicate errors such as "Server not known" or
appservice-specific warnings.
- The database shows `appservice_stream_position` stuck at an old event, and
restarting Synapse does not resolve the issue.
- Logs from Synapse may contain warnings similar to:
  ```
  push_bulk to https://chat.example.com/irc threw exception(JSONDecodeError): Expecting value: line 1 column 1 (char 0)
  ```

### Root cause
The `appservice_stream_position` in the Synapse database can get stuck on a
problematic event, causing the `appservice` sender to break silently and stop
processing new events.

### Solution
1. **Back up the Synapse database**:
   Before making any changes, ensure you have a full backup of your Synapse
   database to prevent data loss.

   Find more details about the backup in [How to Backup and Restore](https://charmhub.io/synapse/docs/how-to-backup-and-restore).

2. **Update the `appservice_stream_position`**:
   Run the following SQL query to update the `appservice_stream_position`
   to the latest event:
   ```sql
   UPDATE appservice_stream_position
   SET stream_ordering = (SELECT MAX(stream_ordering) FROM events);
   ```

3. **Restart Synapse**:
   After executing the query, restart the Synapse service to apply the changes.

### Additional notes
- This solution skips the problematic event and allows Synapse to resume
sending events to the IRC bridge.
- If the issue persists, check the Synapse logs for additional errors or
misconfigurations.
- In this [IRC-Bridge issue](https://github.com/matrix-org/matrix-appservice-irc/issues/1222), you can find more details about the error.
