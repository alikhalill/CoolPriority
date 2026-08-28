from __future__ import annotations

import pandas as pd


# ============================================================
# INTERVENTION ASSUMPTIONS
# ============================================================
# These are scenario assumptions for the prototype.
# They are NOT measured real-world effects.
#
# The purpose is to answer:
# "What could happen if we apply a cooling intervention?"
# ============================================================

INTERVENTIONS = {
    "No Intervention": {
        "avg_temp_reduction": 0.0,
        "max_temp_reduction": 0.0,
        "priority_reduction_factor": 0.0,
        "description": "Baseline scenario.",
    },

    "Urban Trees / Shade": {
        "avg_temp_reduction": 1.0,
        "max_temp_reduction": 2.0,
        "priority_reduction_factor": 0.08,
        "description": (
            "Scenario assumption representing additional shade "
            "and cooling from urban vegetation."
        ),
    },

    "Cool Roofs": {
        "avg_temp_reduction": 0.7,
        "max_temp_reduction": 1.5,
        "priority_reduction_factor": 0.06,
        "description": (
            "Scenario assumption representing reflective/cool-roof "
            "interventions."
        ),
    },

    "Cooling Center": {
        "avg_temp_reduction": 0.0,
        "max_temp_reduction": 0.0,
        "priority_reduction_factor": 0.12,
        "description": (
            "Does not change ambient temperature directly; "
            "scenario represents reduction in effective cooling need "
            "where accessible cooling is provided."
        ),
    },
}


# ============================================================
# APPLY INTERVENTION
# ============================================================

def simulate_intervention(
    df: pd.DataFrame,
    intervention_name: str,
    coverage: float = 1.0,
) -> pd.DataFrame:
    """
    Simulate an intervention on a selected area.

    coverage:
        0.0 → no implementation
        1.0 → full assumed implementation

    Important:
    This is a scenario model, not a physical climate model.
    """

    if intervention_name not in INTERVENTIONS:
        raise ValueError(
            f"Unknown intervention: {intervention_name}"
        )

    if not 0.0 <= coverage <= 1.0:
        raise ValueError(
            "coverage must be between 0 and 1."
        )

    settings = INTERVENTIONS[
        intervention_name
    ]

    result = df.copy()

    baseline = pd.to_numeric(
        result[
            "cooling_priority_score"
        ],
        errors="coerce",
    ).fillna(0.0)

    # --------------------------------------------------------
    # Scenario priority reduction
    # --------------------------------------------------------

    reduction_factor = (
        settings[
            "priority_reduction_factor"
        ]
        * coverage
    )

    result[
        "simulated_priority_reduction"
    ] = (
        baseline
        * reduction_factor
    )

    result[
        "simulated_cooling_priority"
    ] = (
        baseline
        -
        result[
            "simulated_priority_reduction"
        ]
    )

    # --------------------------------------------------------
    # Optional temperature context
    # --------------------------------------------------------

    if "average_temperature" in result.columns:

        result[
            "simulated_average_temperature"
        ] = (
            pd.to_numeric(
                result[
                    "average_temperature"
                ],
                errors="coerce",
            )
            -
            (
                settings[
                    "avg_temp_reduction"
                ]
                * coverage
            )
        )

    if "maximum_temperature" in result.columns:

        result[
            "simulated_maximum_temperature"
        ] = (
            pd.to_numeric(
                result[
                    "maximum_temperature"
                ],
                errors="coerce",
            )
            -
            (
                settings[
                    "max_temp_reduction"
                ]
                * coverage
            )
        )

    return result


# ============================================================
# SUMMARY
# ============================================================

def summarize_intervention(
    baseline_df: pd.DataFrame,
    simulated_df: pd.DataFrame,
):
    baseline_priority = (
        baseline_df[
            "cooling_priority_score"
        ]
        .sum()
    )

    simulated_priority = (
        simulated_df[
            "simulated_cooling_priority"
        ]
        .sum()
    )

    reduction = (
        baseline_priority
        -
        simulated_priority
    )

    return {
        "baseline_priority_sum":
            round(
                baseline_priority,
                2,
            ),

        "simulated_priority_sum":
            round(
                simulated_priority,
                2,
            ),

        "priority_reduction":
            round(
                reduction,
                2,
            ),

        "priority_reduction_percent":
            round(
                (
                    reduction
                    /
                    baseline_priority
                    *
                    100
                )
                if baseline_priority
                else 0.0,
                2,
            ),
    }