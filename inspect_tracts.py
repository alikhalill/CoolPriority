import geopandas as gpd


FILE_PATH = "data/ny_tracts/tl_2022_36_tract.shp"


def main():
    print("=" * 70)
    print("NEW YORK CENSUS TRACTS INSPECTION")
    print("=" * 70)

    # ------------------------------------------------------
    # 1. Read shapefile
    # ------------------------------------------------------

    gdf = gpd.read_file(FILE_PATH)

    # ------------------------------------------------------
    # 2. Basic information
    # ------------------------------------------------------

    print("\nShape:")
    print(gdf.shape)

    print("\nCRS:")
    print(gdf.crs)

    print("\nGeometry types:")
    print(gdf.geometry.geom_type.value_counts())

    # ------------------------------------------------------
    # 3. Columns
    # ------------------------------------------------------

    print("\nColumns:")

    for column in gdf.columns:
        print(column)

    # ------------------------------------------------------
    # 4. First rows
    # ------------------------------------------------------

    print("\nFirst 5 rows:")

    print(
        gdf.head()
    )

    # ------------------------------------------------------
    # 5. Bounds
    # ------------------------------------------------------

    print("\nBounds:")
    print(gdf.total_bounds)

    # ------------------------------------------------------
    # 6. Check important FIPS-related columns
    # ------------------------------------------------------

    print("\nPotential FIPS / GEOID columns:")

    for column in gdf.columns:

        name = column.upper()

        if (
            "GEOID" in name
            or "STATEFP" in name
            or "COUNTYFP" in name
            or "TRACT" in name
        ):
            print(column)

    # ------------------------------------------------------
    # 7. Check whether our FortyGuard area
    #    falls inside the New York bounds
    # ------------------------------------------------------

    test_lat = 40.7144
    test_lon = -74.0030

    print("\nTest FortyGuard point:")
    print(
        f"Latitude: {test_lat}"
    )
    print(
        f"Longitude: {test_lon}"
    )

    print("\n✅ Inspection completed.")


if __name__ == "__main__":
    main()