# Phase 130 Task

## Context

- Brand related cards are now aligned with the newer CRM pattern, and the remaining requested sequence is Models, Send, then Template.
- Model, Send, and Template detail pages still lack the same level of related-record coverage and shared related-card presentation.
- The next pass should keep the same Salesforce-style UI grammar and preserve read-only behavior where messaging records should not be edited from related flows.

## Goals

- Add Model related cards using the shared connected-record pattern.
- Add Send related cards and Template related cards with meaningful linked records and `View All` behavior.
- Support any needed related-flow query prefills so `New` actions only appear where the linked context can be carried safely.
