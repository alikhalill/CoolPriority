import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FORTYGUARD_API_KEY")

if not API_KEY:
    raise RuntimeError("FORTYGUARD_API_KEY was not found in .env")

url = "https://api.fortyguard.com/v1/heatmap"

headers = {
    "api-key": API_KEY,
    "Content-Type": "application/json",
}

payload = {
    "polygon_aoi": {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-74.0170, 40.7050],
                        [-74.0030, 40.7050],
                        [-74.0030, 40.7180],
                        [-74.0170, 40.7180],
                        [-74.0170, 40.7050]
                    ]]
                }
            }
        ]
    },
    "date_time": {
        "start_date": "2024-07-15",
        "start_time": "14:00",
        "filter_type": 1
    },
    "granularity": 100
}

response = requests.post(
    url,
    headers=headers,
    json=payload,
    timeout=60
)

print("Status code:", response.status_code)
print("Response:")
print(response.text)




# Heatmap 
import time

activity_id = response.json()["data"]["activity_id"]

status_url = f"https://api.fortyguard.com/v1/status/{activity_id}"

for attempt in range(120):
    status_response = requests.get(
        status_url,
        headers={"api-key": API_KEY},
        timeout=30
    )

    print(f"Attempt {attempt + 1}")
    print("Status code:", status_response.status_code)

    status_data = status_response.json()
    print(status_data)

    if status_response.status_code != 200:
        break

    data = status_data.get("data", {})
    status = data.get("status", "").lower()

    if status in ("completed", "succeeded"):
        print("\n✅ TASK COMPLETED")
        print("RESULT:")
        result = data.get("result", {})
        map_data = result.get("map_data", {})

        features = map_data.get("features", [])

        print("\n✅ TASK COMPLETED")
        print("Number of tiles:", len(features))

        if features:
            temperatures = [
                f["properties"]["average_temperature"]
                for f in features
                if f.get("properties", {}).get("average_temperature") is not None
            ]

            hottest = max(features, key=lambda f: f["properties"]["average_temperature"])
            coolest = min(features, key=lambda f: f["properties"]["average_temperature"])

            print("Minimum temperature:", min(temperatures))
            print("Maximum temperature:", max(temperatures))
            print("Average temperature:", sum(temperatures) / len(temperatures))

            print("\n🔥 Hottest tile:")
            print(hottest["properties"])

            print("\n❄️ Coolest tile:")
            print(coolest["properties"])
        break

    if status in ("failed", "error"):
        print("\n❌ TASK FAILED")
        break

    print("⏳ Still processing...\n")
    time.sleep(5)
else:
    print("❌ Task did not complete within the polling window.")