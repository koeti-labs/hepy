import json


def test_basket_weights_sum_to_one():
    with open("basket.json", encoding="utf-8") as f:
        basket = json.load(f)
    total = sum(item["weight"] for item in basket)
    assert abs(total - 1.0) < 1e-6


def test_basket_items_have_required_fields():
    with open("basket.json", encoding="utf-8") as f:
        basket = json.load(f)
    assert len(basket) >= 20
    for item in basket:
        assert item["product_key"]
        assert item["nombre_canonico"]
        assert item["bcp_category"]
        assert 0 < item["weight"] < 1
        assert isinstance(item["queries"], dict)
        assert len(item["queries"]) == 9  # one search query per supermarket
