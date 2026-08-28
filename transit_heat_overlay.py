from __future__ import annotations

import requests
import pandas as pd
import geopandas as gpd


MTA_STATIONS_URL = (
    "https://data.ny.gov/resource/39hk-dx4f.json"
    "?$limit=500"
)


# ============================================================
# LOAD MTA STATIONS
# ============================================================

def load_mta_stations():

    response = requests.get(
        MTA_STATIONS_URL,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(
        data,
        list,
    ):
        raise RuntimeError(
            "Unexpected MTA response."
        )

    df = pd.DataFrame(
        data
    )

    required = [
        "stop_name",
        "gtfs_latitude",
        "gtfs_longitude",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:

        raise RuntimeError(
            "MTA response missing columns: "
            + ", ".join(missing)
        )

    # --------------------------------------------------------
    # Convert coordinates to numeric
    # --------------------------------------------------------

    df[
        "gtfs_latitude"
    ] = pd.to_numeric(
        df[
            "gtfs_latitude"
        ],
        errors="coerce",
    )

    df[
        "gtfs_longitude"
    ] = pd.to_numeric(
        df[
            "gtfs_longitude"
        ],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Remove records without coordinates
    # --------------------------------------------------------

    df = df.dropna(
        subset=[
            "gtfs_latitude",
            "gtfs_longitude",
        ]
    )

    # --------------------------------------------------------
    # Remove duplicate physical stations
    #
    # The MTA dataset can contain multiple records for
    # the same physical station because the station may
    # serve multiple routes / lines.
    #
    # We identify a physical station using:
    #   stop_name + latitude + longitude
    # --------------------------------------------------------

    dedup_columns = [
        "stop_name",
        "gtfs_latitude",
        "gtfs_longitude",
    ]

    existing_dedup_columns = [
        column
        for column in dedup_columns
        if column in df.columns
    ]

    before_dedup = len(
        df
    )

    df = (
        df
        .drop_duplicates(
            subset=existing_dedup_columns
        )
        .reset_index(
            drop=True
        )
    )

    after_dedup = len(
        df
    )

    print(
        f"MTA records before deduplication: "
        f"{before_dedup}"
    )

    print(
        f"Unique physical stations: "
        f"{after_dedup}"
    )

    print(
        f"Duplicate records removed: "
        f"{before_dedup - after_dedup}"
    )

    return df


# ============================================================
# CONVERT STATIONS TO GEODATAFRAME
# ============================================================

def stations_to_gdf(
    stations_df,
):

    gdf = gpd.GeoDataFrame(
        stations_df.copy(),

        geometry=gpd.points_from_xy(
            stations_df[
                "gtfs_longitude"
            ],
            stations_df[
                "gtfs_latitude"
            ],
        ),

        crs="EPSG:4326",
    )

    return gdf


# ============================================================
# MATCH STATIONS TO PRIORITY TRACTS
# ============================================================

def match_stations_to_priority(
    stations_gdf,
    priority_gdf,
):

    priority = priority_gdf.copy()

    priority = priority.to_crs(
        "EPSG:4326"
    )

    stations = (
        stations_gdf
        .to_crs("EPSG:4326")
    )

    joined = gpd.sjoin(
        stations,
        priority[
            [
                "GEOID",
                "TRACT_NAME",
                "cooling_priority_score",
                "priority_label",
                "heat_exposure_score",
                "social_vulnerability_score",
                "geometry",
            ]
        ],
        how="left",
        predicate="within",
    )

    return joined


# ============================================================
# PRIORITIZE HOT TRANSIT STATIONS
# ============================================================

def rank_transit_heat_exposure(
    matched_gdf,
    threshold=75.0,
):

    result = matched_gdf.copy()

    result[
        "heat_priority_flag"
    ] = (
        result[
            "cooling_priority_score"
        ]
        >= threshold
    )

    result = (
        result
        .sort_values(
            "cooling_priority_score",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )

    return result


# ============================================================
# TOP HOT TRANSIT STATIONS
# ============================================================

def get_top_hot_stations(
    matched_gdf,
    n=5,
):

    hot = matched_gdf[
        matched_gdf[
            "cooling_priority_score"
        ].notna()
    ]

    return (
        hot
        .sort_values(
            "cooling_priority_score",
            ascending=False,
        )
        .head(n)
        .copy()
    )