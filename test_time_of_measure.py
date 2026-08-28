import json
import time
from pathlib import Path

import requests


# ============================================================
# CONFIG
# ============================================================

API_URL = (
    "https://api.fortyguard.com/v1/heatmap"
)

STATUS_URL = (
    "https://api.fortyguard.com/v1/status/"
)

API_KEY = None

# Load the same API key that your project already uses.
# DO NOT hard-code the real key into this file.

from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv(
    "FORTYGUARD_API_KEY"
)

if not API_KEY:

    raise RuntimeError(
        "FORTYGUARD_API_KEY was not found in .env"
    )


# ============================================================
# SAME VALIDATED PILOT AOI
# ============================================================

PILOT_POLYGON = {
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
                    [-74.0170, 40.7050],
                ]],
            },
        }
    ],
}


# ============================================================
# PAYLOAD
# ============================================================

payload = {

    "polygon_aoi":
        PILOT_POLYGON,

    "date_time": {

        "start_date":
            "2024-07-15",

        "start_time":
            "06:00",

        "end_time":
            "20:00",

        "filter_type":
            2,
    },

    "granularity":
        100,

    "analytic_type":
        "time_of_measure",
}


# ============================================================
# SUBMIT
# ============================================================

headers = {
    "api-key":
        API_KEY,

    "Content-Type":
        "application/json",
}


print("=" * 70)
print(
    "FORTYGUARD TIME OF MEASURE"
)
print("=" * 70)


response = requests.post(
    API_URL,
    headers=headers,
    json=payload,
    timeout=60,
)

response.raise_for_status()

submit_data = response.json()

print(
    "\nSubmit status:",
    response.status_code,
)

print(
    "Submit response:",
    json.dumps(
        submit_data,
        indent=2,
    ),
)


activity_id = (
    submit_data
    .get("data", {})
    .get("activity_id")
)

if not activity_id:

    raise RuntimeError(
        "No activity_id returned."
    )


print(
    "\nActivity ID:",
    activity_id
)


# ============================================================
# POLL
# ============================================================

status_url = (
    STATUS_URL
    + activity_id
)


result = None

for attempt in range(
    1,
    61,
):

    status_response = requests.get(
        status_url,
        headers={
            "api-key":
                API_KEY
        },
        timeout=60,
    )

    status_response.raise_for_status()

    status_data = (
        status_response
        .json()
    )

    activity_data = (
        status_data
        .get("data", {})
    )

    status = activity_data.get(
        "status"
    )

    print(
        f"Attempt {attempt}: {status}"
    )

    if status == "Completed":

        result = (
            activity_data
            .get("result")
        )

        break

    if status == "Failed":

        raise RuntimeError(
            "FortyGuard activity failed."
        )

    time.sleep(3)


if result is None:

    raise TimeoutError(
        "FortyGuard activity did not complete."
    )


# ============================================================
# SAVE
# ============================================================

output_file = (
    "time_of_measure_result.json"
)

with open(
    output_file,
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        result,
        file,
        indent=4,
        ensure_ascii=False,
    )


print(
    "\nSaved to:",
    output_file
)

print(
    "\nDone."
)