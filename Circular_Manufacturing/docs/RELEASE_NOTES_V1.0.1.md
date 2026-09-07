# V1.0.1 Hotfix — Windows SQLite Handle Lifecycle

V1.0.0 final Windows validation exposed a platform-layer portability defect.

## Root cause

`sqlite3.Connection` was used directly as a Python context manager. That
context manager commits or rolls back transactions but does **not** close the
underlying connection.

On Linux, deleting a still-open SQLite file is permitted, which allowed the
portable build-host diagnostics to pass. Windows correctly retained the file
lock and raised `WinError 32` when `TemporaryDirectory` attempted cleanup.

## Fix

Every `RunStore` operation now uses an explicit transactional connection
context that:

1. opens the SQLite connection;
2. yields it to the operation;
3. commits on success or rolls back on failure;
4. **always calls `Connection.close()` in `finally`**.

This applies to initialization, health, scenario CRUD, run persistence and
audit reads/writes.

## Regression evidence

A platform regression test instruments every SQLite connection and asserts
that every created connection receives an explicit close call.

The accepted Phase-10 computational core is unchanged.
