import json


INPUT_FILE = "tract_cooling_priority.json"
OUTPUT_FILE = "resource_allocation_results.json"


# ============================================================
# Intervention Budget
# ============================================================

DEFAULT_BUDGET = 3


# ============================================================
# Load tract priorities
# ============================================================

def load_tracts():

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        tracts = json.load(file)

    if not isinstance(tracts, list):
        raise RuntimeError(
            "Expected tract_cooling_priority.json "
            "to contain a list."
        )

    return tracts


# ============================================================
# Calculate allocation score
# ============================================================

def calculate_allocation_value(tract):

    priority = float(
        tract["cooling_priority_score"]
    )

    heat = float(
        tract["heat_exposure"]["heat_exposure_score"]
    )

    vulnerability = float(
        tract[
            "social_vulnerability"
        ]["RPL_THEMES"]
    )

    # --------------------------------------------------------
    # Current MVP allocation value
    #
    # Priority remains the dominant factor.
    # Heat + vulnerability are retained for explanation.
    # --------------------------------------------------------

    value = (
        priority * 0.70
        +
        heat * 0.20
        +
        vulnerability * 0.10
    )

    return round(
        value,
        2,
    )


# ============================================================
# Generate recommended allocation
# ============================================================

def optimize_allocation(
    tracts,
    budget,
):

    if budget <= 0:
        raise ValueError(
            "Budget must be greater than zero."
        )

    if budget > len(tracts):
        budget = len(tracts)

    ranked = []

    for tract in tracts:

        allocation_value = (
            calculate_allocation_value(
                tract
            )
        )

        item = dict(tract)

        item[
            "allocation_value"
        ] = allocation_value

        ranked.append(
            item
        )

    ranked.sort(
        key=lambda item:
        item["allocation_value"],
        reverse=True,
    )

    selected = ranked[:budget]

    return selected, ranked


# ============================================================
# Explain allocation decision
# ============================================================

def explain_allocation(tract):

    priority = float(
        tract[
            "cooling_priority_score"
        ]
    )

    heat = float(
        tract[
            "heat_exposure"
        ]["heat_exposure_score"]
    )

    vulnerability = float(
        tract[
            "social_vulnerability"
        ]["RPL_THEMES"]
    )

    reasons = []

    if heat >= 75:
        reasons.append(
            "very high heat exposure"
        )

    elif heat >= 50:
        reasons.append(
            "high heat exposure"
        )

    if vulnerability >= 75:
        reasons.append(
            "very high social vulnerability"
        )

    elif vulnerability >= 50:
        reasons.append(
            "high social vulnerability"
        )

    if not reasons:
        reasons.append(
            "combined heat and vulnerability"
        )

    reason_text = " + ".join(
        reasons
    )

    return (
        f"Selected because of {reason_text}. "
        f"Cooling Priority = {priority:.2f}/100."
    )


# ============================================================
# Coverage summary
# ============================================================

def calculate_coverage(
    selected,
    all_tracts,
):

    selected_geoids = {
        tract["GEOID"]
        for tract in selected
    }

    total_priority = sum(
        float(
            tract[
                "cooling_priority_score"
            ]
        )
        for tract in all_tracts
    )

    selected_priority = sum(
        float(
            tract[
                "cooling_priority_score"
            ]
        )
        for tract in selected
    )

    if total_priority == 0:
        coverage = 0.0

    else:
        coverage = (
            selected_priority
            / total_priority
        ) * 100.0

    return {
        "selected_areas":
            len(selected_geoids),

        "total_areas":
            len(all_tracts),

        "selected_priority_sum":
            round(
                selected_priority,
                2,
            ),

        "all_priority_sum":
            round(
                total_priority,
                2,
            ),

        "priority_coverage_percent":
            round(
                coverage,
                2,
            ),
    }


# ============================================================
# Save result
# ============================================================

def save_results(
    budget,
    selected,
    ranked,
    coverage,
):

    output = {
        "optimization": {
            "budget":
                budget,

            "selected_areas":
                [
                    {
                        "GEOID":
                            tract["GEOID"],

                        "TRACT_NAME":
                            tract[
                                "TRACT_NAME"
                            ],

                        "cooling_priority_score":
                            tract[
                                "cooling_priority_score"
                            ],

                        "heat_exposure_score":
                            tract[
                                "heat_exposure"
                            ][
                                "heat_exposure_score"
                            ],

                        "social_vulnerability_score":
                            tract[
                                "social_vulnerability"
                            ][
                                "RPL_THEMES"
                            ],

                        "allocation_value":
                            tract[
                                "allocation_value"
                            ],

                        "explanation":
                            explain_allocation(
                                tract
                            ),
                    }
                    for tract in selected
                ],
        },

        "coverage":
            coverage,

        "full_ranking":
            [
                {
                    "GEOID":
                        tract["GEOID"],

                    "TRACT_NAME":
                        tract[
                            "TRACT_NAME"
                        ],

                    "cooling_priority_score":
                        tract[
                            "cooling_priority_score"
                        ],

                    "allocation_value":
                        tract[
                            "allocation_value"
                        ],
                }
                for tract in ranked
            ],
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            output,
            file,
            indent=4,
            ensure_ascii=False,
        )


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 70)
    print(
        "COOLING RESOURCE ALLOCATION OPTIMIZER"
    )
    print("=" * 70)

    tracts = load_tracts()

    print(
        f"\nAreas available: "
        f"{len(tracts)}"
    )

    print(
        f"Intervention budget: "
        f"{DEFAULT_BUDGET}"
    )

    selected, ranked = optimize_allocation(
        tracts,
        DEFAULT_BUDGET,
    )

    coverage = calculate_coverage(
        selected,
        tracts,
    )

    # --------------------------------------------------------
    # Recommended allocation
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        "RECOMMENDED ALLOCATION"
    )
    print("=" * 70)

    for rank, tract in enumerate(
        selected,
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
            f"Tract: "
            f"{tract['TRACT_NAME']}"
        )

        print(
            f"Cooling Priority: "
            f"{tract['cooling_priority_score']:.2f}"
        )

        print(
            f"Heat Exposure: "
            f"{tract['heat_exposure']['heat_exposure_score']:.2f}"
        )

        print(
            f"Social Vulnerability: "
            f"{tract['social_vulnerability']['RPL_THEMES']:.2f}"
        )

        print(
            f"Allocation Value: "
            f"{tract['allocation_value']:.2f}"
        )

        print(
            "Why:",
        )

        print(
            explain_allocation(
                tract
            )
        )

    # --------------------------------------------------------
    # Coverage
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        "ALLOCATION COVERAGE"
    )
    print("=" * 70)

    print(
        f"Selected areas: "
        f"{coverage['selected_areas']}"
    )

    print(
        f"Total areas: "
        f"{coverage['total_areas']}"
    )

    print(
        f"Selected priority sum: "
        f"{coverage['selected_priority_sum']}"
    )

    print(
        f"Overall priority sum: "
        f"{coverage['all_priority_sum']}"
    )

    print(
        f"Priority coverage: "
        f"{coverage['priority_coverage_percent']:.2f}%"
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_results(
        DEFAULT_BUDGET,
        selected,
        ranked,
        coverage,
    )

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)

    print(
        "\nSaved to:"
        f"\n{OUTPUT_FILE}"
    )

    print(
        "\nNo API requests were made."
    )

    print(
        "Credits consumed: 0"
    )


if __name__ == "__main__":
    main()