import geopandas as gpd


FILE = "tract_cooling_priority.geojson"


def main():
    gdf = gpd.read_file(FILE)

    print("=" * 70)
    print("MAP DATA INSPECTION")
    print("=" * 70)

    print("\nShape:")
    print(gdf.shape)

    print("\nCRS:")
    print(gdf.crs)

    print("\nColumns:")
    print(gdf.columns.tolist())

    print("\nMissing values:")
    print(
        gdf[
            [
                "GEOID",
                "cooling_priority_score",
                "priority_label",
                "heat_exposure_score",
                "social_vulnerability_score",
                "geometry",
            ]
        ].isna().sum()
    )

    print("\nPriority summary:")
    print(
        gdf[
            [
                "GEOID",
                "TRACT_NAME",
                "cooling_priority_score",
                "priority_label",
            ]
        ]
        .sort_values(
            "cooling_priority_score",
            ascending=False,
        )
        .to_string(index=False)
    )

    print("\nGeometry types:")
    print(gdf.geometry.geom_type.value_counts())

    print("\n✅ Inspection completed.")


if __name__ == "__main__":
    main()