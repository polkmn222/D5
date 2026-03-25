# Phase 131 Task

## Context

- The Send list view still looks visually off compared with the other list pages, especially in the table surface and row action treatment.
- Message detail editing currently triggers an `Object type not supported` save failure, and related navigation between Send and Template records still needs verification.
- Several core CRM objects have blank lookup fields, which weakens Related tab coverage and makes cross-object navigation inconsistent.

## Goals

- Align the Send list table surface and row action button styling with the other object list views.
- Fix Send/Template related behavior and eliminate the unsupported-object save path.
- Populate missing lookup data where possible across Contacts, Opportunities, Brands, Models, Products, Assets, Sends, and Templates so Related tabs have dependable linked records.
- Add and run focused unit tests for the changed UI, routing, and save behavior.
