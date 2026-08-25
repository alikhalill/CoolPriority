import json


INPUT_FILE = "heat_burden_results.json"


def main():

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    exceedance = None
    persistence = None

    for item in data:

        if item["analytic_type"] == "exceedance":
            exceedance = item["result"]

        elif item["analytic_type"] == "persistence":
            persistence = item["result"]

    if not exceedance or not persistence:
        raise RuntimeError(
            "Could not find both exceedance and persistence results."
        )

    exceedance_features = (
        exceedance
        .get("map_data", {})
        .get("features", [])
    )

    persistence_features = (
        persistence
        .get("map_data", {})
        .get("features", [])
    )

    exceedance_values = {}

    for feature in exceedance_features:

        props = feature.get(
            "properties",
            {},
        )

        tile_id = props.get(
            "tile_id"
        )

        value = props.get(
            "value"
        )

        exceedance_values[tile_id] = value

    persistence_values = {}

    for feature in persistence_features:

        props = feature.get(
            "properties",
            {},
        )

        tile_id = props.get(
            "tile_id"
        )

        value = props.get(
            "value"
        )

        persistence_values[tile_id] = value

    print("=" * 70)
    print("EXCEEDANCE vs PERSISTENCE")
    print("=" * 70)

    print(
        "\nExceedance tiles:",
        len(exceedance_values),
    )

    print(
        "Persistence tiles:",
        len(persistence_values),
    )

    common_ids = set(
        exceedance_values
    ) & set(
        persistence_values
    )

    different = []

    for tile_id in sorted(
        common_ids
    ):

        exc = exceedance_values[
            tile_id
        ]

        persistence = persistence_values[
            tile_id
        ]

        difference = abs(
            exc - persistence
        )

        if difference > 1e-9:

            different.append(
                {
                    "tile_id": tile_id,
                    "exceedance": exc,
                    "persistence": persistence,
                    "difference": difference,
                }
            )

    print(
        "\nCommon tiles:",
        len(common_ids),
    )

    print(
        "Different tiles:",
        len(different),
    )

    print(
        "Identical tiles:",
        len(common_ids) - len(different),
    )

    if different:

        print("\nExamples where they differ:")

        for item in different[:10]:

            print(
                f"Tile {item['tile_id']} | "
                f"Exceedance={item['exceedance']} | "
                f"Persistence={item['persistence']} | "
                f"Difference={item['difference']}"
            )

    else:

        print(
            "\n✅ Exceedance and persistence are "
            "identical for every common tile."
        )

    # --------------------------------------------------------
    # Calculate maximum difference
    # --------------------------------------------------------

    if common_ids:

        max_difference = max(
            abs(
                exceedance_values[tile_id]
                -
                persistence_values[tile_id]
            )
            for tile_id in common_ids
        )

        print(
            "\nMaximum absolute difference:",
            max_difference,
        )

    print(
        "\nNo API request was made."
    )

    print(
        "Credits consumed: 0"
    )


if __name__ == "__main__":
    main()