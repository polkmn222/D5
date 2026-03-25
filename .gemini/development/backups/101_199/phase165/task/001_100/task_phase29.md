# Task: Phase 29 - AI Agent UI Refinement & Multi-LLM Ensemble

## Objective
Enhance the AI Agent's stability and intelligence. Fix UI issues related to window state management (minimize, maximize, reset) and implement a Multi-LLM Ensemble backend using Cerebras, Groq, Gemini, and OpenAI. The ensemble will pick the best response based on a confidence score and provide full bilingual support for English and Korean.

## Sub-tasks
1. **Frontend (JS/HTML)**:
   - Rewrite `ai_agent.js` with explicit state tracking (`isAiAgentMinimized`, `isAiAgentMaximized`).
   - Implement `resetAiAgent()` to clear history and restore default window dimensions.
   - Update `ai_agent.html` close button to trigger a full reset.
2. **Backend (Python)**:
   - Install `openai` and `google-generativeai` SDKs.
   - Update `AiAgentService` to perform parallel async calls to Cerebras, Groq, Gemini, and OpenAI.
   - Implement an ensemble picker that selects the highest-scoring valid JSON response.
   - Update the system prompt to explicitly support and encourage Korean/English interactions.
3. **Verification**:
   - Verify UI button behavior and window stability.
   - Confirm ensemble execution through backend logging.
   - Test natural language queries in both languages.

## Completion Criteria
- AI Agent window functions smoothly across all states.
- The 'X' button resets the chat and UI to initial state.
- Backend utilizes all 4 API providers and picks the best response.
- Agent handles Korean and English queries natively.
- Phase 29 documentation is generated.