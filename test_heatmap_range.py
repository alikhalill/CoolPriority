import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FORTYGUARD_API_KEY")

if not API_KEY:
    raise RuntimeError("FORTYGUARD_API_KEY was not found in .env")

# ============================================================
# Configuration
# ============================================================

HEATMAP_URL = "https://api.fortyguard.com/v1/heatmap"
STATUS_URL_BASE = "https://api.fortyguard.com/v1/status"

START_DATE = "2024-07-15"
START_TIME = "06:00"
END_TIME = "20:00"

FILTER_TYPE = 2
GRANULARITY = 100

# Same small Manhattan-area polygon we already tested
POLYGON_AOI = {
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
}

SUBMIT_HEADERS = {
    "api-key": API_KEY,
    "Content-Type": "application/json",
}

STATUS_HEADERS = {
    "api-key": API_KEY,
}

# ============================================================
# Submit Heatmap
# ============================================================

def submit_heatmap():
    payload = {
        "polygon_aoi": POLYGON_AOI,
        "date_time": {
            "start_date": START_DATE,
            "start_time": START_TIME,
            "end_time": END_TIME,
            "filter_type": FILTER_TYPE,
        },
        "granularity": GRANULARITY,
    }

    print("=" * 70)
    print("FORTYGUARD HEATMAP TIME-RANGE TEST")
    print("=" * 70)

    print("\nPayload:")
    print(json.dumps(payload, indent=4))

    try:
        response = requests.post(
            HEATMAP_URL,
            headers=SUBMIT_HEADERS,
            json=payload,
            timeout=60,
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Heatmap submission failed: {exc}"
        ) from exc

    print("\nSubmit status code:", response.status_code)
    print("Submit response:")
    print(response.text)

    # Show validation errors clearly
    if response.status_code >= 400:
        return None

    response.raise_for_status()

    data = response.json()

    activity_id = data.get("data", {}).get("activity_id")

    if not activity_id:
        raise RuntimeError(
            "No activity_id found in successful submission."
        )

    return activity_id


# ============================================================
# Poll Status
# ============================================================

def wait_for_result(activity_id):
    status_url = f"{STATUS_URL_BASE}/{activity_id}"

    print("\nActivity ID:", activity_id)

    for attempt in range(1, 121):

        try:
            response = requests.get(
                status_url,
                headers=STATUS_HEADERS,
                timeout=30,
            )
        except requests.RequestException as exc:
            print(f"Status request failed: {exc}")
            time.sleep(5)
            continue

        print(
            f"\nAttempt {attempt}/120 | "
            f"HTTP {response.status_code}"
        )

        if response.status_code == 404:
            print("Activity not available yet.")
            time.sleep(5)
            continue

        if response.status_code == 429:
            print("Rate limit reached. Waiting 10 seconds...")
            time.sleep(10)
            continue

        response.raise_for_status()

        status_data = response.json()
        data = status_data.get("data", {})
        status = str(data.get("status", "")).lower()

        print("Status:", status)

        if status in ("completed", "succeeded"):
            print("\n✅ HEATMAP COMPLETED")
            return data.get("result", {})

        if status in ("failed", "error"):
            print("\n❌ HEATMAP FAILED")
            print(json.dumps(status_data, indent=4))
            return None

        time.sleep(5)

    raise TimeoutError(
        "Heatmap task did not finish within the polling window."
    )


# ============================================================
# Analyze Result
# ============================================================

def analyze_result(result):
    print("\n" + "=" * 70)
    print("RESULT STRUCTURE")
    print("=" * 70)

    print("Top-level result keys:")
    print(list(result.keys()))

    # --------------------------------------------------------
    # map_data
    # --------------------------------------------------------

    map_data = result.get("map_data")

    if not map_data:
        print("\nNo map_data returned.")
        return

    print("\nmap_data type:")
    print(map_data.get("type"))

    features = map_data.get("features", [])

    print("Number of features:", len(features))

    if not features:
        return

    # --------------------------------------------------------
    # Inspect first feature
    # --------------------------------------------------------

    print("\nFirst feature:")
    print(
        json.dumps(
            features[0],
            indent=4
        )
    )

    # --------------------------------------------------------
    # Temperature statistics from tiles
    # --------------------------------------------------------

    temperatures = []

    for feature in features:
        properties = feature.get("properties", {})
        value = properties.get("average_temperature")

        if isinstance(value, (int, float)):
            temperatures.append(value)

    if temperatures:
        print("\n" + "=" * 70)
        print("SPATIAL TEMPERATURE SUMMARY")
        print("=" * 70)

        print("Tile count:", len(temperatures))
        print("Minimum:", min(temperatures))
        print("Maximum:", max(temperatures))
        print(
            "Average:",
            round(sum(temperatures) / len(temperatures), 4)
        )

    # --------------------------------------------------------
    # Check for any temporal fields
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("CHECKING FOR TEMPORAL DATA")
    print("=" * 70)

    temporal_keys = []

    for key in result.keys():
        lowered = key.lower()

        if any(
            word in lowered
            for word in (
                "time",
                "timestamp",
                "hour",
                "series",
                "forecast",
                "history",
                "stats",
            )
        ):
            temporal_keys.append(key)

    if temporal_keys:
        print("Possible temporal/statistical fields:")
        for key in temporal_keys:
            print("-", key)

    else:
        print(
            "No obvious temporal field found at the top level."
        )

    # --------------------------------------------------------
    # Print stats_data if available
    # --------------------------------------------------------

    if "stats_data" in result:
        print("\n" + "=" * 70)
        print("STATS DATA")
        print("=" * 70)

        print(
            json.dumps(
                result["stats_data"],
                indent=4
            )
        )


# ============================================================
# Main
# ============================================================

def main():

    activity_id = submit_heatmap()

    # Request may be rejected immediately
    if not activity_id:
        print(
            "\nNo task was created. "
            "The endpoint may not support this time-range request."
        )
        return

    result = wait_for_result(activity_id)

    if result is None:
        return

    # Save raw result
    with open(
        "heatmap_time_range_result.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            result,
            file,
            indent=4,
            ensure_ascii=False
        )

    analyze_result(result)

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)

    print(
        "\nSaved raw result to:"
        "\nheatmap_time_range_result.json"
    )


if __name__ == "__main__":
    main()