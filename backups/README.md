# Backup Layout

Use grouped range folders under this directory so phase backups stay organized as the project grows.

## Rules

- Store each phase inside a range folder plus a dedicated phase folder.
- Use paths such as `001_100/phase36/` and `101_199/phase148/`.
- Do not create loose `phaseN/` folders directly under `backups/`.
- Keep non-phase historical folders such as `tmp_system/` or `vercel_render_legacy/` separate unless they are explicitly migrated later.

## Range Pattern

- `001_100`: phases 1 through 100
- `101_199`: phases 101 through 199
- `200_299`: phases 200 through 299
- Continue the same pattern for later ranges
