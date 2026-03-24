import requests
import json

url = "http://127.0.0.1:8000/api/ask-agent/chat"
payload = {"query": "hi"}
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response JSON: {response.json()}")
    except:
        print(f"Response Text (not JSON): {response.text[:500]}")
except Exception as e:
    print(f"Request failed: {e}")
