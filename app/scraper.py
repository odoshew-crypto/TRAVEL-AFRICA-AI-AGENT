import time
from pathlib import Path

import pandas as pd
import requests

OVERPASS_URL = "https://overpass.kumi.systems/api/interpreter"

HEADERS = {
    "User-Agent": "TravelAfricaRAGProject/1.0",
    "Accept": "application/json"
}

LOCATIONS = [
    # Kenya
    {"name": "Nairobi", "country": "Kenya", "lat": -1.286389, "lon": 36.817223},
    {"name": "Mombasa", "country": "Kenya", "lat": -4.043477, "lon": 39.668206},
    {"name": "Nakuru", "country": "Kenya", "lat": -0.303099, "lon": 36.080025},
    {"name": "Kisumu", "country": "Kenya", "lat": -0.091702, "lon": 34.767956},
    {"name": "Eldoret", "country": "Kenya", "lat": 0.514277, "lon": 35.269779},
    {"name": "Naivasha", "country": "Kenya", "lat": -0.717177, "lon": 36.431026},
    {"name": "Malindi", "country": "Kenya", "lat": -3.217990, "lon": 40.116890},
    {"name": "Lamu", "country": "Kenya", "lat": -2.271690, "lon": 40.902010},
    {"name": "Diani", "country": "Kenya", "lat": -4.322197, "lon": 39.575360},
    {"name": "Watamu", "country": "Kenya", "lat": -3.352000, "lon": 40.020000},
    {"name": "Nanyuki", "country": "Kenya", "lat": 0.016700, "lon": 37.066700},
    {"name": "Maasai Mara", "country": "Kenya", "lat": -1.493100, "lon": 35.143900},
    {"name": "Amboseli", "country": "Kenya", "lat": -2.648600, "lon": 37.260600},

    # Tanzania
    {"name": "Zanzibar", "country": "Tanzania", "lat": -6.165917, "lon": 39.202641},
    {"name": "Arusha", "country": "Tanzania", "lat": -3.386925, "lon": 36.682993},
    {"name": "Dar es Salaam", "country": "Tanzania", "lat": -6.792354, "lon": 39.208328},

    # Uganda
    {"name": "Kampala", "country": "Uganda", "lat": 0.347596, "lon": 32.582520},
]

RADIUS_METERS = 15000
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_CSV = DATA_DIR / "hotels_raw.csv"


def _normalize_hotel(item, location_name, country):
    tags = item.get("tags", {})
    hotel_name = (tags.get("name") or "").strip()

    if not hotel_name:
        return None

    latitude = item.get("lat") or item.get("center", {}).get("lat")
    longitude = item.get("lon") or item.get("center", {}).get("lon")

    return {
        "hotel_name": hotel_name,
        "location": location_name,
        "country": country,
        "description": tags.get(
            "description",
            f"{hotel_name} is an accommodation option in {location_name}, {country}."
        ),
        "amenities": ", ".join([
            key for key in tags.keys()
            if key in [
                "internet_access",
                "parking",
                "restaurant",
                "bar",
                "swimming_pool",
                "air_conditioning",
                "wheelchair"
            ]
        ]) or "Not listed",
        "rating": tags.get("stars", "Not listed"),
        "contact": tags.get("phone", tags.get("contact:phone", "")),
        "website_url": tags.get("website", tags.get("contact:website", "")),
        "source_url": f"https://www.openstreetmap.org/{item['type']}/{item['id']}",
        "latitude": latitude,
        "longitude": longitude,
    }


def scrape_hotels():
    hotels = []
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for location in LOCATIONS:
        name = location["name"]
        country = location["country"]
        lat = location["lat"]
        lon = location["lon"]

        query = f"""
        [out:json][timeout:60];
        (
          node["tourism"~"hotel|guest_house|hostel|motel"](around:{RADIUS_METERS},{lat},{lon});
          way["tourism"~"hotel|guest_house|hostel|motel"](around:{RADIUS_METERS},{lat},{lon});
        );
        out center tags;
        """

        try:
            response = requests.post(
                OVERPASS_URL,
                data={"data": query},
                headers=HEADERS,
                timeout=90,
            )

            print("=" * 50)
            print("Location:", name)
            print("Country:", country)
            print("Status:", response.status_code)
            print("Preview:", response.text[:200])

            if response.status_code != 200:
                continue

            data = response.json()
            print("Elements found:", len(data.get("elements", [])))

        except Exception as exc:
            print(f"Failed for {name}: {exc}")
            continue

        for item in data.get("elements", []):
            hotel = _normalize_hotel(item, name, country)
            if hotel:
                hotels.append(hotel)

        time.sleep(3)

    df = pd.DataFrame(hotels)

    if not df.empty:
        df = df.drop_duplicates(subset=["hotel_name", "location", "country"])

    df.to_csv(OUTPUT_CSV, index=False)

    print("TOTAL HOTELS:", len(df))

    return df