import json
import geopandas as gpd

TRACTS_FILE = (
    "data/ny_tracts/tl_2022_36_tract.shp"
)

PRIORITY_FILE = (
    "tract_priority_explanations.json"
)

OUTPUT_FILE = (
    "tract_cooling_priority.geojson"
)


def main():

    print("=" * 70)
    print("PREPARING MAP DATA")
    print("=" * 70)

    # ------------------------------------------------------
    # 1. Load Census Tracts
    # ------------------------------------------------------

    print("\nLoading Census Tracts...")

    tracts = gpd.read_file(
        TRACTS_FILE
    )

    print(
        f"Tracts loaded: {len(tracts)}"
    )

    # ------------------------------------------------------
    # 2. Load priority results
    # ------------------------------------------------------

    print(
        "\nLoading priority results..."
    )

    with open(
        PRIORITY_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        priority_data = json.load(file)

    print(
        f"Priority records: "
        f"{len(priority_data)}"
    )

    # ------------------------------------------------------
    # 3. Convert priority results to DataFrame
    # ------------------------------------------------------

    import pandas as pd

    priority_df = pd.DataFrame(
        priority_data
    )

    # ------------------------------------------------------
    # 4. Prepare GEOID
    # ------------------------------------------------------

    priority_df["GEOID"] = (
        priority_df["GEOID"]
        .astype(str)
        .str.zfill(11)
    )

    tracts["GEOID"] = (
        tracts["GEOID"]
        .astype(str)
        .str.zfill(11)
    )

    # ------------------------------------------------------
    # 5. Select fields for map
    # ------------------------------------------------------

    columns = [
        "GEOID",
        "TRACT_NAME",
        "cooling_priority_score",
        "priority_label",
        "heat_exposure_score",
        "social_vulnerability_score",
        "heat_contribution",
        "vulnerability_contribution",
    ]

    available = [
        column
        for column in columns
        if column in priority_df.columns
    ]

    priority_small = (
        priority_df[
            available
        ]
        .copy()
    )

    # ------------------------------------------------------
    # 6. Merge results into tract polygons
    # ------------------------------------------------------

    map_gdf = tracts.merge(
        priority_small,
        on="GEOID",
        how="left",
    )

    print(
        "\nMapped tracts:",
        map_gdf[
            "cooling_priority_score"
        ]
        .notna()
        .sum()
    )

    print(
        "Unmapped tracts:",
        map_gdf[
            "cooling_priority_score"
        ]
        .isna()
        .sum()
    )

    # ------------------------------------------------------
    # 7. Keep only analyzed tracts
    # ------------------------------------------------------

    map_gdf = map_gdf[
        map_gdf[
            "cooling_priority_score"
        ].notna()
    ].copy()

    # ------------------------------------------------------
    # 8. Convert CRS to WGS84 for web maps
    # ------------------------------------------------------

    map_gdf = map_gdf.to_crs(
        "EPSG:4326"
    )

    # ------------------------------------------------------
    # 9. Save GeoJSON
    # ------------------------------------------------------

    map_gdf.to_file(
        OUTPUT_FILE,
        driver="GeoJSON",
    )

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)

    print(
        f"\nSaved map data to:"
        f"\n{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()