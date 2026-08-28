from heat_trajectory import (
    load_time_series,
    extract_trajectory,
    summarize_trajectory,
)


print("=" * 70)
print("HEAT TRAJECTORY TEST")
print("=" * 70)


FILE_NAME = "heatmap_time_range_result.json"


# ============================================================
# 1. Load saved FortyGuard result
# ============================================================

print(
    f"\nLoading: {FILE_NAME}"
)

data = load_time_series(
    FILE_NAME
)

print(
    "✅ Saved FortyGuard result loaded."
)


# ============================================================
# 2. Extract trajectory
# ============================================================

trajectory = extract_trajectory(
    data
)

print(
    "\nTrajectory rows:",
    len(trajectory)
)


# ============================================================
# 3. Display trajectory
# ============================================================

print(
    "\n" + "=" * 70
)

print(
    "TIME TRAJECTORY"
)

print(
    "=" * 70
)

if trajectory.empty:

    print(
        "\n❌ No trajectory data found."
    )

else:

    print(
        trajectory.to_string(
            index=False
        )
    )


# ============================================================
# 4. Summary
# ============================================================

summary = summarize_trajectory(
    trajectory,
    threshold=30.0,
)


print(
    "\n" + "=" * 70
)

print(
    "TRAJECTORY SUMMARY"
)

print(
    "=" * 70
)

print(
    "Peak Temperature:",
    summary.get(
        "peak_temperature"
    ),
)

print(
    "Peak Time:",
    summary.get(
        "peak_time"
    ),
)

print(
    "Hours Above 30°C:",
    summary.get(
        "hours_above_threshold"
    ),
)

print(
    "First Above 30°C:",
    summary.get(
        "first_above_threshold"
    ),
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
    "\nNo FortyGuard API calls were made."
)

print(
    "Credits consumed: 0"
)