from __future__ import annotations

from collections import Counter

import pandas as pd


# ============================================================
# PEAK HEAT TIMING
# ============================================================

def extract_peak_heat_timing(
    heatmap_result: dict,
):
    """
    Extract peak temperature hour information from
    a FortyGuard time_of_measure Heatmap result.

    FortyGuard time_of_measure returns one hour value
    for each heatmap tile.
    """

    if not isinstance(
        heatmap_result,
        dict,
    ):
        raise ValueError(
            "heatmap_result must be a dictionary."
        )

    map_data = heatmap_result.get(
        "map_data",
        {},
    )

    features = map_data.get(
        "features",
        [],
    )

    if not features:

        raise RuntimeError(
            "No heatmap features were returned."
        )

    rows = []

    for feature in features:

        properties = feature.get(
            "properties",
            {},
        )

        tile_id = properties.get(
            "tile_id"
        )

        value = properties.get(
            "value"
        )

        # Some FortyGuard outputs may store
        # the value under a different field.
        if value is None:

            value = properties.get(
                "time_of_measure"
            )

        if value is None:
            continue

        try:

            value = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            continue

        rows.append(
            {
                "tile_id":
                    tile_id,

                "peak_hour_utc":
                    value,
            }
        )

    if not rows:

        raise RuntimeError(
            "No peak-hour values could be extracted."
        )

    return pd.DataFrame(
        rows
    )


# ============================================================
# SUMMARY
# ============================================================

def summarize_peak_heat_timing(
    timing_df: pd.DataFrame,
):
    """
    Summarize peak heat timing across tiles.
    """

    if timing_df.empty:

        return {}

    hours = (
        timing_df[
            "peak_hour_utc"
        ]
        .dropna()
        .astype(float)
    )

    if hours.empty:

        return {}

    counts = (
        hours
        .round()
        .astype(int)
        .value_counts()
        .sort_index()
    )

    peak_hour = int(
        counts.idxmax()
    )

    peak_count = int(
        counts.max()
    )

    total_tiles = int(
        len(hours)
    )

    peak_share = (
        peak_count
        /
        total_tiles
        *
        100.0
    )

    return {
        "most_common_peak_hour_utc":
            peak_hour,

        "tiles_at_peak_hour":
            peak_count,

        "total_tiles":
            total_tiles,

        "peak_hour_share_percent":
            round(
                peak_share,
                2,
            ),

        "minimum_peak_hour_utc":
            int(
                hours.min()
            ),

        "maximum_peak_hour_utc":
            int(
                hours.max()
            ),
    }


# ============================================================
# HOURLY DISTRIBUTION
# ============================================================

def build_hour_distribution(
    timing_df: pd.DataFrame,
):
    """
    Build a complete 0-23 hour distribution.
    """

    if timing_df.empty:

        return pd.DataFrame(
            columns=[
                "hour",
                "tile_count",
                "percentage",
            ]
        )

    counts = (
        timing_df[
            "peak_hour_utc"
        ]
        .dropna()
        .round()
        .astype(int)
        .value_counts()
    )

    total = (
        counts.sum()
    )

    rows = []

    for hour in range(
        24
    ):

        count = int(
            counts.get(
                hour,
                0,
            )
        )

        percentage = (
            count
            /
            total
            *
            100.0
            if total
            else 0.0
        )

        rows.append(
            {
                "hour":
                    hour,

                "tile_count":
                    count,

                "percentage":
                    round(
                        percentage,
                        2,
                    ),
            }
        )

    return pd.DataFrame(
        rows
    )


# ============================================================
# HUMAN-READABLE INTERPRETATION
# ============================================================

def interpret_peak_timing(
    summary,
):
    """
    Convert peak timing into a decision-oriented message.
    """

    if not summary:

        return (
            "No peak timing information is available."
        )

    hour = summary[
        "most_common_peak_hour_utc"
    ]

    share = summary[
        "peak_hour_share_percent"
    ]

    return (
        f"The most common modeled peak-heat hour is "
        f"{hour:02d}:00 UTC, affecting approximately "
        f"{share:.1f}% of analyzed tiles."
    )

def analyze_peak_timing_result(
    result: dict,
):
    """
    Convenience wrapper for Streamlit.
    """

    timing = extract_peak_heat_timing(
        result
    )

    summary = summarize_peak_heat_timing(
        timing
    )

    distribution = build_hour_distribution(
        timing
    )

    return {
        "timing":
            timing,

        "summary":
            summary,

        "distribution":
            distribution,

        "interpretation":
            interpret_peak_timing(
                summary
            ),
    }