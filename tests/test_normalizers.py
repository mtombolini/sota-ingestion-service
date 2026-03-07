from app.normalizers.bsale import normalize_product


def test_normalize_product():
    payload = {"id": 10, "name": "Prod", "code": "SKU", "state": 0, "category": {"name": "Cat"}, "unit": {"name": "UN"}}
    out = normalize_product(payload)
    assert out["external_id"] == "10"
    assert out["name"] == "Prod"
