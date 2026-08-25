import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FORTYGUARD_API_KEY")

if not API_KEY:
    raise RuntimeError("FORTYGUARD_API_KEY was not found in .env")


# Hotspot from our real Heatmap result
latitude = 40.7144
longitude = -74.0030
temperature = 33.14

url = "https://api.fortyguard.com/v1/env_params"

headers = {
    "api-key": API_KEY,
    "Content-Type": "application/json",
}

payload = {
    "latitude": latitude,
    "longitude": longitude,
    "temperature": temperature,
    "date_time": {
        "start_date": "2024-07-15",
        "start_time": "14:00",
        "filter_type": 1
    }
}

response = requests.post(
    url,
    headers=headers,
    json=payload,
    timeout=60
)

print("Submit status code:", response.status_code)
print("Submit response:")
print(response.text)

response.raise_for_status()

activity_id = response.json()["data"]["activity_id"]

status_url = f"https://api.fortyguard.com/v1/status/{activity_id}"

print("\nActivity ID:", activity_id)

for attempt in range(120):

    status_response = requests.get(
        status_url,
        headers={"api-key": API_KEY},
        timeout=30
    )

    status_response.raise_for_status()

    status_data = status_response.json()
    data = status_data.get("data", {})
    status = data.get("status", "").lower()

    print(f"Attempt {attempt + 1}: {status}")

    if status in ("completed", "succeeded"):
        print("\n✅ ENVIRONMENTAL ANALYSIS COMPLETED")

        result = data.get("result", {})

        print("\nResult:")
        print(result)

        break

    if status in ("failed", "error"):
        print("\n❌ TASK FAILED")
        print(status_data)
        break

    time.sleep(5)

else:
    raise TimeoutError("Task did not complete within the polling window.")