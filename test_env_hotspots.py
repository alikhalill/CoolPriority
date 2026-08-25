import json


INPUT_FILE = "cooling_priority_results.json"


def calculate_polygon_centroid(coordinates):
    """
    Calculate a simple centroid for a polygon using
    the average of its coordinate points.

    coordinates format:
    [
        [longitude, latitude],
        [longitude, latitude],
        ...
    ]
    """

    if not coordinates:
        raise ValueError("Polygon has no coordinates.")

    # Ignore the duplicated last point if it equals the first point
    points = coordinates

    if len(points) > 1 and points[0] == points[-1]:
        points = points[:-1]

    if not points:
        raise ValueError("Polygon has no valid points.")

    longitudes = [point[0] for point in points]
    latitudes = [point[1] for point in points]

    centroid_longitude = sum(longitudes) / len(longitudes)
    centroid_latitude = sum(latitudes) / len(latitudes)

    return centroid_latitude, centroid_longitude


def prepare_tile(tile):
    """
    Extract the fields we need from a ranked tile.
    """

    geometry = tile.get("geometry", {})

    if geometry.get("type") != "Polygon":
        raise ValueError(
            f"Tile {tile.get('tile_id')} does not contain a Polygon."
        )

    coordinates = geometry.get("coordinates", [])

    if not coordinates:
        raise ValueError(
            f"Tile {tile.get('tile_id')} has no coordinates."
        )

    # Polygon structure:
    # coordinates[0] = outer ring
    outer_ring = coordinates[0]

    latitude, longitude = calculate_polygon_centroid(
        outer_ring
    )

    return {
        "tile_id": tile.get("tile_id"),
        "latitude": round(latitude, 6),
        "longitude": round(longitude, 6),

        "average_temperature": tile.get(
            "average_temperature"
        ),

        "min_temperature": tile.get(
            "min_temperature"
        ),

        "max_temperature": tile.get(
            "max_temperature"
        ),

        "thermal_range": tile.get(
            "thermal_range"
        ),

        "cooling_priority_score": tile.get(
            "cooling_priority_score"
        ),

        "priority_label": tile.get(
            "priority_label"
        ),
    }


def main():

    # ------------------------------------------------------
    # 1. Load ranked results
    # ------------------------------------------------------

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        tiles = json.load(file)

    if not isinstance(tiles, list):
        raise RuntimeError(
            "Expected cooling_priority_results.json "
            "to contain a list."
        )

    print("=" * 70)
    print("HOTSPOT ENVIRONMENT PREPARATION")
    print("=" * 70)

    print(f"\nTotal ranked tiles: {len(tiles)}")

    # ------------------------------------------------------
    # 2. Select Top 5 and Bottom 5
    # ------------------------------------------------------

    top_5 = tiles[:5]
    bottom_5 = tiles[-5:]

    selected_tiles = []

    # Top 5
    for tile in top_5:
        prepared = prepare_tile(tile)
        prepared["group"] = "TOP_5"
        selected_tiles.append(prepared)

    # Bottom 5
    for tile in bottom_5:
        prepared = prepare_tile(tile)
        prepared["group"] = "BOTTOM_5"
        selected_tiles.append(prepared)

    # ------------------------------------------------------
    # 3. Print selected locations
    # ------------------------------------------------------

    print("\n" + "=" * 70)
    print("SELECTED TILES")
    print("=" * 70)

    for item in selected_tiles:

        print(
            f"\nGroup: {item['group']}"
        )

        print(
            f"Tile ID: {item['tile_id']}"
        )

        print(
            f"Centroid: "
            f"{item['latitude']}, "
            f"{item['longitude']}"
        )

        print(
            f"Average Temperature: "
            f"{item['average_temperature']:.2f} °C"
        )

        print(
            f"Maximum Temperature: "
            f"{item['max_temperature']:.2f} °C"
        )

        print(
            f"Minimum Temperature: "
            f"{item['min_temperature']:.2f} °C"
        )

        print(
            f"Thermal Range: "
            f"{item['thermal_range']:.2f} °C"
        )

        print(
            f"Cooling Priority Score: "
            f"{item['cooling_priority_score']:.2f}"
        )

        print(
            f"Priority: "
            f"{item['priority_label']}"
        )

    # ------------------------------------------------------
    # 4. Save selected tiles
    # ------------------------------------------------------

    output_file = "hotspot_environment_targets.json"

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            selected_tiles,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)

    print(
        f"\nSaved targets to:"
        f"\n{output_file}"
    )


if __name__ == "__main__":
    main()