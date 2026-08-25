import json


# ============================================================
# Files
# ============================================================

BASE_FILE = "fortyguard_svi_matched.json"
PRIORITY_FILE = "tract_cooling_priority.json"

OUTPUT_FILE = "resource_allocation_v3_results.json"


# ============================================================
# Configuration
# ============================================================

DEFAULT_BUDGET = 3

POLICIES = {
    "NEED-FIRST": {
        "need_weight": 0.85,
        "reach_weight": 0.15,
        "description": (
            "Prioritize the areas with the highest "
            "cooling need."
        ),
    },

    "BALANCED": {
        "need_weight": 0.70,
        "reach_weight": 0.30,
        "description": (
            "Balance cooling need with the number "
            "of people potentially affected."
        ),
    },

    "REACH-FIRST": {
        "need_weight": 0.40,
        "reach_weight": 0.60,
        "description": (
            "Prioritize larger population reach while "
            "retaining a meaningful heat/vulnerability signal."
        ),
    },
}


# ============================================================
# Load files
# ============================================================

def load_json(path):

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


# ============================================================
# Build unique population record per tract
# ============================================================

def build_population_by_tract(
    records,
):

    population_by_geoid = {}

    for record in records:

        geoid = str(
            record["GEOID"]
        ).zfill(11)

        if geoid not in population_by_geoid:

            population_by_geoid[geoid] = {
                "GEOID": geoid,
                "population": int(
                    record["E_TOTPOP"]
                ),
            }

    return population_by_geoid


# ============================================================
# Merge priority + population
# ============================================================

def merge_tract_data(
    priority_records,
    population_by_geoid,
):

    merged = []

    for tract in priority_records:

        geoid = str(
            tract["GEOID"]
        ).zfill(11)

        population_record = (
            population_by_geoid.get(
                geoid
            )
        )

        if population_record is None:

            raise RuntimeError(
                f"Population missing for GEOID {geoid}"
            )

        item = {
            "GEOID": geoid,

            "TRACT_NAME":
                tract["TRACT_NAME"],

            "population":
                population_record[
                    "population"
                ],

            "cooling_priority_score":
                float(
                    tract[
                        "cooling_priority_score"
                    ]
                ),

            "heat_exposure_score":
                float(
                    tract[
                        "heat_exposure"
                    ][
                        "heat_exposure_score"
                    ]
                ),

            "social_vulnerability_score":
                float(
                    tract[
                        "social_vulnerability"
                    ][
                        "RPL_THEMES"
                    ]
                ),
        }

        merged.append(
            item
        )

    return merged


# ============================================================
# Percentile ranking
# ============================================================

def percentile_rank(
    values,
    value,
):

    if not values:
        return 0.0

    less_or_equal = sum(
        item <= value
        for item in values
    )

    return (
        (
            less_or_equal - 1
        )
        /
        max(
            len(values) - 1,
            1,
        )
    ) * 100.0


# ============================================================
# Add population reach percentile
# ============================================================

def add_population_percentiles(
    tracts,
):

    populations = [
        item["population"]
        for item in tracts
    ]

    for item in tracts:

        item[
            "population_reach_score"
        ] = round(
            percentile_rank(
                populations,
                item["population"],
            ),
            2,
        )

    return tracts


# ============================================================
# Calculate policy impact
# ============================================================

def calculate_policy_scores(
    tracts,
    policy_name,
):

    if policy_name not in POLICIES:

        raise ValueError(
            f"Unknown policy: {policy_name}"
        )

    policy = POLICIES[
        policy_name
    ]

    need_weight = policy[
        "need_weight"
    ]

    reach_weight = policy[
        "reach_weight"
    ]

    results = []

    for item in tracts:

        need = (
            item[
                "cooling_priority_score"
            ]
        )

        reach = (
            item[
                "population_reach_score"
            ]
        )

        impact = (
            need * need_weight
            +
            reach * reach_weight
        )

        result = dict(
            item
        )

        result[
            "need_weight"
        ] = need_weight

        result[
            "reach_weight"
        ] = reach_weight

        result[
            "impact_score"
        ] = round(
            impact,
            2,
        )

        results.append(
            result
        )

    results.sort(
        key=lambda item:
        item["impact_score"],
        reverse=True,
    )

    return results


# ============================================================
# Allocate budget
# ============================================================

def allocate_budget(
    ranked,
    budget,
):

    if budget <= 0:
        raise ValueError(
            "Budget must be greater than zero."
        )

    actual_budget = min(
        budget,
        len(ranked),
    )

    return ranked[
        :actual_budget
    ]


# ============================================================
# Coverage
# ============================================================

def calculate_coverage(
    selected,
    all_tracts,
):

    total_population = sum(
        item["population"]
        for item in all_tracts
    )

    selected_population = sum(
        item["population"]
        for item in selected
    )

    total_priority = sum(
        item[
            "cooling_priority_score"
        ]
        for item in all_tracts
    )

    selected_priority = sum(
        item[
            "cooling_priority_score"
        ]
        for item in selected
    )

    total_impact = sum(
        item["impact_score"]
        for item in selected
    )

    population_coverage = (
        (
            selected_population
            /
            total_population
        ) * 100.0
        if total_population > 0
        else 0.0
    )

    priority_coverage = (
        (
            selected_priority
            /
            total_priority
        ) * 100.0
        if total_priority > 0
        else 0.0
    )

    return {
        "selected_population":
            selected_population,

        "total_population":
            total_population,

        "population_coverage_percent":
            round(
                population_coverage,
                2,
            ),

        "selected_priority_sum":
            round(
                selected_priority,
                2,
            ),

        "total_priority_sum":
            round(
                total_priority,
                2,
            ),

        "priority_coverage_percent":
            round(
                priority_coverage,
                2,
            ),

        "selected_impact_sum":
            round(
                total_impact,
                2,
            ),
    }


# ============================================================
# Explain decision
# ============================================================

def explain(
    item,
    policy_name,
):

    need = item[
        "cooling_priority_score"
    ]

    reach = item[
        "population_reach_score"
    ]

    population = item[
        "population"
    ]

    if policy_name == "NEED-FIRST":

        if need >= 75:
            return (
                "Selected because the area has "
                "very high cooling need."
            )

        return (
            "Selected primarily because of its "
            "cooling need under the Need-First policy."
        )

    if policy_name == "REACH-FIRST":

        if reach >= 75:
            return (
                "Selected because the area can "
                "potentially reach a large population "
                f"({population:,})."
            )

        return (
            "Selected because it provides a favorable "
            "balance between need and population reach."
        )

    # Balanced
    if (
        need >= 75
        and reach >= 75
    ):
        return (
            "Selected because it combines very high "
            "cooling need with high population reach."
        )

    if need >= 75:

        return (
            "Selected because high cooling need "
            "remains the dominant driver."
        )

    if reach >= 75:

        return (
            "Selected because strong population reach "
            "meaningfully increases its impact."
        )

    return (
        "Selected because of the combined cooling "
        "need and population reach."
    )


# ============================================================
# Run one policy
# ============================================================

def run_policy(
    tracts,
    policy_name,
    budget,
):

    ranked = calculate_policy_scores(
        tracts,
        policy_name,
    )

    selected = allocate_budget(
        ranked,
        budget,
    )

    coverage = calculate_coverage(
        selected,
        tracts,
    )

    return {
        "policy": policy_name,

        "policy_description":
            POLICIES[
                policy_name
            ]["description"],

        "budget": min(
            budget,
            len(ranked),
        ),

        "selected": selected,

        "coverage": coverage,

        "ranking": ranked,
    }


# ============================================================
# Compare policies
# ============================================================

def compare_policies(
    tracts,
    budget,
):

    comparison = {}

    for policy_name in POLICIES:

        comparison[
            policy_name
        ] = run_policy(
            tracts,
            policy_name,
            budget,
        )

    return comparison


# ============================================================
# Print one policy
# ============================================================

def print_policy(
    result,
):

    policy_name = result[
        "policy"
    ]

    print(
        "\n" + "=" * 70
    )

    print(
        policy_name
    )

    print(
        "=" * 70
    )

    print(
        result[
            "policy_description"
        ]
    )

    print(
        f"\nBudget: "
        f"{result['budget']}"
    )

    print(
        "\nRECOMMENDED ALLOCATION"
    )

    for rank, item in enumerate(
        result["selected"],
        start=1,
    ):

        print(
            f"\n#{rank}"
        )

        print(
            f"GEOID: "
            f"{item['GEOID']}"
        )

        print(
            f"Tract: "
            f"{item['TRACT_NAME']}"
        )

        print(
            f"Population: "
            f"{item['population']:,}"
        )

        print(
            f"Cooling Priority: "
            f"{item['cooling_priority_score']:.2f}"
        )

        print(
            f"Population Percentile: "
            f"{item['population_reach_score']:.2f}"
        )

        print(
            f"Impact Score: "
            f"{item['impact_score']:.2f}"
        )

        print(
            "Why:"
        )

        print(
            explain(
                item,
                policy_name,
            )
        )

    coverage = result[
        "coverage"
    ]

    print(
        "\nCOVERAGE"
    )

    print(
        f"Population: "
        f"{coverage['selected_population']:,} / "
        f"{coverage['total_population']:,} "
        f"({coverage['population_coverage_percent']:.2f}%)"
    )

    print(
        f"Priority Coverage: "
        f"{coverage['priority_coverage_percent']:.2f}%"
    )

    print(
        f"Selected Impact Sum: "
        f"{coverage['selected_impact_sum']:.2f}"
    )


# ============================================================
# Save
# ============================================================

def save_results(
    comparison,
):

    output = {
        "model": {
            "name":
                "Resource Allocation V3",

            "population_normalization":
                "Percentile Rank",

            "policies":
                POLICIES,
        },

        "results":
            comparison,
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

    print(
        "=" * 70
    )

    print(
        "RESOURCE ALLOCATION V3"
    )

    print(
        "=" * 70
    )

    base_records = load_json(
        BASE_FILE
    )

    priority_records = load_json(
        PRIORITY_FILE
    )

    population_by_tract = (
        build_population_by_tract(
            base_records
        )
    )

    tracts = merge_tract_data(
        priority_records,
        population_by_tract,
    )

    tracts = (
        add_population_percentiles(
            tracts
        )
    )

    print(
        f"\nCensus Tracts: "
        f"{len(tracts)}"
    )

    print(
        f"Intervention Budget: "
        f"{DEFAULT_BUDGET}"
    )

    # --------------------------------------------------------
    # Compare all policies
    # --------------------------------------------------------

    comparison = (
        compare_policies(
            tracts,
            DEFAULT_BUDGET,
        )
    )

    # --------------------------------------------------------
    # Print
    # --------------------------------------------------------

    for policy_name in POLICIES:

        print_policy(
            comparison[
                policy_name
            ]
        )

    # --------------------------------------------------------
    # Policy comparison summary
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "POLICY COMPARISON"
    )

    print(
        "=" * 70
    )

    for policy_name in POLICIES:

        result = comparison[
            policy_name
        ]

        selected_names = [
            item["TRACT_NAME"]
            for item in result[
                "selected"
            ]
        ]

        coverage = result[
            "coverage"
        ]

        print(
            f"\n{policy_name}"
        )

        print(
            "Selected:",
            ", ".join(
                selected_names
            )
        )

        print(
            f"Population Coverage: "
            f"{coverage['population_coverage_percent']:.2f}%"
        )

        print(
            f"Priority Coverage: "
            f"{coverage['priority_coverage_percent']:.2f}%"
        )

        print(
            f"Impact Sum: "
            f"{coverage['selected_impact_sum']:.2f}"
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_results(
        comparison
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "DONE"
    )

    print(
        "=" * 70
    )

    print(
        f"\nSaved to:"
        f"\n{OUTPUT_FILE}"
    )

    print(
        "\nFortyGuard API calls: 0"
    )


if __name__ == "__main__":
    main()