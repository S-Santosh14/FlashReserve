# FlashReserve startup on Windows

These commands are for Git Bash, run from the project root. Open a separate
terminal for each process and leave it running. The `.venv` and the existing
root `.env` must already be configured. Do not start a second copy of a service
that is already running.

1. Standalone REST backend and Raft HTTP gateway (port 5000):

   ```bash
   ./.venv/Scripts/python.exe -m backend.main
   ```

2. LLM gRPC service (port 50060):

   ```bash
   ./.venv/Scripts/python.exe -m llm.llm_service
   ```

3. Raft node 1 (port 50051):

   ```bash
   ./.venv/Scripts/python.exe -m backend.raft.node_runner --node node-1
   ```

4. Raft node 2 (port 50052):

   ```bash
   ./.venv/Scripts/python.exe -m backend.raft.node_runner --node node-2
   ```

5. Raft node 3 (port 50053):

   ```bash
   ./.venv/Scripts/python.exe -m backend.raft.node_runner --node node-3
   ```

6. Raft node 4 (port 50054):

   ```bash
   ./.venv/Scripts/python.exe -m backend.raft.node_runner --node node-4
   ```

7. Raft node 5 (port 50055):

   ```bash
   ./.venv/Scripts/python.exe -m backend.raft.node_runner --node node-5
   ```

8. Raft node 6 (port 50056):

   ```bash
   ./.venv/Scripts/python.exe -m backend.raft.node_runner --node node-6
   ```

9. Raft node 7 (port 50057):

   ```bash
   ./.venv/Scripts/python.exe -m backend.raft.node_runner --node node-7
   ```

10. Streamlit frontend (port 8502):

    ```bash
    ./.venv/Scripts/python.exe -m streamlit run app.py --server.headless true --server.port 8502
    ```

The listed ports assume the defaults or matching `.env` settings. Start the
nodes, backend and LLM before using the frontend at
http://127.0.0.1:8502. Stop an individually started process with `Ctrl+C` in
its own terminal.

The sign-in / create-account screen shows live status for all Raft nodes,
including leader, quorum, database, and log information. This monitor is
available only before sign-in and is not shown on authenticated pages. Its
compact node table reports the leader's actual per-follower replication ACK
state (ACKNOWLEDGED, PENDING, FAILED, CATCHING UP, or UNREACHABLE); detailed
log, commit, applied, and recovery data remains in node details and backend
status.

Each node logs a periodically sampled cluster table. Set the optional
`RAFT_STATUS_INTERVAL` environment variable to a positive number of seconds
(default 15) to adjust its frequency; restart the node after changing it.
An unavailable observation means that node's status RPC did not complete,
not necessarily that its process has stopped. Peer roles and indexes are
sampled reports, not a consensus decision. Leader replication progress is
the local leader's observed `nextIndex`, `matchIndex`, latest RPC result, and
error. Nodes use term-scoped, randomized election timeout ranges that rotate
their relative order across terms; no node is assigned permanent priority.

The existing `start_all_raft_nodes.bat` and `stop_raft_nodes.bat` cover only
Raft nodes, not all ten services. Their PID records may be stale and they are
not a reliable replacement for a full service manager. A verified `start_all`
and `stop_all` for all services is not yet available.

## Checking a port conflict

If a port is already in use, inspect its owner first. For example, for node 1:

```bash
powershell.exe -NoProfile -Command '$c = Get-NetTCPConnection -LocalPort 50051 -State Listen -ErrorAction SilentlyContinue; $c | ForEach-Object { Get-CimInstance Win32_Process -Filter "ProcessId = $($_.OwningProcess)" | Select-Object ProcessId,ParentProcessId,CommandLine | Format-List }'
```

Replace `50051` with the conflicting port. A listener is not proof of Raft
health: check `http://127.0.0.1:5000/api/raft/status` as well. If the owner
is a FlashReserve process you started, stop it from its terminal with
`Ctrl+C`. Do not stop a process solely because it occupies a port.

## Database and notification limitations

Normal Mode uses the configured standalone database, normally `flashreserve`.
Each Raft node requires its own `RAFT_NODE_<n>_MONGO_URI` and uses its
`RAFT_NODE_<n>_DATABASE_NAME`. The seven default database names are
`flashreserve_raft_node1` through `flashreserve_raft_node7`.

The REST gateway uses the standalone account store for authentication. Raft
events are read from and written to Raft databases; the standalone event
catalogue is not copied into Raft Mode. The shared standalone account store and
notification outbox mean identity and email delivery are not database-isolated
between modes. Booking and cancellation replication, follower recovery, and
leader election were tested against Atlas through the Python Raft gateway
directly, not through the frontend or authenticated HTTP. Crash-safe
persistence and a booking after leader failure have not been verified. See
`docs/architecture-audit.md` for the test scope and remaining limitations.
After a successful mock
payment or cancellation, the backend queues an
email using the signed-in account's address. The queue is stored in the
standalone database for both modes; a backend restart is needed after changes
to SMTP settings or the notification code. See the README for retry behavior
and known delivery limitations. SMTP accepted a Normal Mode booking and
cancellation test; inbox delivery and Raft email delivery remain unverified.
