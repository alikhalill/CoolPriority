from __future__ import annotations

from typing import Any


def percentile_rank(values: list[float], value: float) -> float:
    """
    Return the percentile-like rank of `value` within `values`
    on a 0-100 scale.

    Higher value => higher percentile.
    """

    if not values:
        return 0.0

    less_or_equal = sum(v <= value for v in values)

    return ((less_or_equal - 1) / max(len(values) - 1, 1)) * 100


def extract_tiles(result: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract valid temperature tiles from a FortyGuard heatmap result.
    """

    map_data = result.get("map_data", {})
    features = map_data.get("features", [])

    tiles = []

    for feature in features:
        properties = feature.get("properties", {})

        average = properties.get("average_temperature")
        minimum = properties.get("min_temperature")
        maximum = properties.get("max_temperature")

        if not all(
            isinstance(value, (int, float))
            for value in (average, minimum, maximum)
        ):
            continue

        thermal_range = maximum - minimum

        tiles.append(
            {
                "tile_id": properties.get("tile_id"),
                "average_temperature": float(average),
                "min_temperature": float(minimum),
                "max_temperature": float(maximum),
                "thermal_range": float(thermal_range),
                "geometry": feature.get("geometry"),
            }
        )

    return tiles


def calculate_priority_scores(
    tiles: list[dict[str, Any]],
    average_weight: float = 0.50,
    maximum_weight: float = 0.35,
    range_weight: float = 0.15,
) -> list[dict[str, Any]]:
    """
    Calculate a transparent Cooling Priority Score.

    Current weights:
        Average temperature: 50%
        Maximum temperature: 35%
        Thermal range:       15%

    This is a project-specific ranking algorithm,
    NOT an official FortyGuard or medical risk score.
    """

    if not tiles:
        return []

    weight_sum = (
        average_weight
        + maximum_weight
        + range_weight
    )

    if abs(weight_sum - 1.0) > 1e-9:
        raise ValueError("Weights must sum to 1.0")

    averages = [
        tile["average_temperature"]
        for tile in tiles
    ]

    maximums = [
        tile["max_temperature"]
        for tile in tiles
    ]

    ranges = [
        tile["thermal_range"]
        for tile in tiles
    ]

    scored = []

    for tile in tiles:
        average_score = percentile_rank(
            averages,
            tile["average_temperature"],
        )

        maximum_score = percentile_rank(
            maximums,
            tile["max_temperature"],
        )

        range_score = percentile_rank(
            ranges,
            tile["thermal_range"],
        )

        priority_score = (
            average_score * average_weight
            + maximum_score * maximum_weight
            + range_score * range_weight
        )

        enriched = dict(tile)

        enriched["average_heat_score"] = round(
            average_score,
            2,
        )

        enriched["maximum_heat_score"] = round(
            maximum_score,
            2,
        )

        enriched["thermal_range_score"] = round(
            range_score,
            2,
        )

        enriched["cooling_priority_score"] = round(
            priority_score,
            2,
        )

        scored.append(enriched)

    scored.sort(
        key=lambda item: item["cooling_priority_score"],
        reverse=True,
    )

    return scored


def assign_priority_label(score: float) -> str:
    """
    Convert the relative score into a UI label.

    These labels describe priority within the analyzed area,
    not a medical danger classification.
    """

    if score >= 75:
        return "Critical Priority"

    if score >= 50:
        return "High Priority"

    if score >= 25:
        return "Moderate Priority"

    return "Lower Priority"


def add_priority_labels(
    scored_tiles: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """

    Add a human-readable priority label to each tile.
    """

    result = []

    for tile in scored_tiles:
        enriched = dict(tile)

        enriched["priority_label"] = assign_priority_label(
            tile["cooling_priority_score"]
        )

        result.append(enriched)

    return result