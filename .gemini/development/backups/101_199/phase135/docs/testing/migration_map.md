# Test Migration Map

## Core CRM Objects

- `test_contacts.py` -> `test/unit/crm/contacts/test_contacts.py`
- `test_lead_crud.py` -> `test/unit/crm/leads/test_crud.py`
- `test_crm.py` -> `test/unit/crm/shared/test_core_routes.py`
- `test_deletion_integrity.py` -> `test/unit/crm/shared/test_deletion_integrity.py`

## Search and Lookup

- `test_lookup_search_fix.py` -> `test/unit/search/test_lookup_search.py`
- `test_scoped_search.py` -> `test/unit/search/test_scoped_search.py`
- `test_search_suggestions.py` -> `test/unit/search/test_search_suggestions.py`

## Shared UI and Object Actions

- `test_batch_edit_ui.py` -> `test/unit/ui/shared/test_batch_edit_ui.py`
- `test_batch_save_logic.py` -> `test/unit/ui/shared/test_batch_save_logic.py`
- `test_pencil_unity.py` -> `test/unit/ui/shared/test_inline_edit_unity.py`
- `test_table_sorting_structure.py` -> `test/unit/ui/tables/test_table_sorting_structure.py`
- `test_ui.py` -> `test/unit/ui/shared/test_core_ui.py`
- `test_phase16.py` -> `test/unit/legacy/test_phase16.py`
- `test_phase18.py` -> `test/unit/legacy/test_phase18.py`

## Messaging

- `test_message_provider_factory.py` -> `test/unit/messaging/providers/test_factory.py`
- `test_message_providers.py` -> `test/unit/messaging/providers/test_providers.py`
- `test_message_template_list_view.py` -> `test/unit/messaging/templates/test_list_view.py`
- `test_message_template_save_fix.py` -> `test/unit/messaging/templates/test_save.py`
- `test_messaging_detailed.py` -> `test/unit/messaging/test_messaging_detailed.py`
- `test_messaging_router_template_subject.py` -> `test/unit/messaging/router/test_template_subject.py`
- `test_messaging_router_upload_validation.py` -> `test/unit/messaging/router/test_upload_validation.py`
- `test_send_message_assets.py` -> `test/unit/messaging/ui/test_send_message_assets.py`

## AI Agent

- `test_ai_agent_auto.py` -> `test/unit/ai_agent/backend/test_auto.py`
- `test_ai_agent_chat.py` -> `test/unit/ai_agent/backend/test_chat.py`
- `test_ai_agent_comprehensive_crud.py` -> `test/unit/ai_agent/backend/test_comprehensive_crud.py`
- `test_ai_agent_conversation_context.py` -> `test/unit/ai_agent/backend/test_conversation_context.py`
- `test_ai_agent_crud.py` -> `test/unit/ai_agent/backend/test_crud.py`
- `test_ai_agent_delete_confirmation.py` -> `test/unit/ai_agent/backend/test_delete_confirmation.py`
- `test_ai_agent_frontend_assets.py` -> `test/unit/ai_agent/frontend/test_assets.py`
- `test_ai_agent_intent_variations.py` -> `test/unit/ai_agent/backend/test_intent_variations.py`
- `test_ai_agent_message_template_visibility.py` -> `test/unit/ai_agent/backend/test_message_template_visibility.py`
- `test_ai_agent_pagination.py` -> `test/unit/ai_agent/backend/test_pagination.py`
- `test_ai_agent_reasoner.py` -> `test/unit/ai_agent/backend/test_reasoner.py`
- `test_ai_agent_recommend_mode.py` -> `test/unit/ai_agent/backend/test_recommend_mode.py`
- `test_ai_agent_reset.py` -> `test/unit/ai_agent/backend/test_reset.py`
- `test_ai_agent_selection_context.py` -> `test/unit/ai_agent/backend/test_selection_context.py`
- `test_ai_agent_send_message_context.py` -> `test/unit/ai_agent/backend/test_send_message_context.py`
- `test_ai_lead_debug.py` -> `test/unit/ai_agent/legacy/test_lead_debug.py`
- `test_ai_messaging_crud.py` -> `test/unit/ai_agent/backend/test_messaging_crud.py`
- `test_ai_opp_contact_crud.py` -> `test/unit/ai_agent/backend/test_opp_contact_crud.py`
- `test_ai_recommend_logic.py` -> `test/unit/ai_agent/backend/test_recommend_logic.py`

## Integration and Manual

- `integration/test_e2e_simulation.py` -> `integration/crm/test_e2e_simulation.py`
- `manual/ai_agent/*` stays under `manual/ai_agent/`
- `manual/tmp_system/*` stays under `manual/tmp_system/` until individually rewritten or retired
