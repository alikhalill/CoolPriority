from __future__ import annotations

import os
import time
from typing import Any

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


def submit_heatmap(
    polygon_aoi: dict[str, Any],
    start_date: str,
    start_time: str,
    end_time: str | None = None,
    filter_type: int = 1,
    granularity: int = 100,
) -> str:

    payload = {
        "polygon_aoi": polygon_aoi,

        "date_time": {
            "start_date": start_date,
            "start_time": start_time,
            "filter_type": filter_type,
        },

        "granularity": granularity,
    }

    if filter_type == 2:

        if not end_time:
            raise ValueError(
                "end_time is required for filter_type=2"
            )

        payload["date_time"]["end_time"] = end_time

    headers = {
        "api-key": API_KEY,
        "Content-Type": "application/json",
    }

    response = requests.post(
        HEATMAP_URL,
        headers=headers,
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    activity_id = (
        data
        .get("data", {})
        .get("activity_id")
    )

    if not activity_id:
        raise RuntimeError(
            "FortyGuard did not return activity_id."
        )

    return activity_id


def wait_for_heatmap(
    activity_id: str,
    poll_interval: int = 5,
    max_attempts: int = 120,
) -> dict[str, Any]:

    url = (
        f"{STATUS_URL_BASE}/{activity_id}"
    )

    headers = {
        "api-key": API_KEY,
    }

    for _ in range(max_attempts):

        response = requests.get(
            url,
            headers=headers,
            timeout=30,
        )

        if response.status_code == 404:

            time.sleep(
                poll_interval
            )

            continue

        if response.status_code == 429:

            time.sleep(
                poll_interval * 2
            )

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
                "FortyGuard Heatmap task failed."
            )

        time.sleep(
            poll_interval
        )

    raise TimeoutError(
        "FortyGuard Heatmap task "
        "did not complete in time."
    )


def run_heatmap(
    polygon_aoi: dict[str, Any],
    start_date: str,
    start_time: str,
    end_time: str | None = None,
    filter_type: int = 1,
    granularity: int = 100,
) -> dict[str, Any]:

    activity_id = submit_heatmap(
        polygon_aoi=polygon_aoi,
        start_date=start_date,
        start_time=start_time,
        end_time=end_time,
        filter_type=filter_type,
        granularity=granularity,
    )

    result = wait_for_heatmap(
        activity_id
    )

    return {
        "activity_id": activity_id,
        "result": result,
    }