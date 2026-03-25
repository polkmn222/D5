import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/ask-agent/chat"

def test_query(query):
    print(f"\n--- Testing Query: '{query}' ---")
    try:
        response = requests.post(BASE_URL, json={"query": query}, timeout=15)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Intent: {data.get('intent')}")
            print(f"Text: {data.get('text')}")
            if "results" in data:
                print(f"Results Found: {len(data['results'])}")
            if "sql" in data:
                print(f"SQL Generated: {data['sql']}")
        else:
            print(f"Error Response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    queries = [
        "hi",
        "show me some leads",
        "list my opportunities",
        "who are you?",
        "create a contact named Test User",
        "invalid_request_xyz"
    ]
    for q in queries:
        test_query(q)
