import json


INPUT_FILE = "tract_cooling_priority.json"
OUTPUT_FILE = "tract_priority_explanations.json"


HEAT_WEIGHT = 0.70
VULNERABILITY_WEIGHT = 0.30


def explain_priority(tract):
    heat_score = tract["heat_exposure"]["heat_exposure_score"]
    svi_score = tract["social_vulnerability"]["RPL_THEMES"]
    final_score = tract["cooling_priority_score"]
    label = tract["priority_label"]

    heat_contribution = heat_score * HEAT_WEIGHT
    vulnerability_contribution = (
        svi_score * VULNERABILITY_WEIGHT
    )

    reasons = []

    if heat_score >= 75:
        reasons.append("Very high heat exposure")
    elif heat_score >= 50:
        reasons.append("High heat exposure")
    elif heat_score >= 25:
        reasons.append("Moderate heat exposure")
    else:
        reasons.append("Lower heat exposure")

    if svi_score >= 75:
        reasons.append("Very high social vulnerability")
    elif svi_score >= 50:
        reasons.append("High social vulnerability")
    elif svi_score >= 25:
        reasons.append("Moderate social vulnerability")
    else:
        reasons.append("Lower social vulnerability")

    if heat_score >= 75 and svi_score >= 75:
        summary = (
            "High heat exposure combined with high social "
            "vulnerability makes this a top cooling priority."
        )
    elif heat_score >= 75:
        summary = (
            "The area has very high heat exposure, which "
            "drives its cooling priority."
        )
    elif svi_score >= 75:
        summary = (
            "High social vulnerability increases the need "
            "for cooling intervention."
        )
    else:
        summary = (
            "The area's cooling priority is driven by its "
            "combined heat exposure and vulnerability."
        )

    return {
        "GEOID": tract["GEOID"],
        "TRACT_NAME": tract["TRACT_NAME"],
        "tile_count": tract["tile_count"],
        "cooling_priority_score": final_score,
        "priority_label": label,

        "heat_exposure_score": heat_score,
        "social_vulnerability_score": svi_score,

        "heat_contribution": round(
            heat_contribution,
            2,
        ),

        "vulnerability_contribution": round(
            vulnerability_contribution,
            2,
        ),

        "reasons": reasons,
        "explanation": summary,

        "heat_exposure_details": {
            "average_temperature":
                tract["heat_exposure"][
                    "average_temperature"
                ],

            "average_max_temperature":
                tract["heat_exposure"][
                    "average_max_temperature"
                ],

            "average_min_temperature":
                tract["heat_exposure"][
                    "average_min_temperature"
                ],

            "average_thermal_range":
                tract["heat_exposure"][
                    "average_thermal_range"
                ],
        },

        "vulnerability_details": {
            "RPL_THEME1":
                tract["social_vulnerability"][
                    "RPL_THEME1"
                ],

            "RPL_THEME2":
                tract["social_vulnerability"][
                    "RPL_THEME2"
                ],

            "RPL_THEME3":
                tract["social_vulnerability"][
                    "RPL_THEME3"
                ],

            "RPL_THEME4":
                tract["social_vulnerability"][
                    "RPL_THEME4"
                ],
        },
    }


def main():

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        tracts = json.load(file)

    if not isinstance(tracts, list):
        raise RuntimeError(
            "Expected tract_cooling_priority.json "
            "to contain a list."
        )

    explained = [
        explain_priority(tract)
        for tract in tracts
    ]

    explained.sort(
        key=lambda item:
        item["cooling_priority_score"],
        reverse=True,
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            explained,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print("=" * 70)
    print("COOLING PRIORITY EXPLANATION ENGINE")
    print("=" * 70)

    print(
        f"\nTracts processed: "
        f"{len(explained)}"
    )

    print("\n" + "=" * 70)
    print("TOP PRIORITY EXPLANATIONS")
    print("=" * 70)

    for rank, item in enumerate(
        explained[:5],
        start=1,
    ):
        print(f"\n#{rank}")
        print(
            f"GEOID: {item['GEOID']}"
        )
        print(
            f"Tract: {item['TRACT_NAME']}"
        )
        print(
            f"Priority Score: "
            f"{item['cooling_priority_score']:.2f}/100"
        )
        print(
            f"Priority: "
            f"{item['priority_label']}"
        )
        print(
            f"Heat Contribution: "
            f"{item['heat_contribution']:.2f}"
        )
        print(
            f"Vulnerability Contribution: "
            f"{item['vulnerability_contribution']:.2f}"
        )
        print(
            "Why:"
        )
        print(
            item["explanation"]
        )

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)

    print(
        f"\nSaved to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()