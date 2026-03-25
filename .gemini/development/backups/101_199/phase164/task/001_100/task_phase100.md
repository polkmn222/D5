# Phase 100 Task

## Context

- Contact and Opportunity pinning surfaced a frontend JSON parsing failure in the browser.
- Brands and Models still used the older simple list-table UI while the other CRM objects already used the newer saved list-view workflow.

## Goals

- Make pin failures degrade cleanly and support stale builtin ids.
- Extend the Salesforce-style customizable list-view system to Brands and Models.
- Add unit tests for the new Brand and Model list-view behavior.
