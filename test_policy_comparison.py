import json

import pandas as pd

from policy_comparison import (
    compare_policies,
    comparison_table,
)


# ============================================================
# Load current priority GeoJSON
# ============================================================

with open(
    "tract_cooling_priority.geojson",
    "r",
    encoding="utf-8",
) as file:

    geojson = json.load(file)


records = []

for feature in geojson["features"]:

    props = feature.get(
        "properties",
        {},
    )

    records.append(
        {
            "GEOID":
                props.get(
                    "GEOID"
                ),

            "TRACT_NAME":
                props.get(
                    "TRACT_NAME"
                ),

            "cooling_priority_score":
                props.get(
                    "cooling_priority_score"
                ),
        }
    )


df = pd.DataFrame(
    records
)


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

svi_ny = svi[
    svi["ST_ABBR"] == "NY"
][
    [
        "FIPS",
        "E_TOTPOP",
    ]
].copy()

svi_ny = svi_ny.rename(
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
    svi_ny,
    on="GEOID",
    how="left",
)


# ============================================================
# Compare policies
# ============================================================

results = compare_policies(
    df,
    budget=3,
)

table = comparison_table(
    results
)


print("=" * 70)
print(
    "POLICY WHAT-IF COMPARISON"
)
print("=" * 70)

print()

print(
    table.to_string(
        index=False
    )
)


# ============================================================
# Detailed results
# ============================================================

print(
    "\n" + "=" * 70
)

for policy_name, result in results.items():

    print(
        f"\n{policy_name}"
    )

    print(
        "Selected:",
        ", ".join(
            result["selected"][
                "TRACT_NAME"
            ]
            .astype(str)
            .tolist()
        )
    )

    print(
        "Population Coverage:",
        f"{result['population_coverage']:.2f}%"
    )

    print(
        "Priority Coverage:",
        f"{result['priority_coverage']:.2f}%"
    )

    print(
        "Impact:",
        f"{result['impact_sum']:.2f}"
    )


print(
    "\nNo FortyGuard API calls were made."
)

print(
    "Credits consumed: 0"
)