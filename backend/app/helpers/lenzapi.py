import requests

LENS_API_KEY = "your_api_key_here"  # ← Replace with your real Lens.org API key
SEARCH_STRING = '"global software development" AND "project performance"'  # You can change this

url = "https://api.lens.org/scholarly/search"

headers = {
    "Authorization": f"Bearer {LENS_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "query": SEARCH_STRING,
    "size": 5,
    "include": ["title", "abstract"]
}

response = requests.post(url, headers=headers, json=payload)

if response.status_code == 200:
    results = response.json().get("data", [])
    for i, paper in enumerate(results, start=1):
        title = paper.get("title", "No title")
        abstract = paper.get("abstract", "No abstract available")
        print(f"\nResult {i}")
        print(f"Title: {title}")
        print(f"Abstract: {abstract}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
