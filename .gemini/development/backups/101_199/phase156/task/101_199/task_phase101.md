# Phase 101 Task

## Context

- Opening CRM tabs like Leads, Contacts, and Opportunities triggered `Agent Error: cannot access local variable 'view_id' where it is not associated with a value`.
- Testing docs also needed to explicitly include saved list-view checks in both unit-test guidance and manual regression guidance.

## Goals

- Fix the `view_id` runtime error first so list pages load again.
- Keep pin support working for stale builtin ids.
- Update markdown and manual regression guidance to include saved list-view coverage.
