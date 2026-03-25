# Task: Phase 37 - Automotive Object CRUD & Conversational AI

## Objective
Verify and standardize the CRUD (Create, Read, Update, Delete) functionality for automotive-specific objects: Assets (VIN-based), Products, Brands (Vehicle Specifications), and Models. Enhance the AI Agent's conversational flow for these objects and ensure robust error handling and system backups.

## Sub-tasks
1. **Source Backup**: Create a full backup of automotive services and AI logic in `.gemini/development/backups/phase37/`.
2. **Standardize Automotive Services**:
   - Update `AssetService.create_asset` to handle optional names and use VIN as a fallback.
   - Verify `ProductService`, `VehicleSpecService`, and `ModelService` for operational readiness.
3. **AI Agent Intent Extension**:
   - Add `CREATE asset` support to `AiAgentService._execute_intent`.
   - Update the system prompt to explicitly guide users through mandatory fields for Assets (VIN), Brands (Name), Models (Name, Brand), and Products (Name, Brand).
4. **Validation via Testing**:
   - Run baseline automotive tests in `test_phase18.py` after fixing SQLite path issues.
   - Create and run `test_ai_agent_auto.py` to verify conversational flows for Asset registration and Brand/Product querying.
5. **Ensemble AI Check**: Confirm that natural language queries like "Search Tesla brand" or "Register new car" trigger the correct conversational paths in both Korean and English.

## Completion Criteria
- Comprehensive backup for Phase 37 is created.
- Automotive CRUD operations pass 100% in unit tests.
- AI Agent correctly identifies missing info for automotive objects and asks for it.
- Phase 37 documentation is generated.