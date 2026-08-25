import json
import statistics


INPUT_FILE = "heat_burden_results.json"


def percentile(sorted_values, p):
    """
    Simple linear percentile calculation.
    p is between 0 and 100.
    """
    if not sorted_values:
        return None

    if len(sorted_values) == 1:
        return sorted_values[0]

    position = (
        (len(sorted_values) - 1)
        * (p / 100)
    )

    lower = int(position)
    upper = min(
        lower + 1,
        len(sorted_values) - 1,
    )

    weight = position - lower

    return (
        sorted_values[lower]
        * (1 - weight)
        +
        sorted_values[upper]
        * weight
    )


def rank_correlation(xs, ys):
    """
    Spearman-like rank correlation using
    average tie-free ordering for this experiment.
    """

    if len(xs) != len(ys) or not xs:
        return None

    def ranks(values):
        order = sorted(
            range(len(values)),
            key=lambda i: values[i],
        )

        ranks = [0.0] * len(values)

        for rank, index in enumerate(order):
            ranks[index] = rank + 1

        return ranks

    rx = ranks(xs)
    ry = ranks(ys)

    mean_x = statistics.mean(rx)
    mean_y = statistics.mean(ry)

    numerator = sum(
        (x - mean_x) * (y - mean_y)
        for x, y in zip(rx, ry)
    )

    denominator_x = sum(
        (x - mean_x) ** 2
        for x in rx
    )

    denominator_y = sum(
        (y - mean_y) ** 2
        for y in ry
    )

    denominator = (
        denominator_x
        * denominator_y
    ) ** 0.5

    if denominator == 0:
        return 0.0

    return numerator / denominator


def main():

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        results = json.load(file)

    exceedance_result = next(
        item
        for item in results
        if item["analytic_type"] == "exceedance"
    )

    features = (
        exceedance_result
        .get("result", {})
        .get("map_data", {})
        .get("features", [])
    )

    values = []

    for feature in features:

        properties = feature.get(
            "properties",
            {},
        )

        value = properties.get(
            "value"
        )

        if isinstance(
            value,
            (int, float),
        ):
            values.append(
                value
            )

    if not values:
        raise RuntimeError(
            "No exceedance values found."
        )

    values_sorted = sorted(
        values
    )

    print("=" * 70)
    print("HEAT BURDEN DISTRIBUTION")
    print("=" * 70)

    print(
        "\nTiles:",
        len(values)
    )

    print(
        "Minimum:",
        round(
            min(values),
            4,
        )
    )

    print(
        "P25:",
        round(
            percentile(
                values_sorted,
                25,
            ),
            4,
        )
    )

    print(
        "Median:",
        round(
            percentile(
                values_sorted,
                50,
            ),
            4,
        )
    )

    print(
        "P75:",
        round(
            percentile(
                values_sorted,
                75,
            ),
            4,
        )
    )

    print(
        "Maximum:",
        round(
            max(values),
            4,
        )
    )

    print(
        "Mean:",
        round(
            statistics.mean(values),
            4,
        )
    )

    print(
        "Std Dev:",
        round(
            statistics.stdev(values),
            4,
        )
    )

    # --------------------------------------------------------
    # Compare with current Heat Exposure
    # --------------------------------------------------------

    # Load the existing heat exposure results.
    with open(
    "cooling_priority_v2_results.json",
    "r",
    encoding="utf-8",
    ) as file:
        heat_records = json.load(file)

    heat_by_tile = {
        item["tile_id"]:
            item["heat_exposure_score"]
        for item in heat_records
    }

    heat_scores = []
    burden_scores = []

    for feature in features:

        properties = feature.get(
            "properties",
            {},
        )

        tile_id = properties.get(
            "tile_id"
        )

        value = properties.get(
            "value"
        )

        heat_score = heat_by_tile.get(
            tile_id
        )

        if (
            isinstance(value, (int, float))
            and isinstance(heat_score, (int, float))
        ):
            burden_scores.append(
                value
            )

            heat_scores.append(
                heat_score
            )

    correlation = rank_correlation(
        heat_scores,
        burden_scores,
    )

    print("\n" + "=" * 70)
    print(
        "HEAT EXPOSURE vs HEAT BURDEN"
    )
    print("=" * 70)

    print(
        "\nSpearman-like rank correlation:",
        round(
            correlation,
            4,
        )
        if correlation is not None
        else None,
    )

    if correlation is not None:

        if correlation >= 0.75:
            interpretation = (
                "Strong positive relationship"
            )

        elif correlation >= 0.50:
            interpretation = (
                "Moderate positive relationship"
            )

        elif correlation >= 0.25:
            interpretation = (
                "Weak positive relationship"
            )

        elif correlation <= -0.25:
            interpretation = (
                "Negative relationship"
            )

        else:
            interpretation = (
                "Little relationship"
            )

        print(
            "Interpretation:",
            interpretation,
        )

    print("\nNo API requests were made.")
    print("Credits consumed: 0")


if __name__ == "__main__":
    main()