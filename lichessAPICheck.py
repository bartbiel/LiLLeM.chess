import requests

url = "https://lichess.org/api/games/user/bielbart77"
params = {
    "max": 5,
    "perfType": "rapid",
    "pgnInJson": True
}

resp = requests.get(url, params=params, stream=True)

print("Status:", resp.status_code)
print("First 500 chars:\n", resp.text[:500])
