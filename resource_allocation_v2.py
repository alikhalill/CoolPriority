import json


# ============================================================
# Files
# ============================================================

INPUT_FILE = "fortyguard_svi_matched.json"
PRIORITY_FILE = "tract_cooling_priority.json"

OUTPUT_FILE = (
    "resource_allocation_v2_results.json"
)


# ============================================================
# Configuration
# ============================================================

DEFAULT_BUDGET = 3

NEED_WEIGHT = 0.70
REACH_WEIGHT = 0.30


# ============================================================
# Load base data
# ============================================================

def load_base_data():

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        records = json.load(file)

    if not isinstance(records, list):
        raise RuntimeError(
            "fortyguard_svi_matched.json "
            "must contain a list."
        )

    return records


# ============================================================
# Extract unique Census Tracts
#
# Multiple FortyGuard tiles may belong to the
# same Census Tract.
# ============================================================

def aggregate_population_by_tract(
    records,
):

    grouped = {}

    for record in records:

        geoid = str(
            record["GEOID"]
        ).zfill(11)

        if geoid not in grouped:

            grouped[geoid] = {
                "GEOID": geoid,

                "TRACT_NAME":
                    record["NAME"],

                "population":
                    record["E_TOTPOP"],
            }

    return list(
        grouped.values()
    )


# ============================================================
# Load existing tract-level priority
# ============================================================

def load_priority_data():

    with open(
        PRIORITY_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        tracts = json.load(file)

    if not isinstance(
        tracts,
        list,
    ):
        raise RuntimeError(
            "tract_cooling_priority.json "
            "must contain a list."
        )

    return tracts


# ============================================================
# Merge Priority + Population
# ============================================================

def merge_data(
    priority_tracts,
    population_tracts,
):

    population_by_geoid = {
        item["GEOID"]:
            item
        for item in population_tracts
    }

    merged = []

    for tract in priority_tracts:

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
                f"Population missing for "
                f"GEOID {geoid}"
            )

        item = dict(
            tract
        )

        item["population"] = (
            population_record[
                "population"
            ]
        )

        merged.append(
            item
        )

    return merged


# ============================================================
# Normalize Population
# ============================================================

def normalize_population(
    tracts,
):

    populations = [
        float(
            item["population"]
        )
        for item in tracts
    ]

    minimum = min(
        populations
    )

    maximum = max(
        populations
    )

    for item in tracts:

        population = float(
            item["population"]
        )

        if maximum == minimum:

            normalized = 50.0

        else:

            normalized = (
                (
                    population
                    - minimum
                )
                /
                (
                    maximum
                    - minimum
                )
            ) * 100.0

        item[
            "population_reach_score"
        ] = round(
            normalized,
            2,
        )

    return tracts


# ============================================================
# Calculate Impact Score
# ============================================================

def calculate_impact_scores(
    tracts,
):

    for item in tracts:

        need = float(
            item[
                "cooling_priority_score"
            ]
        )

        reach = float(
            item[
                "population_reach_score"
            ]
        )

        impact = (
            need * NEED_WEIGHT
            +
            reach * REACH_WEIGHT
        )

        item[
            "impact_score"
        ] = round(
            impact,
            2,
        )

        item[
            "need_score"
        ] = round(
            need,
            2,
        )

        item[
            "reach_score"
        ] = round(
            reach,
            2,
        )

    return tracts


# ============================================================
# Optimize
# ============================================================

def optimize(
    tracts,
    budget,
):

    if budget <= 0:
        raise ValueError(
            "Budget must be greater than zero."
        )

    if budget > len(tracts):
        budget = len(tracts)

    ranked = sorted(
        tracts,
        key=lambda item:
        item["impact_score"],
        reverse=True,
    )

    selected = ranked[
        :budget
    ]

    return selected, ranked


# ============================================================
# Explain
# ============================================================

def explain(
    item,
):

    need = item[
        "need_score"
    ]

    reach = item[
        "reach_score"
    ]

    population = item[
        "population"
    ]

    if (
        need >= 75
        and reach >= 75
    ):

        return (
            "Selected because the area has "
            "very high cooling need and a "
            "large population reach."
        )

    if need >= 75:

        return (
            "Selected primarily because of "
            "very high cooling need."
        )

    if reach >= 75:

        return (
            "Selected because the intervention "
            "could reach a large population."
        )

    return (
        "Selected because of the combined "
        "cooling need and population reach."
    )


# ============================================================
# Coverage
# ============================================================

def calculate_coverage(
    selected,
    all_tracts,
):

    total_population = sum(
        int(
            item["population"]
        )
        for item in all_tracts
    )

    selected_population = sum(
        int(
            item["population"]
        )
        for item in selected
    )

    total_priority = sum(
        float(
            item[
                "cooling_priority_score"
            ]
        )
        for item in all_tracts
    )

    selected_priority = sum(
        float(
            item[
                "cooling_priority_score"
            ]
        )
        for item in selected
    )

    population_coverage = (
        selected_population
        / total_population
        * 100.0
        if total_population
        else 0.0
    )

    priority_coverage = (
        selected_priority
        / total_priority
        * 100.0
        if total_priority
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
    }


# ============================================================
# Save
# ============================================================

def save_results(
    budget,
    selected,
    ranked,
    coverage,
):

    output = {
        "model": {
            "name":
                "Population-Aware "
                "Resource Allocation V2",

            "budget":
                budget,

            "need_weight":
                NEED_WEIGHT,

            "reach_weight":
                REACH_WEIGHT,
        },

        "recommended_allocation": [
            {
                "GEOID":
                    item["GEOID"],

                "TRACT_NAME":
                    item["TRACT_NAME"],

                "population":
                    item["population"],

                "cooling_priority_score":
                    item[
                        "cooling_priority_score"
                    ],

                "population_reach_score":
                    item[
                        "population_reach_score"
                    ],

                "impact_score":
                    item[
                        "impact_score"
                    ],

                "explanation":
                    explain(item),
            }

            for item in selected
        ],

        "coverage":
            coverage,

        "full_ranking": [
            {
                "GEOID":
                    item["GEOID"],

                "TRACT_NAME":
                    item["TRACT_NAME"],

                "population":
                    item["population"],

                "cooling_priority_score":
                    item[
                        "cooling_priority_score"
                    ],

                "population_reach_score":
                    item[
                        "population_reach_score"
                    ],

                "impact_score":
                    item["impact_score"],
            }

            for item in ranked
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
        "POPULATION-AWARE RESOURCE "
        "ALLOCATION V2"
    )
    print("=" * 70)

    base_records = (
        load_base_data()
    )

    priority_tracts = (
        load_priority_data()
    )

    print(
        f"\nFortyGuard/SVI tile records: "
        f"{len(base_records)}"
    )

    print(
        f"Census Tracts: "
        f"{len(priority_tracts)}"
    )

    # --------------------------------------------------------
    # Population by tract
    # --------------------------------------------------------

    population_tracts = (
        aggregate_population_by_tract(
            base_records
        )
    )

    print(
        f"Population records: "
        f"{len(population_tracts)}"
    )

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    merged = merge_data(
        priority_tracts,
        population_tracts,
    )

    # --------------------------------------------------------
    # Normalize population
    # --------------------------------------------------------

    merged = normalize_population(
        merged
    )

    # --------------------------------------------------------
    # Impact score
    # --------------------------------------------------------

    merged = calculate_impact_scores(
        merged
    )

    # --------------------------------------------------------
    # Optimize
    # --------------------------------------------------------

    selected, ranked = optimize(
        merged,
        DEFAULT_BUDGET,
    )

    # --------------------------------------------------------
    # Coverage
    # --------------------------------------------------------

    coverage = calculate_coverage(
        selected,
        merged,
    )

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "RECOMMENDED ALLOCATION V2"
    )

    print(
        "=" * 70
    )

    for rank, item in enumerate(
        selected,
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
            f"Population Reach: "
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
            explain(item)
        )

    # --------------------------------------------------------
    # Coverage
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "IMPACT COVERAGE"
    )

    print(
        "=" * 70
    )

    print(
        f"Selected population: "
        f"{coverage['selected_population']:,}"
    )

    print(
        f"Total population: "
        f"{coverage['total_population']:,}"
    )

    print(
        f"Population coverage: "
        f"{coverage['population_coverage_percent']:.2f}%"
    )

    print(
        f"Priority coverage: "
        f"{coverage['priority_coverage_percent']:.2f}%"
    )

    # --------------------------------------------------------
    # Compare with old ranking
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "TOP 5 IMPACT RANKING"
    )

    print(
        "=" * 70
    )

    for rank, item in enumerate(
        ranked[:5],
        start=1,
    ):

        print(
            f"#{rank} "
            f"{item['TRACT_NAME']} | "
            f"Priority="
            f"{item['cooling_priority_score']:.2f} | "
            f"Population="
            f"{item['population']:,} | "
            f"Reach="
            f"{item['population_reach_score']:.2f} | "
            f"Impact="
            f"{item['impact_score']:.2f}"
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