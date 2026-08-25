import json


INPUT_FILE = "fortyguard_svi_matched.json"
OUTPUT_FILE = "cooling_priority_v2_results.json"


# ============================================================
# Configuration
# ============================================================

HEAT_WEIGHT = 0.70
VULNERABILITY_WEIGHT = 0.30

AVERAGE_TEMP_WEIGHT = 0.50
MAX_TEMP_WEIGHT = 0.35
THERMAL_RANGE_WEIGHT = 0.15


# ============================================================
# Percentile Ranking
# ============================================================

def percentile_rank(values, value):
    """
    Convert a value into a relative percentile-like score
    from 0 to 100.

    Higher value = higher score.
    """

    if not values:
        return 0.0

    less_or_equal = sum(
        item <= value
        for item in values
    )

    return (
        (less_or_equal - 1)
        / max(len(values) - 1, 1)
    ) * 100


# ============================================================
# Load matched data
# ============================================================

def load_data():

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    if not isinstance(data, list):
        raise RuntimeError(
            "Expected a list in fortyguard_svi_matched.json"
        )

    return data


# ============================================================
# Calculate Heat Exposure Scores
# ============================================================

def calculate_heat_scores(records):

    average_values = [
        item["average_temperature"]
        for item in records
        if item.get("average_temperature") is not None
    ]

    maximum_values = [
        item["max_temperature"]
        for item in records
        if item.get("max_temperature") is not None
    ]

    range_values = [
        item["thermal_range"]
        for item in records
        if item.get("thermal_range") is not None
    ]

    for item in records:

        average_score = percentile_rank(
            average_values,
            item["average_temperature"],
        )

        maximum_score = percentile_rank(
            maximum_values,
            item["max_temperature"],
        )

        range_score = percentile_rank(
            range_values,
            item["thermal_range"],
        )

        heat_score = (
            average_score * AVERAGE_TEMP_WEIGHT
            +
            maximum_score * MAX_TEMP_WEIGHT
            +
            range_score * THERMAL_RANGE_WEIGHT
        )

        item["heat_exposure_score"] = round(
            heat_score,
            2,
        )

        item["average_heat_component"] = round(
            average_score,
            2,
        )

        item["maximum_heat_component"] = round(
            maximum_score,
            2,
        )

        item["thermal_range_component"] = round(
            range_score,
            2,
        )

    return records


# ============================================================
# Calculate Cooling Priority
# ============================================================

def calculate_cooling_priority(records):

    for item in records:

        svi = item.get(
            "RPL_THEMES"
        )

        if svi is None:
            raise RuntimeError(
                f"Missing RPL_THEMES for "
                f"Tile {item.get('tile_id')}"
            )

        vulnerability_score = (
            float(svi) * 100
        )

        heat_score = item[
            "heat_exposure_score"
        ]

        priority_score = (
            heat_score * HEAT_WEIGHT
            +
            vulnerability_score
            * VULNERABILITY_WEIGHT
        )

        item["social_vulnerability_score"] = round(
            vulnerability_score,
            2,
        )

        item["cooling_priority_score_v2"] = round(
            priority_score,
            2,
        )

    return records


# ============================================================
# Assign Priority Label
# ============================================================

def assign_priority(score):

    if score >= 75:
        return "Critical Priority"

    if score >= 50:
        return "High Priority"

    if score >= 25:
        return "Moderate Priority"

    return "Lower Priority"


# ============================================================
# Add Labels
# ============================================================

def add_labels(records):

    for item in records:

        item["priority_label_v2"] = assign_priority(
            item[
                "cooling_priority_score_v2"
            ]
        )

    return records


# ============================================================
# Save Results
# ============================================================

def save_results(records):

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


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 70)
    print("COOLING PRIORITY ENGINE V2")
    print("=" * 70)

    records = load_data()

    print(
        f"\nRecords loaded: {len(records)}"
    )

    # --------------------------------------------------------
    # Heat exposure
    # --------------------------------------------------------

    records = calculate_heat_scores(
        records
    )

    # --------------------------------------------------------
    # Vulnerability + final score
    # --------------------------------------------------------

    records = calculate_cooling_priority(
        records
    )

    # --------------------------------------------------------
    # Labels
    # --------------------------------------------------------

    records = add_labels(
        records
    )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    records.sort(
        key=lambda item:
        item["cooling_priority_score_v2"],
        reverse=True,
    )

    # --------------------------------------------------------
    # Top 10
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP 10 COOLING PRIORITY AREAS")
    print("=" * 70)

    for rank, item in enumerate(
        records[:10],
        start=1,
    ):

        print(
            f"\n#{rank}"
        )

        print(
            f"Tile: "
            f"{item['tile_id']}"
        )

        print(
            f"Census Tract: "
            f"{item.get('GEOID')}"
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
            f"Thermal Range: "
            f"{item['thermal_range']:.2f} °C"
        )

        print(
            f"Heat Exposure Score: "
            f"{item['heat_exposure_score']:.2f}"
        )

        print(
            f"SVI Score: "
            f"{item['social_vulnerability_score']:.2f}"
        )

        print(
            f"Cooling Priority: "
            f"{item['cooling_priority_score_v2']:.2f}/100"
        )

        print(
            f"Priority: "
            f"{item['priority_label_v2']}"
        )

    # --------------------------------------------------------
    # Lowest 5
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("LOWEST 5")
    print("=" * 70)

    for item in records[-5:]:

        print(
            f"Tile {item['tile_id']} | "
            f"Heat={item['heat_exposure_score']:.2f} | "
            f"SVI={item['social_vulnerability_score']:.2f} | "
            f"Priority="
            f"{item['cooling_priority_score_v2']:.2f} | "
            f"{item['priority_label_v2']}"
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_results(
        records
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