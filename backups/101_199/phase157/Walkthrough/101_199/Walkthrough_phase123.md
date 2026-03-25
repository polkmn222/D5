# Phase 123 Walkthrough

## Result

- `./run_crm.sh` now handles occupied port `8000` cleanly, even if `lsof` returns multiple PIDs.
- The invalid `kill` argument error is gone.

## Validation

- `bash -n run_crm.sh`
- `bash run_crm.sh`
- Result:
  - startup reaches `Waiting for server startup...`
  - `http://127.0.0.1:8000/docs` -> `200`
  - output does not contain `arguments must be process or job IDs`
