# Troubleshooting

## Issue: Synapse Stops Sending Events to the IRC Bridge

### Symptoms
- Synapse is unable to push appservice transactions to the IRC bridge.
- Synapse logs may indicate errors such as "Server not known" or
appservice-specific warnings.
- The database shows `appservice_stream_position` stuck at an old event, and
restarting Synapse does not resolve the issue.
- Logs from Synapse may contain warnings similar to:
  ```
  push_bulk to https://chat.example.com/irc threw exception(JSONDecodeError): Expecting value: line 1 column 1 (char 0)
  ```

### Root Cause
The `appservice_stream_position` in the Synapse database can get stuck on a
problematic event, causing the appservice sender to break silently and stop
processing new events.

### Solution
1. **Backup the Synapse Database**:
   Before making any changes, ensure you have a full backup of your Synapse
   database to prevent data loss.

2. **Update the `appservice_stream_position`**:
   Run the following SQL query to update the `appservice_stream_position`
   to the latest event:
   ```sql
   UPDATE appservice_stream_position
   SET stream_ordering = (SELECT MAX(stream_ordering) FROM events);
   ```

3. **Restart Synapse**:
   After executing the query, restart the Synapse service to apply the changes.

### Additional Notes
- This solution skips the problematic event and allows Synapse to resume
sending events to the IRC bridge.
- If the issue persists, verify Synapse logs for additional errors or
misconfigurations.
