import pandas as pd

from budget_scenario import (
    run_budget_scenarios,
)


# ============================================================
# Load Priority Data
# ============================================================

priority_df = pd.read_json(
    "tract_cooling_priority.json"
)


# ============================================================
# Prepare priority dataframe
# ============================================================

rows = []

for _, row in priority_df.iterrows():

    rows.append(
        {
            "GEOID":
                row["GEOID"],

            "TRACT_NAME":
                row["TRACT_NAME"],

            "cooling_priority_score":
                row[
                    "cooling_priority_score"
                ],
        }
    )

df = pd.DataFrame(
    rows
)


# ============================================================
# Add SVI 2022 Population
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

df["GEOID"] = (
    df["GEOID"]
    .astype(str)
    .str.zfill(11)
)

df = df.merge(
    svi,
    on="GEOID",
    how="left",
)


# ============================================================
# Budget Scenarios
# ============================================================

budgets = [
    1,
    2,
    3,
    5,
    7,
]


results = run_budget_scenarios(
    df,
    budgets,
)


# ============================================================
# Display
# ============================================================

print(
    "=" * 90
)

print(
    "WHAT-IF BUDGET SIMULATOR"
)

print(
    "=" * 90
)

print()

print(
    results.to_string(
        index=False
    )
)


# ============================================================
# Policy summaries
# ============================================================

print(
    "\n" + "=" * 90
)

print(
    "BUDGET TRADE-OFF SUMMARY"
)

print(
    "=" * 90
)


for policy in [
    "Need-First",
    "Balanced",
    "Reach-First",
]:

    print(
        f"\n{'=' * 20} {policy} {'=' * 20}"
    )

    policy_results = results[
        results[
            "Policy"
        ]
        == policy
    ]

    for _, row in policy_results.iterrows():

        print(
            f"Budget={int(row['Budget'])} | "
            f"Population={row['Population Coverage']:.2f}% | "
            f"Priority={row['Priority Coverage']:.2f}% | "
            f"Impact={row['Impact Score']:.2f}"
        )


print(
    "\nNo FortyGuard API calls were made."
)

print(
    "Credits consumed: 0"
)