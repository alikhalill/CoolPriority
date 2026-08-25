import json

import pandas as pd
import geopandas as gpd


# ============================================================
# Configuration
# ============================================================

HEATMAP_FILE = "cooling_priority_results.json"

SVI_FILE = "data/SVI_2022_US.csv"

TRACTS_FILE = (
    "data/ny_tracts/tl_2022_36_tract.shp"
)

OUTPUT_FILE = "fortyguard_svi_matched.json"


# ============================================================
# Load FortyGuard Tiles
# ============================================================

def load_fortyguard_tiles():

    with open(
        HEATMAP_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        tiles = json.load(file)

    if not isinstance(
        tiles,
        list,
    ):
        raise RuntimeError(
            "cooling_priority_results.json "
            "must contain a list."
        )

    return tiles


# ============================================================
# Load Census Tracts
# ============================================================

def load_census_tracts():

    tracts = gpd.read_file(
        TRACTS_FILE
    )

    print(
        "\nCensus tract CRS:",
        tracts.crs
    )

    return tracts


# ============================================================
# Load SVI 2022
# ============================================================

def load_svi():

    svi = pd.read_csv(
        SVI_FILE,
        dtype={
            "FIPS": str
        }
    )

    # Make sure FIPS is 11 digits
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

    # New York only
    svi_ny = svi[
        svi["ST_ABBR"] == "NY"
    ].copy()

    print(
        "\nSVI NY rows:",
        len(svi_ny)
    )

    return svi_ny


# ============================================================
# Build FortyGuard GeoDataFrame
# ============================================================

def build_fortyguard_gdf(
    tiles
):

    features = []

    for tile in tiles:

        geometry = tile.get(
            "geometry"
        )

        if not geometry:
            continue

        properties = {
            "tile_id":
                tile.get(
                    "tile_id"
                ),

            "average_temperature":
                tile.get(
                    "average_temperature"
                ),

            "min_temperature":
                tile.get(
                    "min_temperature"
                ),

            "max_temperature":
                tile.get(
                    "max_temperature"
                ),

            "thermal_range":
                tile.get(
                    "thermal_range"
                ),

            "cooling_priority_score":
                tile.get(
                    "cooling_priority_score"
                ),

            "priority_label":
                tile.get(
                    "priority_label"
                ),
        }

        features.append(
            {
                "type": "Feature",
                "properties": properties,
                "geometry": geometry,
            }
        )

    gdf = (
        gpd.GeoDataFrame
        .from_features(
            features,
            crs="EPSG:4326"
        )
    )

    return gdf


# ============================================================
# Spatial Join
# ============================================================

def spatial_join_tiles_to_tracts(
    fortyguard,
    tracts,
):

    print(
        "\nFortyGuard CRS:",
        fortyguard.crs
    )

    # Match CRS
    fortyguard_projected = (
        fortyguard.to_crs(
            tracts.crs
        )
    )

    # Use representative point for MVP matching
    points = (
        fortyguard_projected
        .copy()
    )

    points["geometry"] = (
        points
        .geometry
        .representative_point()
    )

    joined = gpd.sjoin(
        points,
        tracts[
            [
                "GEOID",
                "STATEFP",
                "COUNTYFP",
                "TRACTCE",
                "NAME",
                "geometry",
            ]
        ],
        how="left",
        predicate="within",
    )

    return joined


# ============================================================
# Merge SVI
# ============================================================

def merge_svi(
    joined,
    svi,
):

    # --------------------------------------------------------
    # Prepare GEOID
    # --------------------------------------------------------

    joined["GEOID"] = (
        joined["GEOID"]
        .astype("string")
        .str.zfill(11)
    )

    # --------------------------------------------------------
    # SVI columns we need
    # --------------------------------------------------------

    svi_columns = [
        "FIPS",

        "STATE",
        "COUNTY",

        # Population
        "E_TOTPOP",
        "M_TOTPOP",

        # SVI Themes
        "RPL_THEME1",
        "RPL_THEME2",
        "RPL_THEME3",
        "RPL_THEME4",
        "RPL_THEMES",

        # Supplemental theme scores
        "SPL_THEME1",
        "SPL_THEME2",
        "SPL_THEME3",
        "SPL_THEME4",
        "SPL_THEMES",
    ]

    available_columns = [
        column
        for column in svi_columns
        if column in svi.columns
    ]

    svi_reduced = (
        svi[
            available_columns
        ]
        .copy()
    )

    svi_reduced = (
        svi_reduced
        .rename(
            columns={
                "FIPS": "GEOID"
            }
        )
    )

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    merged = joined.merge(
        svi_reduced,
        on="GEOID",
        how="left",
    )

    return merged


# ============================================================
# Validate Merge
# ============================================================

def validate_merge(
    merged
):

    print(
        "\n" + "=" * 70
    )

    print(
        "MERGE VALIDATION"
    )

    print(
        "=" * 70
    )

    matched_geoids = (
        merged[
            "GEOID"
        ]
        .notna()
        .sum()
    )

    missing_geoids = (
        merged[
            "GEOID"
        ]
        .isna()
        .sum()
    )

    matched_svi = (
        merged[
            "RPL_THEMES"
        ]
        .notna()
        .sum()
    )

    missing_svi = (
        merged[
            "RPL_THEMES"
        ]
        .isna()
        .sum()
    )

    matched_population = (
        merged[
            "E_TOTPOP"
        ]
        .notna()
        .sum()
    )

    missing_population = (
        merged[
            "E_TOTPOP"
        ]
        .isna()
        .sum()
    )

    print(
        "Tiles with GEOID:",
        matched_geoids
    )

    print(
        "Tiles without GEOID:",
        missing_geoids
    )

    print(
        "Tiles with SVI:",
        matched_svi
    )

    print(
        "Tiles without SVI:",
        missing_svi
    )

    print(
        "Tiles with Population:",
        matched_population
    )

    print(
        "Tiles without Population:",
        missing_population
    )

    if missing_svi > 0:
        raise RuntimeError(
            "Some tiles are missing SVI."
        )

    if missing_population > 0:
        raise RuntimeError(
            "Some tiles are missing population."
        )


# ============================================================
# Prepare Final Output
# ============================================================

def prepare_output(
    merged
):

    output_columns = [
        "tile_id",

        "average_temperature",
        "min_temperature",
        "max_temperature",
        "thermal_range",

        "cooling_priority_score",
        "priority_label",

        "GEOID",
        "STATEFP",
        "COUNTYFP",
        "TRACTCE",
        "NAME",

        # Population
        "E_TOTPOP",
        "M_TOTPOP",

        # SVI
        "RPL_THEME1",
        "RPL_THEME2",
        "RPL_THEME3",
        "RPL_THEME4",
        "RPL_THEMES",

        "SPL_THEME1",
        "SPL_THEME2",
        "SPL_THEME3",
        "SPL_THEME4",
        "SPL_THEMES",
    ]

    available = [
        column
        for column in output_columns
        if column in merged.columns
    ]

    output_df = (
        merged[
            available
        ]
        .copy()
    )

    return output_df


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 70)

    print(
        "FORTYGUARD ↔ SVI 2022 "
        "SPATIAL JOIN + POPULATION"
    )

    print("=" * 70)

    # --------------------------------------------------------
    # 1. Load
    # --------------------------------------------------------

    tiles = (
        load_fortyguard_tiles()
    )

    print(
        "\nFortyGuard tiles:",
        len(tiles)
    )

    tracts = (
        load_census_tracts()
    )

    svi = (
        load_svi()
    )

    # --------------------------------------------------------
    # 2. Build FortyGuard GeoDataFrame
    # --------------------------------------------------------

    fortyguard = (
        build_fortyguard_gdf(
            tiles
        )
    )

    print(
        "\nFortyGuard GeoDataFrame:",
        fortyguard.shape
    )

    # --------------------------------------------------------
    # 3. Spatial Join
    # --------------------------------------------------------

    joined = (
        spatial_join_tiles_to_tracts(
            fortyguard,
            tracts,
        )
    )

    print(
        "\nSpatial join completed."
    )

    # --------------------------------------------------------
    # 4. Merge SVI + Population
    # --------------------------------------------------------

    merged = (
        merge_svi(
            joined,
            svi,
        )
    )

    print(
        "\nSVI merge completed."
    )

    # --------------------------------------------------------
    # 5. Validate
    # --------------------------------------------------------

    validate_merge(
        merged
    )

    # --------------------------------------------------------
    # 6. Prepare output
    # --------------------------------------------------------

    output_df = (
        prepare_output(
            merged
        )
    )

    # --------------------------------------------------------
    # 7. Display sample
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "MATCHED DATA SAMPLE"
    )

    print(
        "=" * 70
    )

    print(
        output_df.head(
            10
        ).to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # 8. Save
    # --------------------------------------------------------

    records = (
        output_df
        .to_dict(
            orient="records"
        )
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            records,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print(
        "\n" + "=" * 70
    )

    print(
        "DONE"
    )

    print(
        "=" * 70
    )

    print(
        f"\nSaved to:"
        f"\n{OUTPUT_FILE}"
    )

    print(
        "\nFortyGuard API calls: 0"
    )


if __name__ == "__main__":
    main()