from __future__ import annotations

import os
import time
from typing import Any

import requests
from dotenv import load_dotenv


# ============================================================
# CONFIG
# ============================================================

HEATMAP_URL = (
    "https://api.fortyguard.com/v1/heatmap"
)

STATUS_URL = (
    "https://api.fortyguard.com/v1/status"
)


# ============================================================
# LOAD API KEY
# ============================================================

load_dotenv()

API_KEY = os.getenv(
    "FORTYGUARD_API_KEY"
)


# ============================================================
# VALIDATE API KEY
# ============================================================

def validate_api_key():
    if not API_KEY:
        raise RuntimeError(
            "FORTYGUARD_API_KEY was not found in .env"
        )


# ============================================================
# RUN TIME OF MEASURE
# ============================================================

def run_time_of_measure(
    polygon_aoi: dict[str, Any],
    start_date: str,
    start_time: str,
    end_time: str | None = None,
    filter_type: int = 1,
    granularity: int = 100,
):
    """
    Run FortyGuard time_of_measure.

    IMPORTANT:
    This function makes ONE FortyGuard Heatmap request.

    It returns the completed result.
    """

    validate_api_key()

    # --------------------------------------------------------
    # Build date_time payload
    # --------------------------------------------------------

    date_time = {
        "start_date": start_date,
        "start_time": start_time,
        "filter_type": filter_type,
    }

    if filter_type == 2:

        if not end_time:

            raise ValueError(
                "end_time is required for filter_type=2."
            )

        date_time[
            "end_time"
        ] = end_time

    # --------------------------------------------------------
    # Payload
    # --------------------------------------------------------

    payload = {
        "polygon_aoi": polygon_aoi,

        "date_time": date_time,

        "granularity": granularity,

        "analytic_type":
            "time_of_measure",
    }

    headers = {
        "api-key": API_KEY,
        "Content-Type":
            "application/json",
    }

    # --------------------------------------------------------
    # Submit
    # --------------------------------------------------------

    response = requests.post(
        HEATMAP_URL,
        headers=headers,
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    submit_data = response.json()

    activity_id = (
        submit_data
        .get("data", {})
        .get("activity_id")
    )

    if not activity_id:

        raise RuntimeError(
            "FortyGuard did not return an activity_id.\n"
            f"Response: {submit_data}"
        )

    # --------------------------------------------------------
    # Poll status
    # --------------------------------------------------------

    status_url = (
        f"{STATUS_URL}/{activity_id}"
    )

    for attempt in range(
        1,
        61,
    ):

        status_response = requests.get(
            status_url,
            headers={
                "api-key": API_KEY
            },
            timeout=60,
        )

        status_response.raise_for_status()

        status_data = (
            status_response
            .json()
        )

        data = (
            status_data
            .get("data", {})
        )

        status = data.get(
            "status"
        )

        print(
            f"Time-of-measure attempt "
            f"{attempt}: {status}"
        )

        if status == "Completed":

            result = data.get(
                "result"
            )

            if not result:

                raise RuntimeError(
                    "FortyGuard completed the activity "
                    "but returned no result."
                )

            return {
                "activity_id":
                    activity_id,

                "result":
                    result,

                "submit_response":
                    submit_data,
            }

        if status == "Failed":

            raise RuntimeError(
                f"FortyGuard time_of_measure failed.\n"
                f"Activity ID: {activity_id}\n"
                f"Response: {status_data}"
            )

        time.sleep(3)

    raise TimeoutError(
        "FortyGuard time_of_measure did not "
        "complete within the polling window."
    )