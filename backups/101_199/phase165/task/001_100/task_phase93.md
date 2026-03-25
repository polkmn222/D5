# Phase 93 Task

## Context

Cloudinary-backed uploads are active, but the MMS dispatch payload still only forwards local `/static/...` image URLs to the provider layer.

## Goals

- Pass Cloudinary-hosted image URLs through the messaging dispatch path.
- Add regression coverage so both local and public attachment URLs can drive MMS previews.
- Verify a live Cloudinary-backed MMS send after the fix.
