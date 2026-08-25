import pandas as pd

from budget_scenario_v2 import (
    run_budget_scenarios,
    calculate_marginal_benefit,
    get_next_intervention_value,
    recommend_policy,
    build_summary_table,
)


# ============================================================
# Load priority data
# ============================================================

priority_df = pd.read_json(
    "tract_cooling_priority.json"
)


priority_df = priority_df[
    [
        "GEOID",
        "TRACT_NAME",
        "cooling_priority_score",
    ]
].copy()


# ============================================================
# Load population from SVI 2022
# ============================================================

svi = pd.read_csv(
    "data/SVI_2022_US.csv",
    dtype={
        "FIPS": str
    },
)

svi["FIPS"] = (
    svi["FIPS"]
    .astype(str)
    .str.replace(
        ".0",
        "",
        regex=False,
    )
    .str.zfill(11)
)

svi = svi[
    svi["ST_ABBR"] == "NY"
][
    [
        "FIPS",
        "E_TOTPOP",
    ]
].copy()

svi = svi.rename(
    columns={
        "FIPS":
            "GEOID",

        "E_TOTPOP":
            "population",
    }
)

priority_df["GEOID"] = (
    priority_df["GEOID"]
    .astype(str)
    .str.zfill(11)
)

df = priority_df.merge(
    svi,
    on="GEOID",
    how="left",
)


# ============================================================
# Budgets
# ============================================================

budgets = [
    1,
    2,
    3,
    4,
    5,
    6,
    7,
]


# ============================================================
# Run scenarios
# ============================================================

scenario_df = run_budget_scenarios(
    df,
    budgets,
)


# ============================================================
# Calculate marginal benefits
# ============================================================

scenario_df = calculate_marginal_benefit(
    scenario_df
)


# ============================================================
# Summary
# ============================================================

summary = build_summary_table(
    scenario_df
)


print(
    "=" * 100
)

print(
    "BUDGET WHAT-IF + MARGINAL BENEFIT"
)

print(
    "=" * 100
)

print()

print(
    summary.to_string(
        index=False
    )
)


# ============================================================
# Value of next intervention
# ============================================================

print(
    "\n" + "=" * 100
)

print(
    "VALUE OF ONE MORE INTERVENTION"
)

print(
    "=" * 100
)

current_budget = 3

for policy in [
    "Need-First",
    "Balanced",
    "Reach-First",
]:

    value = (
        get_next_intervention_value(
            scenario_df,
            policy,
            current_budget,
        )
    )

    print(
        f"\n{policy}"
    )

    if value is None:

        print(
            "No next-budget scenario available."
        )

    else:

        print(
            f"Budget {value['current_budget']} "
            f"→ {value['next_budget']}"
        )

        print(
            f"Population Coverage Gain: "
            f"+{value['population_gain']:.2f}%"
        )

        print(
            f"Priority Coverage Gain: "
            f"+{value['priority_gain']:.2f}%"
        )

        print(
            f"Impact Gain: "
            f"+{value['impact_gain']:.2f}"
        )


# ============================================================
# Policy recommendations
# ============================================================

print(
    "\n" + "=" * 100
)

print(
    "POLICY RECOMMENDATIONS"
)

print(
    "=" * 100
)

for objective in [
    "priority",
    "population",
    "balanced",
]:

    result = recommend_policy(
        scenario_df,
        budget=3,
        objective=objective,
    )

    print(
        f"\nObjective: {objective}"
    )

    print(
        f"Recommended policy: "
        f"{result['policy']}"
    )

    print(
        f"Population Coverage: "
        f"{result['population_coverage']:.2f}%"
    )

    print(
        f"Priority Coverage: "
        f"{result['priority_coverage']:.2f}%"
    )

    print(
        f"Impact: "
        f"{result['impact_score']:.2f}"
    )


print(
    "\nNo FortyGuard API calls were made."
)

print(
    "Credits consumed: 0"
)