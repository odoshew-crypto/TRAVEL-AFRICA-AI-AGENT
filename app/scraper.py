import os
import time
from pathlib import Path

import pandas as pd
import requests


# Multiple Overpass servers are used so the scraper can switch
# when one server is unavailable or times out.
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.nchc.org.tw/api/interpreter",
]

HEADERS = {
    "User-Agent": "TravelAfricaRAGProject/1.0",
    "Accept": "application/json",
}

LOCATIONS = [
    # Kenya
    {
        "name": "Nairobi",
        "country": "Kenya",
        "lat": -1.286389,
        "lon": 36.817223,
    },
    {
        "name": "Mombasa",
        "country": "Kenya",
        "lat": -4.043477,
        "lon": 39.668206,
    },
    {
        "name": "Nakuru",
        "country": "Kenya",
        "lat": -0.303099,
        "lon": 36.080025,
    },
    {
        "name": "Kisumu",
        "country": "Kenya",
        "lat": -0.091702,
        "lon": 34.767956,
    },
    {
        "name": "Eldoret",
        "country": "Kenya",
        "lat": 0.514277,
        "lon": 35.269779,
    },
    {
        "name": "Naivasha",
        "country": "Kenya",
        "lat": -0.717177,
        "lon": 36.431026,
    },
    {
        "name": "Malindi",
        "country": "Kenya",
        "lat": -3.217990,
        "lon": 40.116890,
    },
    {
        "name": "Lamu",
        "country": "Kenya",
        "lat": -2.271690,
        "lon": 40.902010,
    },
    {
        "name": "Diani",
        "country": "Kenya",
        "lat": -4.322197,
        "lon": 39.575360,
    },
    {
        "name": "Watamu",
        "country": "Kenya",
        "lat": -3.352000,
        "lon": 40.020000,
    },
    {
        "name": "Nanyuki",
        "country": "Kenya",
        "lat": 0.016700,
        "lon": 37.066700,
    },
    {
        "name": "Maasai Mara",
        "country": "Kenya",
        "lat": -1.493100,
        "lon": 35.143900,
    },
    {
        "name": "Amboseli",
        "country": "Kenya",
        "lat": -2.648600,
        "lon": 37.260600,
    },

    # Tanzania
    {
        "name": "Zanzibar",
        "country": "Tanzania",
        "lat": -6.165917,
        "lon": 39.202641,
    },
    {
        "name": "Arusha",
        "country": "Tanzania",
        "lat": -3.386925,
        "lon": 36.682993,
    },
    {
        "name": "Dar es Salaam",
        "country": "Tanzania",
        "lat": -6.792354,
        "lon": 39.208328,
    },

    # Uganda
    {
        "name": "Kampala",
        "country": "Uganda",
        "lat": 0.347596,
        "lon": 32.582520,
    },
]


RADIUS_METERS = 15000

BASE_DIR = Path(__file__).resolve().parent

# Locally, data is stored in app/data.
# On Railway, set DATA_DIR=/data when using a persistent volume.
DATA_DIR = Path(
    os.getenv(
        "DATA_DIR",
        str(BASE_DIR / "data"),
    )
)

OUTPUT_CSV = DATA_DIR / "hotels_raw.csv"


def _build_query(latitude: float, longitude: float) -> str:
    """
    Build the Overpass query for one location.
    """

    return f"""
    [out:json][timeout:120];

    (
      node["tourism"~"^(hotel|guest_house|hostel|motel)$"]
        (around:{RADIUS_METERS},{latitude},{longitude});

      way["tourism"~"^(hotel|guest_house|hostel|motel)$"]
        (around:{RADIUS_METERS},{latitude},{longitude});

      relation["tourism"~"^(hotel|guest_house|hostel|motel)$"]
        (around:{RADIUS_METERS},{latitude},{longitude});
    );

    out center tags;
    """


def _normalize_hotel(
    item: dict,
    location_name: str,
    country: str,
) -> dict | None:
    """
    Convert one OpenStreetMap result into a consistent hotel record.
    """

    tags = item.get("tags", {})

    hotel_name = (
        tags.get("name")
        or tags.get("brand")
        or ""
    ).strip()

    if not hotel_name:
        return None

    center = item.get("center", {})

    latitude = item.get("lat") or center.get("lat")
    longitude = item.get("lon") or center.get("lon")

    amenity_keys = [
        "internet_access",
        "parking",
        "restaurant",
        "bar",
        "swimming_pool",
        "air_conditioning",
        "wheelchair",
    ]

    amenities = []

    for key in amenity_keys:
        value = tags.get(key)

        if value and str(value).lower() not in {
            "no",
            "false",
            "0",
        }:
            amenities.append(key)

    contact = (
        tags.get("phone")
        or tags.get("contact:phone")
        or tags.get("mobile")
        or tags.get("contact:mobile")
        or ""
    )

    website_url = (
        tags.get("website")
        or tags.get("contact:website")
        or ""
    )

    description = tags.get(
        "description",
        (
            f"{hotel_name} is an accommodation option "
            f"in {location_name}, {country}."
        ),
    )

    return {
        "hotel_name": hotel_name,
        "location": location_name,
        "country": country,
        "description": description,
        "amenities": ", ".join(amenities) or "Not listed",
        "rating": tags.get("stars", "Not listed"),
        "contact": contact,
        "website_url": website_url,
        "source_url": (
            f"https://www.openstreetmap.org/"
            f"{item.get('type')}/{item.get('id')}"
        ),
        "latitude": latitude,
        "longitude": longitude,
    }


def _query_overpass(
    query: str,
    location_name: str,
    retries: int = 1,
) -> dict:
    """
    Send the query to available Overpass servers.

    If one server fails, the function automatically tries the next one.
    """

    last_error = None

    for attempt in range(1, retries + 1):
        for overpass_url in OVERPASS_URLS:
            try:
                print(
                    f"Trying {location_name} using "
                    f"{overpass_url}, attempt {attempt}"
                )

                response = requests.post(
                    overpass_url,
                    data={"data": query},
                    headers=HEADERS,
                    timeout=(10, 60),
                )

                print(
                    f"{location_name} status: "
                    f"{response.status_code}"
                )

                if response.status_code in {
                    429,
                    502,
                    503,
                    504,
                }:
                    last_error = RuntimeError(
                        f"Overpass returned "
                        f"{response.status_code}"
                    )

                    print(
                        f"Temporary error from "
                        f"{overpass_url}"
                    )

                    continue

                response.raise_for_status()

                data = response.json()

                print(
                    f"{location_name} elements found: "
                    f"{len(data.get('elements', []))}"
                )

                return data

            except requests.Timeout as exc:
                last_error = exc

                print(
                    f"Timeout from {overpass_url}: "
                    f"{exc}"
                )

            except requests.ConnectionError as exc:
                last_error = exc

                print(
                    f"Connection error from "
                    f"{overpass_url}: {exc}"
                )

            except requests.HTTPError as exc:
                last_error = exc

                print(
                    f"HTTP error from "
                    f"{overpass_url}: {exc}"
                )

            except ValueError as exc:
                last_error = exc

                print(
                    f"Invalid JSON from "
                    f"{overpass_url}: {exc}"
                )

        if attempt < retries:
            wait_seconds = attempt * 5

            print(
                f"Waiting {wait_seconds} seconds "
                f"before retrying {location_name}"
            )

            time.sleep(wait_seconds)

    raise RuntimeError(
        f"All Overpass servers failed for "
        f"{location_name}: {last_error}"
    )


def _save_progress(hotels: list[dict]) -> pd.DataFrame:
    """
    Save the current results to CSV.

    This protects the collected data if the application stops
    before all locations are completed.
    """

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = pd.DataFrame(hotels)

    if not df.empty:
        df = df.drop_duplicates(
            subset=["source_url"],
            keep="first",
        )

        df = df.sort_values(
            by=[
                "country",
                "location",
                "hotel_name",
            ]
        )

    df.to_csv(
        OUTPUT_CSV,
        index=False,
    )

    print(
        f"Saved {len(df)} hotel records "
        f"to {OUTPUT_CSV}"
    )

    return df


def scrape_hotels() -> dict:
    """
    Scrape hotel and accommodation records for all locations.

    Returns a dictionary that FastAPI can safely convert to JSON.
    """

    hotels = []
    failed_locations = []

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    for location in LOCATIONS:
        name = location["name"]
        country = location["country"]
        latitude = location["lat"]
        longitude = location["lon"]

        print("\n" + "=" * 60)
        print(f"Scraping {name}, {country}")

        query = _build_query(
            latitude=latitude,
            longitude=longitude,
        )

        try:
            data = _query_overpass(
                query=query,
                location_name=name,
                retries=1,
            )

        except Exception as exc:
            error_message = str(exc)

            print(
                f"Failed for {name}: "
                f"{error_message}"
            )

            failed_locations.append(
                {
                    "location": name,
                    "country": country,
                    "error": error_message,
                }
            )

            continue

        location_count = 0

        for item in data.get("elements", []):
            hotel = _normalize_hotel(
                item=item,
                location_name=name,
                country=country,
            )

            if hotel:
                hotels.append(hotel)
                location_count += 1

        print(
            f"Accepted records for {name}: "
            f"{location_count}"
        )

        _save_progress(hotels)

        # Delay requests so the public API is not overloaded.
        time.sleep(3)

    final_df = _save_progress(hotels)

    print("\n" + "=" * 60)
    print("Hotel scraping completed")
    print("Total hotels:", len(final_df))
    print(
        "Failed locations:",
        len(failed_locations),
    )
    print("Output file:", OUTPUT_CSV)

    return {
        "status": "completed",
        "total_hotels": len(final_df),
        "failed_location_count": len(
            failed_locations
        ),
        "failed_locations": failed_locations,
        "output_file": str(OUTPUT_CSV),
    }


if __name__ == "__main__":
    result = scrape_hotels()
    print(result)