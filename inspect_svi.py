import pandas as pd
FILE_PATH = "data/SVI_2022_US.csv"
def main():
    df = pd.read_csv(FILE_PATH)

    print("=" * 70)
    print("SVI 2022 DATASET INSPECTION")
    print("=" * 70)

    print("\nShape:")
    print(df.shape)

    print("\nColumns:")
    for column in df.columns:
        print(column)

    print("\nFirst 5 rows:")
    print(df.head())

    print("\nData types:")
    print(df.dtypes)

    print("\nMissing values - Top 20:")
    missing = df.isnull().sum().sort_values(
        ascending=False
    )

    print(missing.head(20))

    # Show important-looking SVI columns
    keywords = [
        "FIPS",
        "TRACT",
        "COUNTY",
        "STATE",
        "LOCATION",
        "RPL_THEMES",
        "RPL_THEME1",
        "RPL_THEME2",
        "RPL_THEME3",
        "RPL_THEME4",
    ]

    print("\nRelevant SVI columns found:")

    found = []

    for column in df.columns:
        column_upper = column.upper()

        if any(
            keyword in column_upper
            for keyword in keywords
        ):
            found.append(column)

    for column in found:
        print(column)

    print("\nUnique states:")
    if "ST_ABBR" in df.columns:
        print(df["ST_ABBR"].nunique())

        print(
            df["ST_ABBR"]
            .dropna()
            .unique()
        )

    print("\n✅ Inspection completed.")


if __name__ == "__main__":
    main()