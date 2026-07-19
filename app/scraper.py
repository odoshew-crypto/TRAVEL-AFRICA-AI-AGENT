import os
import time
from pathlib import Path

import pandas as pd
import requests


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

# On Railway, set DATA_DIR=/data when using a volume.
DATA_DIR = Path(
    os.getenv(
        "DATA_DIR",
        str(BASE_DIR / "data"),
    )
)

OUTPUT_CSV = DATA_DIR / "hotels_raw.csv"