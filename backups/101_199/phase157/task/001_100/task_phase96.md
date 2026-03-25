# Phase 96 Task

## Context

Slack and Cloudinary verification are complete. The next step is enabling a real carrier-backed provider with the supplied Solapi credentials so D4 can send SMS/LMS/MMS beyond Slack dev/test mode.

## Goals

- Add a Solapi message provider using the documented HMAC auth flow.
- Support SMS, LMS, and MMS sends, including Solapi MMS file upload from either local or public image URLs.
- Wire provider selection through `MESSAGE_PROVIDER` while preserving existing `mock` and `slack` behavior.
- Record the required Solapi env vars, including the sender number and allowlisted IP note.
