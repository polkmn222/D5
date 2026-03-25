import os
import httpx
from dotenv import load_dotenv
from backend.app.utils.error_handler import handle_agent_errors

load_dotenv()

CEREBRAS_API_KEY = os.getenv("CELEBRACE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class AIService:
    @staticmethod
    @handle_agent_errors
    async def generate_summary(description: str) -> str:
        if not description:
            return ""
        
        # Prefer Cerebras for fast real-time summaries as requested
        api_key = CEREBRAS_API_KEY
        base_url = "https://api.cerebras.ai/v1/chat/completions"
        model = "llama3.1-8b" # Standard fast model on Cerebras

        # Fallback to Groq if Cerebras is not configured
        if not api_key:
            api_key = GROQ_API_KEY
            base_url = "https://api.groq.com/openai/v1/chat/completions"
            model = "llama-3.3-70b-versatile"

        if not api_key:
            return "AI Summary unavailable (API Key missing)"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    base_url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": "You are a professional CRM assistant. Summarize the following customer description into a concise one-line summary (max 100 characters) in Korean if possible, or English if not."},
                            {"role": "user", "content": description}
                        ],
                        "max_tokens": 50
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    return f"AI Error: {response.status_code}"
        except Exception as e:
            return f"AI Service Error: {str(e)}"

# END FILE
