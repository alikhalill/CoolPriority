import json
import os
import time

import requests
from dotenv import load_dotenv


# ============================================================
# FortyGuard - Environmental Validation
# ============================================================

load_dotenv()

API_KEY = os.getenv("FORTYGUARD_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "FORTYGUARD_API_KEY was not found in .env"
    )


# ============================================================
# Configuration
# ============================================================

INPUT_FILE = "hotspot_environment_targets.json"
OUTPUT_FILE = "hotspot_environment_results.json"

ENV_PARAMS_URL = "https://api.fortyguard.com/v1/env_params"
STATUS_URL_BASE = "https://api.fortyguard.com/v1/status"

DATE = "2024-07-15"
TIME = "14:00"

POLL_INTERVAL_SECONDS = 5
MAX_POLL_ATTEMPTS = 120


SUBMIT_HEADERS = {
    "api-key": API_KEY,
    "Content-Type": "application/json",
}

STATUS_HEADERS = {
    "api-key": API_KEY,
}


# ============================================================
# Load targets
# ============================================================

def load_targets():
    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        targets = json.load(file)

    if not isinstance(targets, list):
        raise RuntimeError(
            f"{INPUT_FILE} must contain a list."
        )

    return targets


# ============================================================
# Submit Environmental Analysis
# ============================================================

def submit_environment_analysis(target):

    payload = {
        "latitude": target["latitude"],
        "longitude": target["longitude"],

        # IMPORTANT:
        # Use the temperature associated with THIS tile,
        # not the old fixed 33.14°C value.
        "temperature": target["average_temperature"],

        "date_time": {
            "start_date": DATE,
            "start_time": TIME,
            "filter_type": 1,
        },

        "analysis": [
            "heat_index_celsius",
            "apparent_temperature_celsius",
            "wet_bulb_temperature_celsius",
            "relative_humidity_percent",
            "air_quality:idx",
        ],
    }

    response = requests.post(
        ENV_PARAMS_URL,
        headers=SUBMIT_HEADERS,
        json=payload,
        timeout=60,
    )

    print(
        "Submit status code:",
        response.status_code
    )

    print(
        "Submit response:"
    )

    print(response.text)

    response.raise_for_status()

    response_json = response.json()

    activity_id = (
        response_json
        .get("data", {})
        .get("activity_id")
    )

    if not activity_id:
        raise RuntimeError(
            "activity_id was not returned."
        )

    return activity_id


# ============================================================
# Poll Task
# ============================================================

def wait_for_completion(activity_id):

    status_url = (
        f"{STATUS_URL_BASE}/{activity_id}"
    )

    for attempt in range(
        1,
        MAX_POLL_ATTEMPTS + 1
    ):

        response = requests.get(
            status_url,
            headers=STATUS_HEADERS,
            timeout=30,
        )

        # Temporary 404
        if response.status_code == 404:
            print(
                "Activity not available yet."
            )

            time.sleep(
                POLL_INTERVAL_SECONDS
            )

            continue

        # Rate limiting
        if response.status_code == 429:
            print(
                "Rate limit reached."
            )

            time.sleep(10)

            continue

        response.raise_for_status()

        status_json = response.json()

        data = status_json.get(
            "data",
            {}
        )

        status = str(
            data.get(
                "status",
                ""
            )
        ).lower()

        print(
            f"Attempt {attempt}: {status}"
        )

        # Completed
        if status in (
            "completed",
            "succeeded",
            "success",
        ):

            return data.get(
                "result",
                {}
            )

        # Failed
        if status in (
            "failed",
            "failure",
            "error",
        ):

            raise RuntimeError(
                "FortyGuard task failed:\n"
                +
                json.dumps(
                    status_json,
                    indent=4,
                )
            )

        time.sleep(
            POLL_INTERVAL_SECONDS
        )

    raise TimeoutError(
        f"Activity {activity_id} "
        "did not complete in time."
    )


# ============================================================
# Extract Environmental Data
# ============================================================

def extract_environment_data(result):

    locations = result.get(
        "locations",
        []
    )

    if not locations:
        raise RuntimeError(
            "No locations returned."
        )

    location = locations[0]

    parameters = location.get(
        "parameters",
        {}
    )

    def get_first_value(name):

        values = parameters.get(name)

        if isinstance(values, list):

            if values:
                return values[0]

            return None

        return values

    return {
        "latitude": location.get("lat"),
        "longitude": location.get("lon"),
        "elevation": location.get("elevation"),

        "temperature":
            location.get("temperature"),

        "heat_index_celsius":
            get_first_value(
                "heat_index_celsius"
            ),

        "apparent_temperature_celsius":
            get_first_value(
                "apparent_temperature_celsius"
            ),

        "wet_bulb_temperature_celsius":
            get_first_value(
                "wet_bulb_temperature_celsius"
            ),

        "relative_humidity_percent":
            get_first_value(
                "relative_humidity_percent"
            ),

        "air_quality_idx":
            get_first_value(
                "air_quality:idx"
            ),
    }


# ============================================================
# Main
# ============================================================

def main():

    targets = load_targets()

    print("=" * 70)
    print("FORTYGUARD ENVIRONMENTAL VALIDATION")
    print("=" * 70)

    print(
        f"\nTargets loaded: {len(targets)}"
    )

    results = []

    # ========================================================
    # Process each selected tile
    # ========================================================

    for index, target in enumerate(
        targets,
        start=1
    ):

        print("\n" + "=" * 70)

        print(
            f"TARGET {index}/{len(targets)}"
        )

        print("=" * 70)

        print(
            "Group:",
            target["group"]
        )

        print(
            "Tile ID:",
            target["tile_id"]
        )

        print(
            "Latitude:",
            target["latitude"]
        )

        print(
            "Longitude:",
            target["longitude"]
        )

        print(
            "Heatmap Average Temperature:",
            target["average_temperature"]
        )

        print(
            "Cooling Priority Score:",
            target[
                "cooling_priority_score"
            ]
        )

        # ----------------------------------------------------
        # Submit
        # ----------------------------------------------------

        activity_id = (
            submit_environment_analysis(
                target
            )
        )

        print(
            "\nActivity ID:",
            activity_id
        )

        # ----------------------------------------------------
        # Wait
        # ----------------------------------------------------

        result = (
            wait_for_completion(
                activity_id
            )
        )

        # ----------------------------------------------------
        # Extract
        # ----------------------------------------------------

        environmental_data = (
            extract_environment_data(
                result
            )
        )

        record = {

            "group":
                target["group"],

            "tile_id":
                target["tile_id"],

            "location": {
                "latitude":
                    target["latitude"],

                "longitude":
                    target["longitude"],
            },

            "heatmap_data": {

                "average_temperature":
                    target[
                        "average_temperature"
                    ],

                "minimum_temperature":
                    target[
                        "min_temperature"
                    ],

                "maximum_temperature":
                    target[
                        "max_temperature"
                    ],

                "thermal_range":
                    target[
                        "thermal_range"
                    ],

                "cooling_priority_score":
                    target[
                        "cooling_priority_score"
                    ],

                "priority_label":
                    target[
                        "priority_label"
                    ],
            },

            "environmental_data":
                environmental_data,

            "activity_id":
                activity_id,
        }

        results.append(record)

        print(
            "\n✅ Environmental data collected."
        )

        print(
            json.dumps(
                environmental_data,
                indent=4,
            )
        )

    # ========================================================
    # Save
    # ========================================================

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            results,
            file,
            indent=4,
            ensure_ascii=False,
        )

    # ========================================================
    # Comparison
    # ========================================================

    print("\n" + "=" * 70)
    print("TOP VS BOTTOM COMPARISON")
    print("=" * 70)

    for record in results:

        env = record[
            "environmental_data"
        ]

        print(
            f"\n"
            f"{record['group']:10s} | "
            f"Tile {record['tile_id']:>3} | "
            f"Priority="
            f"{record['heatmap_data']['cooling_priority_score']:6.2f} | "
            f"HeatIndex="
            f"{env['heat_index_celsius']} | "
            f"Apparent="
            f"{env['apparent_temperature_celsius']} | "
            f"WetBulb="
            f"{env['wet_bulb_temperature_celsius']} | "
            f"Humidity="
            f"{env['relative_humidity_percent']} | "
            f"AQI="
            f"{env['air_quality_idx']}"
        )

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)

    print(
        f"\nSaved results to:"
        f"\n{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()