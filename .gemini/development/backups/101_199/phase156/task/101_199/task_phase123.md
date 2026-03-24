# Phase 123 Task

## Context

`./run_crm.sh` fails from the terminal when multiple processes are bound to port 8000 because it treats a multi-line PID list as one invalid kill argument.

## Goals

- Make `run_crm.sh` handle one or many PIDs safely.
- Preserve the existing restart behavior for occupied ports.
- Verify the script no longer throws invalid `kill` argument errors.
