import json
import pandas as pd

from intervention_simulator import (
    simulate_intervention,
    summarize_intervention,
)


# ============================================================
# Load current priority data
# ============================================================

with open(
    "tract_cooling_priority.json",
    "r",
    encoding="utf-8",
) as file:
    data = json.load(file)


if isinstance(data, dict):
    records = data.get(
        "features",
        data.get(
            "data",
            []
        ),
    )
else:
    records = data


# ============================================================
# Build DataFrame
# ============================================================

rows = []

for item in records:

    if "properties" in item:
        item = item["properties"]

    rows.append(
        {
            "GEOID":
                item.get("GEOID"),

            "TRACT_NAME":
                item.get("TRACT_NAME"),

            "cooling_priority_score":
                item.get(
                    "cooling_priority_score"
                ),
        }
    )


df = pd.DataFrame(rows)

print("=" * 70)
print("INTERVENTION SIMULATOR TEST")
print("=" * 70)

print()
print(
    "Areas loaded:",
    len(df),
)


# ============================================================
# Test interventions
# ============================================================

for intervention in [
    "No Intervention",
    "Urban Trees / Shade",
    "Cool Roofs",
    "Cooling Center",
]:

    simulated = simulate_intervention(
        df,
        intervention,
        coverage=1.0,
    )

    summary = summarize_intervention(
        df,
        simulated,
    )

    print()
    print("=" * 70)
    print(intervention)
    print("=" * 70)

    print(
        "Baseline Priority:",
        summary[
            "baseline_priority_sum"
        ],
    )

    print(
        "Simulated Priority:",
        summary[
            "simulated_priority_sum"
        ],
    )

    print(
        "Priority Reduction:",
        summary[
            "priority_reduction"
        ],
    )

    print(
        "Priority Reduction %:",
        summary[
            "priority_reduction_percent"
        ],
    )


print()
print("=" * 70)
print("DONE")
print("=" * 70)

print(
    "\nNo FortyGuard API calls were made."
)

print(
    "Credits consumed: 0"
)