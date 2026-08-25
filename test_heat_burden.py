import os
import json
import time

import requests
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("FORTYGUARD_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "FORTYGUARD_API_KEY was not found in .env"
    )


HEATMAP_URL = (
    "https://api.fortyguard.com/v1/heatmap"
)

STATUS_URL_BASE = (
    "https://api.fortyguard.com/v1/status"
)


# ============================================================
# Configuration
# ============================================================

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
                    [-74.0170, 40.7050],
                ]],
            },
        }
    ],
}

DATE = "2024-07-15"
START_TIME = "06:00"
END_TIME = "20:00"

FILTER_TYPE = 2
GRANULARITY = 100

THRESHOLD = 30.0
DIRECTION = "above"

POLL_INTERVAL = 5
MAX_ATTEMPTS = 120


HEADERS = {
    "api-key": API_KEY,
    "Content-Type": "application/json",
}


# ============================================================
# Submit one analytical Heatmap
# ============================================================

def submit_heatmap(
    analytic_type,
):
    payload = {
        "polygon_aoi": POLYGON_AOI,

        "date_time": {
            "start_date": DATE,
            "start_time": START_TIME,
            "end_time": END_TIME,
            "filter_type": FILTER_TYPE,
        },

        "granularity": GRANULARITY,

        "analytic_type": analytic_type,

        "threshold": THRESHOLD,

        "direction": DIRECTION,
    }

    print("\n" + "=" * 70)
    print(f"FORTYGUARD {analytic_type.upper()} TEST")
    print("=" * 70)

    print("\nPayload:")
    print(json.dumps(payload, indent=4))

    response = requests.post(
        HEATMAP_URL,
        headers=HEADERS,
        json=payload,
        timeout=60,
    )

    print(
        "\nSubmit status:",
        response.status_code,
    )

    print(
        "Submit response:"
    )

    print(response.text)

    response.raise_for_status()

    body = response.json()

    activity_id = (
        body
        .get("data", {})
        .get("activity_id")
    )

    if not activity_id:
        raise RuntimeError(
            "No activity_id returned."
        )

    return activity_id


# ============================================================
# Poll
# ============================================================

def wait_for_result(
    activity_id,
):
    url = (
        f"{STATUS_URL_BASE}/{activity_id}"
    )

    status_headers = {
        "api-key": API_KEY
    }

    for attempt in range(
        1,
        MAX_ATTEMPTS + 1,
    ):

        response = requests.get(
            url,
            headers=status_headers,
            timeout=30,
        )

        if response.status_code == 404:
            time.sleep(
                POLL_INTERVAL
            )
            continue

        if response.status_code == 429:
            print(
                "Rate limit reached. "
                "Waiting 10 seconds..."
            )

            time.sleep(10)
            continue

        response.raise_for_status()

        body = response.json()

        data = body.get(
            "data",
            {},
        )

        status = str(
            data.get(
                "status",
                "",
            )
        ).lower()

        print(
            f"Attempt {attempt}: {status}"
        )

        if status in (
            "completed",
            "succeeded",
            "success",
        ):
            return data.get(
                "result",
                {},
            )

        if status in (
            "failed",
            "failure",
            "error",
        ):
            raise RuntimeError(
                "FortyGuard task failed:\n"
                + json.dumps(
                    body,
                    indent=4,
                )
            )

        time.sleep(
            POLL_INTERVAL
        )

    raise TimeoutError(
        "Task did not complete."
    )


# ============================================================
# Inspect Result
# ============================================================

def inspect_result(
    analytic_type,
    result,
):
    print("\n" + "=" * 70)
    print(
        f"{analytic_type.upper()} RESULT"
    )
    print("=" * 70)

    print(
        "\nResult keys:"
    )

    print(
        list(
            result.keys()
        )
    )

    stats = result.get(
        "stats_data",
        {},
    )

    print(
        "\nStats data:"
    )

    print(
        json.dumps(
            stats,
            indent=4,
            ensure_ascii=False,
        )
    )

    map_data = result.get(
        "map_data",
        {},
    )

    features = map_data.get(
        "features",
        [],
    )

    print(
        "\nNumber of tiles:",
        len(features),
    )

    # --------------------------------------------------------
    # Show first 5 tile values
    # --------------------------------------------------------

    print(
        "\nFirst tile values:"
    )

    for feature in features[:5]:

        properties = feature.get(
            "properties",
            {},
        )

        print(
            properties
        )

    return {
        "analytic_type": analytic_type,
        "result": result,
    }


# ============================================================
# Main
# ============================================================

def main():

    outputs = []

    for analytic_type in (
        "exceedance",
        "persistence",
    ):

        activity_id = submit_heatmap(
            analytic_type
        )

        print(
            "\nActivity ID:",
            activity_id,
        )

        result = wait_for_result(
            activity_id
        )

        inspected = inspect_result(
            analytic_type,
            result,
        )

        inspected[
            "activity_id"
        ] = activity_id

        outputs.append(
            inspected
        )

    # --------------------------------------------------------
    # Save raw analytical results
    # --------------------------------------------------------

    output_file = (
        "heat_burden_results.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            outputs,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print("\n" + "=" * 70)
    print("HEAT BURDEN EXPERIMENT COMPLETED")
    print("=" * 70)

    print(
        f"\nSaved to: {output_file}"
    )


if __name__ == "__main__":
    main()