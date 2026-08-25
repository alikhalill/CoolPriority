import pandas as pd

from policy_comparison import (
    POLICIES,
    compare_policies,
)


# ============================================================
# Run multiple budget scenarios
# ============================================================

def run_budget_scenarios(
    df,
    budgets,
):
    """
    Run all policies across multiple budgets.
    """

    results = []

    for budget in budgets:

        comparison = compare_policies(
            df,
            budget,
        )

        for policy_name in POLICIES:

            result = comparison[
                policy_name
            ]

            results.append(
                {
                    "Budget": budget,

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
                        ", ".join(
                            result["selected"][
                                "TRACT_NAME"
                            ]
                            .astype(str)
                            .tolist()
                        ),
                }
            )

    return pd.DataFrame(
        results
    )


# ============================================================
# Calculate marginal benefits
# ============================================================

def calculate_marginal_benefit(
    scenario_df,
):
    """
    Calculate the gain from adding one more
    intervention.

    Example:

    Budget 3 → Budget 4

    Population Gain
    Priority Gain
    Impact Gain
    """

    scenario_df = (
        scenario_df
        .copy()
        .sort_values(
            [
                "Policy",
                "Budget",
            ]
        )
        .reset_index(drop=True)
    )

    scenario_df[
        "Population Coverage Gain"
    ] = 0.0

    scenario_df[
        "Priority Coverage Gain"
    ] = 0.0

    scenario_df[
        "Impact Gain"
    ] = 0.0

    for policy in scenario_df[
        "Policy"
    ].unique():

        policy_mask = (
            scenario_df["Policy"]
            == policy
        )

        policy_rows = (
            scenario_df[
                policy_mask
            ]
            .sort_values(
                "Budget"
            )
        )

        previous_population = None
        previous_priority = None
        previous_impact = None

        for index, row in policy_rows.iterrows():

            if previous_population is None:

                population_gain = 0.0
                priority_gain = 0.0
                impact_gain = 0.0

            else:

                population_gain = (
                    row[
                        "Population Coverage"
                    ]
                    -
                    previous_population
                )

                priority_gain = (
                    row[
                        "Priority Coverage"
                    ]
                    -
                    previous_priority
                )

                impact_gain = (
                    row[
                        "Impact Score"
                    ]
                    -
                    previous_impact
                )

            scenario_df.loc[
                index,
                "Population Coverage Gain",
            ] = round(
                population_gain,
                2,
            )

            scenario_df.loc[
                index,
                "Priority Coverage Gain",
            ] = round(
                priority_gain,
                2,
            )

            scenario_df.loc[
                index,
                "Impact Gain",
            ] = round(
                impact_gain,
                2,
            )

            previous_population = (
                row[
                    "Population Coverage"
                ]
            )

            previous_priority = (
                row[
                    "Priority Coverage"
                ]
            )

            previous_impact = (
                row[
                    "Impact Score"
                ]
            )

    return scenario_df


# ============================================================
# Get value of next intervention
# ============================================================

def get_next_intervention_value(
    scenario_df,
    policy,
    current_budget,
):
    """
    Return what happens if one additional
    intervention is added.
    """

    policy_df = (
        scenario_df[
            scenario_df["Policy"]
            == policy
        ]
        .sort_values(
            "Budget"
        )
    )

    current = policy_df[
        policy_df["Budget"]
        == current_budget
    ]

    next_budget = (
        current_budget + 1
    )

    next_row = policy_df[
        policy_df["Budget"]
        == next_budget
    ]

    if current.empty or next_row.empty:

        return None

    current = current.iloc[0]
    next_row = next_row.iloc[0]

    return {
        "current_budget":
            current_budget,

        "next_budget":
            next_budget,

        "population_coverage":
            next_row[
                "Population Coverage"
            ],

        "priority_coverage":
            next_row[
                "Priority Coverage"
            ],

        "impact_score":
            next_row[
                "Impact Score"
            ],

        "population_gain":
            round(
                next_row[
                    "Population Coverage"
                ]
                -
                current[
                    "Population Coverage"
                ],
                2,
            ),

        "priority_gain":
            round(
                next_row[
                    "Priority Coverage"
                ]
                -
                current[
                    "Priority Coverage"
                ],
                2,
            ),

        "impact_gain":
            round(
                next_row[
                    "Impact Score"
                ]
                -
                current[
                    "Impact Score"
                ],
                2,
            ),
    }


# ============================================================
# Best policy for objective
# ============================================================

def recommend_policy(
    scenario_df,
    budget,
    objective,
):
    """
    Recommend a policy depending on objective.

    objective options:

    - priority
    - population
    - balanced
    """

    rows = scenario_df[
        scenario_df["Budget"]
        == budget
    ].copy()

    if rows.empty:
        return None

    if objective == "priority":

        row = rows.loc[
            rows[
                "Priority Coverage"
            ].idxmax()
        ]

    elif objective == "population":

        row = rows.loc[
            rows[
                "Population Coverage"
            ].idxmax()
        ]

    elif objective == "balanced":

        rows[
            "_balanced_score"
        ] = (
            rows[
                "Population Coverage"
            ]
            +
            rows[
                "Priority Coverage"
            ]
        ) / 2.0

        row = rows.loc[
            rows[
                "_balanced_score"
            ].idxmax()
        ]

    else:

        raise ValueError(
            "Unknown objective."
        )

    return {
        "policy":
            row["Policy"],

        "population_coverage":
            row[
                "Population Coverage"
            ],

        "priority_coverage":
            row[
                "Priority Coverage"
            ],

        "impact_score":
            row[
                "Impact Score"
            ],
    }


# ============================================================
# Build clean comparison table
# ============================================================

def build_summary_table(
    scenario_df,
):

    return (
        scenario_df[
            [
                "Budget",
                "Policy",
                "Population Coverage",
                "Priority Coverage",
                "Population Coverage Gain",
                "Priority Coverage Gain",
                "Impact Score",
                "Impact Gain",
                "Selected Areas",
            ]
        ]
        .sort_values(
            [
                "Budget",
                "Policy",
            ]
        )
        .reset_index(
            drop=True
        )
    )