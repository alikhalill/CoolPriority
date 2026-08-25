from __future__ import annotations

from typing import Any

import json
import geopandas as gpd
import pandas as pd


# ============================================================
# FILES
# ============================================================

TRACTS_FILE = (
    "data/ny_tracts/tl_2022_36_tract.shp"
)

SVI_FILE = (
    "data/SVI_2022_US.csv"
)


# ============================================================
# WEIGHTS
# ============================================================

# Heat Exposure
HEAT_AVG_WEIGHT = 0.50
HEAT_MAX_WEIGHT = 0.35
HEAT_RANGE_WEIGHT = 0.15

# Final Cooling Priority
FINAL_HEAT_WEIGHT = 0.70
FINAL_SVI_WEIGHT = 0.30


# ============================================================
# Percentile Rank
# ============================================================

def percentile_rank(
    values: list[float],
    value: float,
) -> float:

    if not values:
        return 0.0

    less_or_equal = sum(
        item <= value
        for item in values
    )

    return (
        (less_or_equal - 1)
        / max(len(values) - 1, 1)
    ) * 100.0


# ============================================================
# Load SVI - New York
# ============================================================

def load_svi_ny() -> pd.DataFrame:

    svi = pd.read_csv(
        SVI_FILE,
        dtype={
            "FIPS": str
        },
    )

    svi["FIPS"] = (
        svi["FIPS"]
        .astype(str)
        .str.replace(
            ".0",
            "",
            regex=False,
        )
        .str.zfill(11)
    )

    svi = svi[
        svi["ST_ABBR"] == "NY"
    ].copy()

    return svi[
        [
            "FIPS",
            "RPL_THEME1",
            "RPL_THEME2",
            "RPL_THEME3",
            "RPL_THEME4",
            "RPL_THEMES",
        ]
    ].copy()


# ============================================================
# Load Census Tracts
# ============================================================

def load_ny_tracts() -> gpd.GeoDataFrame:

    tracts = gpd.read_file(
        TRACTS_FILE
    )

    tracts["GEOID"] = (
        tracts["GEOID"]
        .astype(str)
        .str.zfill(11)
    )

    return tracts


# ============================================================
# Convert FortyGuard Heatmap Result → GeoDataFrame
# ============================================================

def heatmap_result_to_gdf(
    heatmap_result: dict[str, Any],
) -> gpd.GeoDataFrame:

    # --------------------------------------------------------
    # Validate top-level response
    # --------------------------------------------------------

    if not isinstance(
        heatmap_result,
        dict,
    ):
        raise RuntimeError(
            "FortyGuard Heatmap result is not a dictionary."
        )

    # --------------------------------------------------------
    # Get map_data
    # --------------------------------------------------------

    map_data = heatmap_result.get(
        "map_data",
        {},
    )

    if not isinstance(
        map_data,
        dict,
    ):
        raise RuntimeError(
            "FortyGuard Heatmap returned invalid map_data."
        )

    # --------------------------------------------------------
    # Get features
    # --------------------------------------------------------

    features = map_data.get(
        "features",
        [],
    )

    # --------------------------------------------------------
    # IMPORTANT DEBUGGING
    # --------------------------------------------------------

    if not features:

        result_keys = list(
            heatmap_result.keys()
        )

        map_data_keys = list(
            map_data.keys()
        )

        debug_map_data = json.dumps(
            map_data,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

        # Keep error readable
        if len(debug_map_data) > 5000:
            debug_map_data = (
                debug_map_data[:5000]
                + "\n... [truncated]"
            )

        raise RuntimeError(
            "FortyGuard Heatmap returned no features.\n\n"

            "This usually means the selected AOI "
            "produced no spatial cells, or the "
            "Heatmap response structure is different "
            "from what the analysis engine expects.\n\n"

            f"Result keys:\n"
            f"{result_keys}\n\n"

            f"Map data keys:\n"
            f"{map_data_keys}\n\n"

            f"Map data preview:\n"
            f"{debug_map_data}"
        )

    # --------------------------------------------------------
    # Build rows
    # --------------------------------------------------------

    rows = []

    for feature in features:

        if not isinstance(
            feature,
            dict,
        ):
            continue

        properties = feature.get(
            "properties",
            {},
        )

        geometry = feature.get(
            "geometry"
        )

        if not isinstance(
            properties,
            dict,
        ):
            continue

        average_temperature = (
            properties.get(
                "average_temperature"
            )
        )

        min_temperature = (
            properties.get(
                "min_temperature"
            )
        )

        max_temperature = (
            properties.get(
                "max_temperature"
            )
        )

        # ----------------------------------------------------
        # Validate temperature values
        # ----------------------------------------------------

        if not all(
            isinstance(
                value,
                (int, float),
            )
            for value in (
                average_temperature,
                min_temperature,
                max_temperature,
            )
        ):
            continue

        if geometry is None:
            continue

        rows.append(
            {
                "tile_id":
                    properties.get(
                        "tile_id"
                    ),

                "average_temperature":
                    float(
                        average_temperature
                    ),

                "min_temperature":
                    float(
                        min_temperature
                    ),

                "max_temperature":
                    float(
                        max_temperature
                    ),

                "thermal_range":
                    float(
                        max_temperature
                        - min_temperature
                    ),

                "geometry":
                    geometry,
            }
        )

    # --------------------------------------------------------
    # Validate parsed tiles
    # --------------------------------------------------------

    if not rows:

        raise RuntimeError(
            "FortyGuard returned features, but "
            "none contained valid temperature values "
            "and geometry."
        )

    # --------------------------------------------------------
    # Build GeoDataFrame
    # --------------------------------------------------------

    return gpd.GeoDataFrame.from_features(
        [
            {
                "type": "Feature",
                "properties": {
                    key: value
                    for key, value in row.items()
                    if key != "geometry"
                },
                "geometry":
                    row["geometry"],
            }
            for row in rows
        ],
        crs="EPSG:4326",
    )


# ============================================================
# Calculate Heat Exposure Scores
# ============================================================

def add_heat_scores(
    tiles: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:

    averages = (
        tiles[
            "average_temperature"
        ]
        .tolist()
    )

    maximums = (
        tiles[
            "max_temperature"
        ]
        .tolist()
    )

    ranges = (
        tiles[
            "thermal_range"
        ]
        .tolist()
    )

    tiles = tiles.copy()

    tiles["average_heat_component"] = (
        tiles[
            "average_temperature"
        ]
        .apply(
            lambda value:
            percentile_rank(
                averages,
                value,
            )
        )
    )

    tiles["maximum_heat_component"] = (
        tiles[
            "max_temperature"
        ]
        .apply(
            lambda value:
            percentile_rank(
                maximums,
                value,
            )
        )
    )

    tiles["thermal_range_component"] = (
        tiles[
            "thermal_range"
        ]
        .apply(
            lambda value:
            percentile_rank(
                ranges,
                value,
            )
        )
    )

    tiles["heat_exposure_score"] = (
        tiles[
            "average_heat_component"
        ]
        * HEAT_AVG_WEIGHT

        +

        tiles[
            "maximum_heat_component"
        ]
        * HEAT_MAX_WEIGHT

        +

        tiles[
            "thermal_range_component"
        ]
        * HEAT_RANGE_WEIGHT
    )

    return tiles


# ============================================================
# Match Heatmap Tiles to Census Tracts
# ============================================================

def match_tiles_to_tracts(
    tiles: gpd.GeoDataFrame,
    tracts: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:

    tiles_projected = (
        tiles
        .to_crs(
            tracts.crs
        )
        .copy()
    )

    # Keep tile geometry first.
    # We use a representative point for matching.
    tiles_projected[
        "tile_geometry"
    ] = (
        tiles_projected
        .geometry
        .copy()
    )

    # Representative point for spatial matching
    tiles_projected[
        "geometry"
    ] = (
        tiles_projected
        .geometry
        .representative_point()
    )

    tract_columns = [
        "GEOID",
        "STATEFP",
        "COUNTYFP",
        "TRACTCE",
        "NAME",
        "geometry",
    ]

    joined = gpd.sjoin(
        tiles_projected,
        tracts[
            tract_columns
        ],
        how="left",
        predicate="within",
    )

    if joined[
        "GEOID"
    ].isna().any():

        unmatched = int(
            joined[
                "GEOID"
            ]
            .isna()
            .sum()
        )

        raise RuntimeError(
            f"{unmatched} Heatmap tiles "
            "could not be matched to "
            "a Census Tract."
        )

    return joined


# ============================================================
# Attach SVI
# ============================================================

def attach_svi(
    joined: gpd.GeoDataFrame,
    svi: pd.DataFrame,
) -> gpd.GeoDataFrame:

    joined = joined.copy()

    svi = svi.rename(
        columns={
            "FIPS": "GEOID"
        }
    )

    joined["GEOID"] = (
        joined["GEOID"]
        .astype(str)
        .str.zfill(11)
    )

    merged = joined.merge(
        svi,
        on="GEOID",
        how="left",
    )

    if merged[
        "RPL_THEMES"
    ].isna().any():

        missing = int(
            merged[
                "RPL_THEMES"
            ]
            .isna()
            .sum()
        )

        raise RuntimeError(
            f"{missing} matched tracts "
            "have no SVI value."
        )

    return merged


# ============================================================
# Aggregate Tiles → Census Tracts
# ============================================================

def aggregate_to_tracts(
    merged: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:

    records = []

    for geoid, group in merged.groupby(
        "GEOID"
    ):

        # ----------------------------------------------------
        # Heat Exposure
        # ----------------------------------------------------

        heat_exposure = (
            group[
                "heat_exposure_score"
            ]
            .mean()
        )

        # ----------------------------------------------------
        # Social Vulnerability
        # ----------------------------------------------------

        svi_score = (
            float(
                group[
                    "RPL_THEMES"
                ]
                .iloc[0]
            )
            * 100.0
        )

        # ----------------------------------------------------
        # Final Priority
        # ----------------------------------------------------

        priority = (
            heat_exposure
            * FINAL_HEAT_WEIGHT

            +

            svi_score
            * FINAL_SVI_WEIGHT
        )

        # ----------------------------------------------------
        # First matched tract record
        # ----------------------------------------------------

        first = group.iloc[0]

        # ----------------------------------------------------
        # Keep actual Census Tract geometry
        # ----------------------------------------------------

        tract_geometry = first[
            "geometry"
        ]

        records.append(
            {
                "GEOID":
                    geoid,

                "TRACT_NAME":
                    first["NAME"],

                "tile_count":
                    len(group),

                "heat_exposure_score":
                    round(
                        heat_exposure,
                        2,
                    ),

                "social_vulnerability_score":
                    round(
                        svi_score,
                        2,
                    ),

                "cooling_priority_score":
                    round(
                        priority,
                        2,
                    ),

                "average_temperature":
                    round(
                        group[
                            "average_temperature"
                        ]
                        .mean(),
                        4,
                    ),

                "maximum_temperature":
                    round(
                        group[
                            "max_temperature"
                        ]
                        .mean(),
                        4,
                    ),

                "thermal_range":
                    round(
                        group[
                            "thermal_range"
                        ]
                        .mean(),
                        4,
                    ),

                "RPL_THEME1":
                    first[
                        "RPL_THEME1"
                    ],

                "RPL_THEME2":
                    first[
                        "RPL_THEME2"
                    ],

                "RPL_THEME3":
                    first[
                        "RPL_THEME3"
                    ],

                "RPL_THEME4":
                    first[
                        "RPL_THEME4"
                    ],

                "RPL_THEMES":
                    first[
                        "RPL_THEMES"
                    ],

                "geometry":
                    tract_geometry,
            }
        )

    # ========================================================
    # Convert records → GeoDataFrame
    # ========================================================

    result = gpd.GeoDataFrame(
        records,
        geometry="geometry",
        crs=merged.crs,
    )

    # ========================================================
    # Convert geometry to WGS84
    # ========================================================

    result = (
        result
        .to_crs(
            "EPSG:4326"
        )
        .reset_index(
            drop=True
        )
    )

    # ========================================================
    # Sort by priority
    # ========================================================

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
# Priority Labels
# ============================================================

def add_priority_labels(
    result: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:

    result = result.copy()

    def label(
        score: float
    ) -> str:

        if score >= 75:
            return "Critical Priority"

        if score >= 50:
            return "High Priority"

        if score >= 25:
            return "Moderate Priority"

        return "Lower Priority"

    result[
        "priority_label"
    ] = (
        result[
            "cooling_priority_score"
        ]
        .apply(label)
    )

    return result


# ============================================================
# Main Analysis Function
# ============================================================

def analyze_heatmap_result(
    heatmap_result: dict[str, Any],
) -> gpd.GeoDataFrame:

    # --------------------------------------------------------
    # 1. FortyGuard Heatmap → Tiles
    # --------------------------------------------------------

    tiles = (
        heatmap_result_to_gdf(
            heatmap_result
        )
    )

    # --------------------------------------------------------
    # 2. Heat Exposure
    # --------------------------------------------------------

    tiles = (
        add_heat_scores(
            tiles
        )
    )

    # --------------------------------------------------------
    # 3. Load Census Tracts
    # --------------------------------------------------------

    tracts = (
        load_ny_tracts()
    )

    # --------------------------------------------------------
    # 4. Load SVI
    # --------------------------------------------------------

    svi = (
        load_svi_ny()
    )

    # --------------------------------------------------------
    # 5. Tile → Census Tract
    # --------------------------------------------------------

    joined = (
        match_tiles_to_tracts(
            tiles,
            tracts,
        )
    )

    # --------------------------------------------------------
    # 6. Attach SVI
    # --------------------------------------------------------

    merged = (
        attach_svi(
            joined,
            svi,
        )
    )

    # --------------------------------------------------------
    # 7. Aggregate to Tract
    # --------------------------------------------------------

    result = (
        aggregate_to_tracts(
            merged
        )
    )

    # --------------------------------------------------------
    # 8. Add labels
    # --------------------------------------------------------

    result = (
        add_priority_labels(
            result
        )
    )

    return result