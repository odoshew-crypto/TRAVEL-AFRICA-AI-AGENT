from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
INPUT_CSV = DATA_DIR / "hotels_raw.csv"
OUTPUT_CSV = DATA_DIR / "hotels.csv"


def clean_hotels():
    if not INPUT_CSV.exists():
        return pd.DataFrame(columns=[
            "hotel_name",
            "location",
            "country",
            "description",
            "amenities",
            "rating",
            "contact",
            "website_url",
            "source_url",
            "latitude",
            "longitude",
        ])

    df = pd.read_csv(INPUT_CSV)

    df = df.dropna(subset=["hotel_name"])
    df = df.drop_duplicates(subset=["hotel_name", "location"])

    df["description"] = df["description"].fillna(
        "Hotel accommodation suitable for travelers visiting this destination."
    )

    df["amenities"] = df["amenities"].fillna("Not listed")
    df["rating"] = df["rating"].fillna("Not listed")
    df["website_url"] = df["website_url"].fillna("")
    df["contact"] = df["contact"].fillna("")

    df.to_csv(OUTPUT_CSV, index=False)
    return df
