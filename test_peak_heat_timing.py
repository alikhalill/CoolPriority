import json

from heat_trajectory import (
    extract_peak_heat_timing,
    summarize_peak_heat_timing,
    build_hour_distribution,
    interpret_peak_timing,
)


FILE_NAME = "time_of_measure_result.json"


print("=" * 70)
print("PEAK HEAT TIMING TEST")
print("=" * 70)


# ============================================================
# Load FortyGuard time_of_measure result
# ============================================================

print(
    f"\nLoading: {FILE_NAME}"
)

with open(
    FILE_NAME,
    "r",
    encoding="utf-8",
) as file:

    data = json.load(file)

print(
    "✅ Saved FortyGuard result loaded."
)


# ============================================================
# Extract peak timing
# ============================================================

timing = extract_peak_heat_timing(
    data
)

print(
    "\nTiles:",
    len(timing)
)


# ============================================================
# Display sample
# ============================================================

print(
    "\n" + "=" * 70
)

print(
    "PEAK TIMING SAMPLE"
)

print(
    "=" * 70
)

print(
    timing.head(10).to_string(
        index=False
    )
)


# ============================================================
# Summary
# ============================================================

summary = summarize_peak_heat_timing(
    timing
)

print(
    "\n" + "=" * 70
)

print(
    "PEAK HEAT TIMING SUMMARY"
)

print(
    "=" * 70
)

for key, value in summary.items():

    print(
        f"{key}: {value}"
    )


# ============================================================
# Hour distribution
# ============================================================

distribution = build_hour_distribution(
    timing
)

print(
    "\n" + "=" * 70
)

print(
    "HOURLY DISTRIBUTION"
)

print(
    "=" * 70
)

print(
    distribution.to_string(
        index=False
    )
)


# ============================================================
# Interpretation
# ============================================================

print(
    "\n" + "=" * 70
)

print(
    "INTERPRETATION"
)

print(
    "=" * 70
)

print(
    interpret_peak_timing(
        summary
    )
)


# ============================================================
# DONE
# ============================================================

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
    "\nNo additional FortyGuard API calls were made."
)

print(
    "Credits consumed by this test: 0"
)