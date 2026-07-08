from pathlib import Path

from app.scraper import OUTPUT_CSV, _normalize_hotel


def test_output_csv_path_is_inside_app_data():
    assert OUTPUT_CSV.parent == Path(__file__).resolve().parents[1] / "app" / "data"
    assert OUTPUT_CSV.name == "hotels_raw.csv"


def test_normalize_hotel_uses_fallback_description():
    item = {
        "type": "node",
        "id": 1,
        "tags": {"name": "Test Hotel"},
    }

    hotel = _normalize_hotel(item, "Nairobi", "Kenya")

    assert hotel["hotel_name"] == "Test Hotel"
    assert hotel["location"] == "Nairobi"
    assert "Nairobi, Kenya" in hotel["description"]
