import requests
import json

# Test the backend API
url = "http://localhost:8000/api/analyze/text"
payload = {
    "text": "Should we invest in renewable energy?",
    "show_updates": False
}

print("Testing backend API...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("\nSending request...")

try:
    response = requests.post(url, json=payload, timeout=60)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        print("\n✅ SUCCESS! Backend is working correctly.")
        data = response.json()
        print(f"\nResponse preview:")
        print(f"- Success: {data.get('success')}")
        print(f"- Factors count: {len(data.get('factors', []))}")
        print(f"- Has final_report: {'final_report' in data}")
        print(f"- Has debates: {'debates' in data}")
    else:
        print(f"\n❌ ERROR: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
