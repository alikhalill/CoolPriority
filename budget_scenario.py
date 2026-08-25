import pandas as pd

from policy_comparison import (
    POLICIES,
    compare_policies,
)


def run_budget_scenarios(
    df,
    budgets,
):
    """
    Run the three decision policies across
    multiple intervention budgets.
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

            selected = result[
                "selected"
            ]

            selected_names = ", ".join(
                selected[
                    "TRACT_NAME"
                ]
                .astype(str)
                .tolist()
            )

            results.append(
                {
                    "Budget":
                        budget,

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
        results
    )