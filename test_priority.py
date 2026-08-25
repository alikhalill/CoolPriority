import json

from src.cooling_priority import (
    extract_tiles,
    calculate_priority_scores,
    add_priority_labels,
)


INPUT_FILE = "heatmap_time_range_result.json"


def main():
    # -------------------------------------------------------
    # 1. Load real FortyGuard result
    # -------------------------------------------------------

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        result = json.load(file)

    # -------------------------------------------------------
    # 2. Extract tiles
    # -------------------------------------------------------

    tiles = extract_tiles(result)

    print("=" * 70)
    print("COOLING PRIORITY ENGINE")
    print("=" * 70)

    print(f"\nTiles loaded: {len(tiles)}")

    if not tiles:
        raise RuntimeError("No valid tiles were found.")

    # -------------------------------------------------------
    # 3. Calculate priority scores
    # -------------------------------------------------------

    scored = calculate_priority_scores(
        tiles,
        average_weight=0.50,
        maximum_weight=0.35,
        range_weight=0.15,
    )

    # -------------------------------------------------------
    # 4. Add labels
    # -------------------------------------------------------

    scored = add_priority_labels(scored)

    # -------------------------------------------------------
    # 5. Print top 10
    # -------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP 10 COOLING PRIORITY AREAS")
    print("=" * 70)

    for rank, tile in enumerate(
        scored[:10],
        start=1,
    ):
        print(
            f"\n#{rank}"
        )

        print(
            f"Tile ID: "
            f"{tile['tile_id']}"
        )

        print(
            f"Average Temperature: "
            f"{tile['average_temperature']:.2f} °C"
        )

        print(
            f"Maximum Temperature: "
            f"{tile['max_temperature']:.2f} °C"
        )

        print(
            f"Thermal Range: "
            f"{tile['thermal_range']:.2f} °C"
        )

        print(
            f"Cooling Priority Score: "
            f"{tile['cooling_priority_score']:.2f}/100"
        )

        print(
            f"Priority: "
            f"{tile['priority_label']}"
        )

    # -------------------------------------------------------
    # 6. Print lowest priority
    # -------------------------------------------------------

    print("\n" + "=" * 70)
    print("LOWEST PRIORITY AREAS")
    print("=" * 70)

    for tile in scored[-5:]:
        print(
            f"Tile {tile['tile_id']} | "
            f"Score={tile['cooling_priority_score']:.2f} | "
            f"{tile['priority_label']}"
        )

    # -------------------------------------------------------
    # 7. Save ranked result
    # -------------------------------------------------------

    output_file = "cooling_priority_results.json"

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            scored,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)

    print(
        f"\nSaved ranked results to: "
        f"{output_file}"
    )


if __name__ == "__main__":
    main()