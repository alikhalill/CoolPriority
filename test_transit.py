import json

import geopandas as gpd

from transit_heat_overlay import (
    load_mta_stations,
    stations_to_gdf,
    match_stations_to_priority,
    get_top_hot_stations,
)


# ============================================================
# Load current priority map
# ============================================================

with open(
    "tract_cooling_priority.geojson",
    "r",
    encoding="utf-8",
) as file:

    geojson = json.load(file)


priority = gpd.GeoDataFrame.from_features(
    geojson["features"],
    crs="EPSG:4326",
)


# ============================================================
# Load MTA stations
# ============================================================

print("=" * 70)
print("TRANSIT HEAT OVERLAY TEST")
print("=" * 70)

print("\nLoading MTA stations...")

stations = load_mta_stations()

print(
    "Stations loaded:",
    len(stations),
)


# ============================================================
# Convert to GeoDataFrame
# ============================================================

stations_gdf = stations_to_gdf(
    stations
)

print(
    "Station GeoDataFrame:",
    stations_gdf.shape,
)


# ============================================================
# Match stations to priority tracts
# ============================================================

matched = match_stations_to_priority(
    stations_gdf,
    priority,
)

print(
    "Matched records:",
    len(matched),
)

print(
    "Stations with priority:",
    matched[
        "cooling_priority_score"
    ]
    .notna()
    .sum()
)


# ============================================================
# Top hot transit stations
# ============================================================

top = get_top_hot_stations(
    matched,
    n=10,
)


print()
print("=" * 70)
print("TOP TRANSIT LOCATIONS IN HIGH PRIORITY AREAS")
print("=" * 70)

for index, (_, row) in enumerate(
    top.iterrows(),
    start=1,
):

    print()
    print(
        f"#{index}"
    )

    print(
        "Station:",
        row.get(
            "stop_name",
            "Unknown",
        ),
    )

    print(
        "Tract:",
        row.get(
            "TRACT_NAME",
            "Unknown",
        ),
    )

    print(
        "Cooling Priority:",
        row.get(
            "cooling_priority_score",
        ),
    )

    print(
        "Heat Exposure:",
        row.get(
            "heat_exposure_score",
        ),
    )

    print(
        "Social Vulnerability:",
        row.get(
            "social_vulnerability_score",
        ),
    )


print()
print("=" * 70)
print("DONE")
print("=" * 70)

print(
    "\nFortyGuard API calls: 0"
)

print(
    "FortyGuard credits consumed: 0"
)