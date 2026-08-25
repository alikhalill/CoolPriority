import pandas as pd


POLICIES = {
    "Need-First": {
        "need_weight": 0.85,
        "reach_weight": 0.15,
        "description": (
            "Prioritize areas with the highest cooling need."
        ),
    },

    "Balanced": {
        "need_weight": 0.70,
        "reach_weight": 0.30,
        "description": (
            "Balance cooling need with potential population reach."
        ),
    },

    "Reach-First": {
        "need_weight": 0.40,
        "reach_weight": 0.60,
        "description": (
            "Prioritize population reach while retaining "
            "heat/vulnerability need."
        ),
    },
}


def percentile_rank(values, value):

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
        max(len(values) - 1, 1)
    ) * 100.0


def prepare_population(df):

    df = df.copy()

    populations = (
        df["population"]
        .fillna(0)
        .tolist()
    )

    df["population_reach_score"] = (
        df["population"]
        .fillna(0)
        .apply(
            lambda value:
            percentile_rank(
                populations,
                value,
            )
        )
    )

    return df


def run_policy(
    df,
    policy_name,
    budget,
):

    policy = POLICIES[
        policy_name
    ]

    work = df.copy()

    need_weight = policy[
        "need_weight"
    ]

    reach_weight = policy[
        "reach_weight"
    ]

    work["impact_score"] = (
        work["cooling_priority_score"]
        * need_weight
        +
        work["population_reach_score"]
        * reach_weight
    )

    work = (
        work
        .sort_values(
            "impact_score",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )

    selected = work.head(
        min(
            budget,
            len(work),
        )
    ).copy()

    total_population = (
        work["population"]
        .fillna(0)
        .sum()
    )

    selected_population = (
        selected["population"]
        .fillna(0)
        .sum()
    )

    total_priority = (
        work["cooling_priority_score"]
        .sum()
    )

    selected_priority = (
        selected["cooling_priority_score"]
        .sum()
    )

    return {
        "policy": policy_name,

        "selected": selected,

        "selected_population":
            int(selected_population),

        "population_coverage":
            round(
                (
                    selected_population
                    /
                    total_population
                    * 100
                )
                if total_population
                else 0,
                2,
            ),

        "priority_coverage":
            round(
                (
                    selected_priority
                    /
                    total_priority
                    * 100
                )
                if total_priority
                else 0,
                2,
            ),

        "impact_sum":
            round(
                selected[
                    "impact_score"
                ].sum(),
                2,
            ),
    }


def compare_policies(
    df,
    budget,
):

    prepared = prepare_population(
        df
    )

    results = {}

    for policy_name in POLICIES:

        results[
            policy_name
        ] = run_policy(
            prepared,
            policy_name,
            budget,
        )

    return results


def comparison_table(
    results,
):

    rows = []

    for policy_name, result in results.items():

        selected_names = ", ".join(
            result["selected"][
                "TRACT_NAME"
            ]
            .astype(str)
            .tolist()
        )

        rows.append(
            {
                "Policy":
                    policy_name,

                "Population Coverage":
                    result[
                        "population_coverage"
                    ],

                "Priority Coverage":
                    result[
                        "priority_coverage"
                    ],

                "Impact Score":
                    result[
                        "impact_sum"
                    ],

                "Selected Areas":
                    selected_names,
            }
        )

    return pd.DataFrame(
        rows
    )