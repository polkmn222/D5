# Phase 123 Implementation

## Changes

- Updated `run_crm.sh` so port-occupying PIDs are collected as a space-separated list instead of a raw multi-line string.
- Fixed the restart logic to kill one or many PIDs safely without passing an invalid combined argument to `kill`.
- Kept the existing startup flow unchanged after the port cleanup step.

## Result

- Running `./run_crm.sh` from the terminal no longer fails with `arguments must be process or job IDs` when multiple listeners are reported on port 8000.
