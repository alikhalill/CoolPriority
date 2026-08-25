import json
import requests


INPUT_FILE = "tract_cooling_priority.json"
OUTPUT_FILE = "tract_population.json"


# ============================================================
# Census configuration
# ============================================================

YEAR = 2024

CENSUS_URL = (
    f"https://api.census.gov/data/"
    f"{YEAR}/acs/acs5"
)


# ============================================================
# Load our analyzed tracts
# ============================================================

def load_tracts():

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        tracts = json.load(file)

    if not isinstance(tracts, list):
        raise RuntimeError(
            "tract_cooling_priority.json "
            "must contain a list."
        )

    return tracts


# ============================================================
# Get Census population for New York
# ============================================================

def fetch_population():

    params = {
        "get": "NAME,B01003_001E",

        # New York state
        "for": "tract:*",

        # County is needed because Census tracts
        # are nested under counties.
        "in": "state:36 county:*",
    }

    response = requests.get(
        CENSUS_URL,
        params=params,
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    if not data or len(data) < 2:
        raise RuntimeError(
            "Census API returned no population data."
        )

    headers = data[0]

    records = []

    for row in data[1:]:

        record = dict(
            zip(
                headers,
                row,
            )
        )

        state = record.get(
            "state"
        )

        county = record.get(
            "county"
        )

        tract = record.get(
            "tract"
        )

        population = record.get(
            "B01003_001E"
        )

        if not all(
            [
                state,
                county,
                tract,
            ]
        ):
            continue

        # Census tract GEOID:
        # state + county + tract
        geoid = (
            state
            + county
            + tract
        )

        try:
            population = int(
                population
            )

        except (
            TypeError,
            ValueError,
        ):
            population = None

        records.append(
            {
                "GEOID": geoid,
                "NAME": record.get(
                    "NAME"
                ),
                "population": population,
            }
        )

    return records


# ============================================================
# Match population to our 11 tracts
# ============================================================

def match_population(
    tracts,
    population_records,
):

    population_by_geoid = {
        item["GEOID"]:
            item
        for item in population_records
    }

    matched = []

    for tract in tracts:

        geoid = str(
            tract["GEOID"]
        ).zfill(11)

        census_record = (
            population_by_geoid.get(
                geoid
            )
        )

        if census_record is None:
            raise RuntimeError(
                f"No Census population found "
                f"for GEOID {geoid}"
            )

        result = {
            "GEOID": geoid,

            "TRACT_NAME":
                tract["TRACT_NAME"],

            "cooling_priority_score":
                tract[
                    "cooling_priority_score"
                ],

            "heat_exposure_score":
                tract[
                    "heat_exposure"
                ][
                    "heat_exposure_score"
                ],

            "social_vulnerability_score":
                tract[
                    "social_vulnerability"
                ][
                    "RPL_THEMES"
                ],

            "population":
                census_record[
                    "population"
                ],
        }

        matched.append(
            result
        )

    return matched


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 70)
    print(
        "CENSUS POPULATION DATA"
    )
    print("=" * 70)

    tracts = load_tracts()

    print(
        f"\nOur analyzed tracts: "
        f"{len(tracts)}"
    )

    print(
        "\nRequesting ACS 2024 5-Year "
        "population data..."
    )

    population_records = (
        fetch_population()
    )

    print(
        f"Census records received: "
        f"{len(population_records)}"
    )

    matched = match_population(
        tracts,
        population_records,
    )

    # --------------------------------------------------------
    # Sort by population
    # --------------------------------------------------------

    matched.sort(
        key=lambda item:
        item["population"],
        reverse=True,
    )

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        "POPULATION BY ANALYZED TRACT"
    )
    print("=" * 70)

    for item in matched:

        print(
            f"\n"
            f"GEOID: "
            f"{item['GEOID']}"
        )

        print(
            f"Tract: "
            f"{item['TRACT_NAME']}"
        )

        print(
            f"Population: "
            f"{item['population']:,}"
        )

        print(
            f"Cooling Priority: "
            f"{item['cooling_priority_score']:.2f}"
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            matched,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)

    print(
        f"\nSaved to:"
        f"\n{OUTPUT_FILE}"
    )

    print(
        "\nFortyGuard API calls: 0"
    )


if __name__ == "__main__":
    main()