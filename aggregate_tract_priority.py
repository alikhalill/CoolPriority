import json
from collections import defaultdict


INPUT_FILE = "cooling_priority_v2_results.json"
OUTPUT_FILE = "tract_cooling_priority.json"


# ============================================================
# Helpers
# ============================================================

def mean(values):
    values = [
        value
        for value in values
        if isinstance(value, (int, float))
    ]

    if not values:
        return None

    return sum(values) / len(values)


def assign_priority(score):
    if score >= 75:
        return "Critical Priority"

    if score >= 50:
        return "High Priority"

    if score >= 25:
        return "Moderate Priority"

    return "Lower Priority"


# ============================================================
# Load data
# ============================================================

def load_records():

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        records = json.load(file)

    if not isinstance(records, list):
        raise RuntimeError(
            "Expected a list of records."
        )

    return records


# ============================================================
# Group tiles by Census Tract
# ============================================================

def group_by_tract(records):

    grouped = defaultdict(list)

    for record in records:

        geoid = record.get("GEOID")

        if not geoid:
            continue

        grouped[geoid].append(record)

    return grouped


# ============================================================
# Aggregate one Census Tract
# ============================================================

def aggregate_tract(geoid, tiles):

    # --------------------------------------------------------
    # Heat exposure values
    # --------------------------------------------------------

    average_temperatures = [
        tile["average_temperature"]
        for tile in tiles
    ]

    maximum_temperatures = [
        tile["max_temperature"]
        for tile in tiles
    ]

    minimum_temperatures = [
        tile["min_temperature"]
        for tile in tiles
    ]

    thermal_ranges = [
        tile["thermal_range"]
        for tile in tiles
    ]

    heat_scores = [
        tile["heat_exposure_score"]
        for tile in tiles
    ]

    # --------------------------------------------------------
    # SVI
    #
    # SVI is tract-level, so use the first valid value.
    # --------------------------------------------------------

    svi_values = [
        tile.get("RPL_THEMES")
        for tile in tiles
        if tile.get("RPL_THEMES") is not None
    ]

    if not svi_values:
        raise RuntimeError(
            f"No SVI value found for tract {geoid}"
        )

    svi_score = float(
        svi_values[0]
    ) * 100

    # --------------------------------------------------------
    # Aggregate heat
    # --------------------------------------------------------

    average_heat = mean(
        average_temperatures
    )

    average_max_temperature = mean(
        maximum_temperatures
    )

    average_min_temperature = mean(
        minimum_temperatures
    )

    average_thermal_range = mean(
        thermal_ranges
    )

    tract_heat_score = mean(
        heat_scores
    )

    # --------------------------------------------------------
    # Final tract priority
    # --------------------------------------------------------

    final_score = (
        tract_heat_score * 0.70
        +
        svi_score * 0.30
    )

    # --------------------------------------------------------
    # Basic location
    # --------------------------------------------------------

    latitude_values = [
        tile.get("latitude")
        for tile in tiles
        if tile.get("latitude") is not None
    ]

    longitude_values = [
        tile.get("longitude")
        for tile in tiles
        if tile.get("longitude") is not None
    ]

    return {
        "GEOID": geoid,

        "STATEFP": tiles[0].get(
            "STATEFP"
        ),

        "COUNTYFP": tiles[0].get(
            "COUNTYFP"
        ),

        "TRACTCE": tiles[0].get(
            "TRACTCE"
        ),

        "TRACT_NAME": tiles[0].get(
            "NAME"
        ),

        "tile_count": len(tiles),

        "centroid": {
            "latitude": mean(
                latitude_values
            ),
            "longitude": mean(
                longitude_values
            ),
        },

        "heat_exposure": {
            "average_temperature":
                round(
                    average_heat,
                    4,
                ),

            "average_max_temperature":
                round(
                    average_max_temperature,
                    4,
                ),

            "average_min_temperature":
                round(
                    average_min_temperature,
                    4,
                ),

            "average_thermal_range":
                round(
                    average_thermal_range,
                    4,
                ),

            "heat_exposure_score":
                round(
                    tract_heat_score,
                    2,
                ),
        },

        "social_vulnerability": {
            "RPL_THEME1":
                tiles[0].get(
                    "RPL_THEME1"
                ),

            "RPL_THEME2":
                tiles[0].get(
                    "RPL_THEME2"
                ),

            "RPL_THEME3":
                tiles[0].get(
                    "RPL_THEME3"
                ),

            "RPL_THEME4":
                tiles[0].get(
                    "RPL_THEME4"
                ),

            "RPL_THEMES":
                round(
                    svi_score,
                    2,
                ),
        },

        "cooling_priority_score":
            round(
                final_score,
                2,
            ),

        "priority_label":
            assign_priority(
                final_score
            ),
    }


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 70)
    print("CENSUS TRACT COOLING PRIORITY AGGREGATION")
    print("=" * 70)

    records = load_records()

    print(
        f"\nTiles loaded: {len(records)}"
    )

    grouped = group_by_tract(
        records
    )

    print(
        f"Unique Census Tracts: "
        f"{len(grouped)}"
    )

    # --------------------------------------------------------
    # Aggregate
    # --------------------------------------------------------

    tract_records = []

    for geoid, tiles in grouped.items():

        tract = aggregate_tract(
            geoid,
            tiles,
        )

        tract_records.append(
            tract
        )

    # --------------------------------------------------------
    # Sort by priority
    # --------------------------------------------------------

    tract_records.sort(
        key=lambda item:
        item["cooling_priority_score"],
        reverse=True,
    )

    # --------------------------------------------------------
    # Print Top 10
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP 10 CENSUS TRACTS")
    print("=" * 70)

    for rank, tract in enumerate(
        tract_records[:10],
        start=1,
    ):

        print(
            f"\n#{rank}"
        )

        print(
            f"GEOID: "
            f"{tract['GEOID']}"
        )

        print(
            f"Name: "
            f"{tract['TRACT_NAME']}"
        )

        print(
            f"Tiles: "
            f"{tract['tile_count']}"
        )

        print(
            f"Heat Exposure Score: "
            f"{tract['heat_exposure']['heat_exposure_score']:.2f}"
        )

        print(
            f"SVI Score: "
            f"{tract['social_vulnerability']['RPL_THEMES']:.2f}"
        )

        print(
            f"Cooling Priority: "
            f"{tract['cooling_priority_score']:.2f}/100"
        )

        print(
            f"Priority: "
            f"{tract['priority_label']}"
        )

    # --------------------------------------------------------
    # Print lowest 5
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("LOWEST 5 CENSUS TRACTS")
    print("=" * 70)

    for tract in tract_records[-5:]:

        print(
            f"GEOID {tract['GEOID']} | "
            f"Heat={tract['heat_exposure']['heat_exposure_score']:.2f} | "
            f"SVI={tract['social_vulnerability']['RPL_THEMES']:.2f} | "
            f"Priority={tract['cooling_priority_score']:.2f} | "
            f"{tract['priority_label']}"
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            tract_records,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)

    print(
        f"\nSaved to:"
        f"\n{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()