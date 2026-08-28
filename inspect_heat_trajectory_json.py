import json


FILE_NAME = "heatmap_time_range_result.json"


print("=" * 70)
print("HEAT TRAJECTORY JSON INSPECTION")
print("=" * 70)

with open(
    FILE_NAME,
    "r",
    encoding="utf-8",
) as file:

    data = json.load(file)


print("\nTop-level type:")
print(type(data).__name__)


if isinstance(data, dict):

    print("\nTop-level keys:")
    print(
        list(
            data.keys()
        )
    )

    # --------------------------------------------------------
    # Inspect result
    # --------------------------------------------------------

    result = data.get(
        "result"
    )

    if result is not None:

        print(
            "\nResult type:"
        )

        print(
            type(result).__name__
        )

        if isinstance(
            result,
            dict,
        ):

            print(
                "\nResult keys:"
            )

            print(
                list(
                    result.keys()
                )
            )

    # --------------------------------------------------------
    # Inspect metadata
    # --------------------------------------------------------

    metadata = data.get(
        "metadata"
    )

    if metadata is None and isinstance(
        result,
        dict,
    ):

        metadata = result.get(
            "metadata"
        )

    print(
        "\nMetadata:"
    )

    if metadata is None:

        print(
            "NOT FOUND"
        )

    else:

        print(
            json.dumps(
                metadata,
                indent=4,
                ensure_ascii=False,
            )
        )

    # --------------------------------------------------------
    # Inspect map_data
    # --------------------------------------------------------

    map_data = data.get(
        "map_data"
    )

    if map_data is None and isinstance(
        result,
        dict,
    ):

        map_data = result.get(
            "map_data"
        )

    print(
        "\nMap data keys:"
    )

    if isinstance(
        map_data,
        dict,
    ):

        print(
            list(
                map_data.keys()
            )
        )

        features = map_data.get(
            "features",
            [],
        )

        print(
            "Number of features:",
            len(features),
        )

        if features:

            print(
                "\nFirst feature:"
            )

            print(
                json.dumps(
                    features[0],
                    indent=4,
                    ensure_ascii=False,
                )[:5000]
            )

    else:

        print(
            "NOT FOUND"
        )

    # --------------------------------------------------------
    # Inspect stats_data
    # --------------------------------------------------------

    stats_data = data.get(
        "stats_data"
    )

    if stats_data is None and isinstance(
        result,
        dict,
    ):

        stats_data = result.get(
            "stats_data"
        )

    print(
        "\nStats data:"
    )

    if stats_data is not None:

        print(
            json.dumps(
                stats_data,
                indent=4,
                ensure_ascii=False,
            )
        )

    else:

        print(
            "NOT FOUND"
        )

else:

    print(
        "\nUnexpected JSON structure."
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