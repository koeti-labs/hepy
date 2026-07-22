from scrapers.base import extract_jsonld_products, extract_ecommercepro_products, extract_nextjs_rsc_products, extract_woocommerce_products, extract_stock_products, select_best_match, Scraper, ProductMatch

def test_extract_jsonld_products_from_fixture():
    with open("fixtures/jsonld_sample.html", encoding="utf-8") as f:
        html = f.read()
    products = extract_jsonld_products(html)
    assert len(products) == 2
    assert products[0] == {"name": "Arroz Blanco 1kg", "price": 6500.0}
    assert products[1] == {"name": "Aceite de Girasol 900ml", "price": 12900.0}

def test_scraper_base_search_not_implemented():
    scraper = Scraper()
    try:
        scraper.search("arroz")
        assert False, "expected NotImplementedError"
    except NotImplementedError:
        pass

def test_product_match_dataclass():
    p = ProductMatch(name="Arroz 1kg", price=6500.0, url="https://x.com/p/1")
    assert p.name == "Arroz 1kg"
    assert p.price == 6500.0

def test_extract_ecommercepro_products_handles_sale_and_plain_price():
    with open("fixtures/ecommercepro_sample.html", encoding="utf-8") as f:
        html = f.read()
    products = extract_ecommercepro_products(html, base_url="https://example.com.py")
    assert len(products) == 2
    assert products[0]["name"] == "PECHUGA FRESCA C/HUESO PECHUGON X KG"
    assert products[0]["price"] == 20900.0  # sale price (from <ins>), not the crossed-out <del>
    assert products[0]["url"] == "https://example.com.py/pechuga-fresca-p12459"
    assert products[1]["name"] == "ARROZ DON ARROZ INTEGRAL 1KG"
    assert products[1]["price"] == 14000.0  # plain price (empty <ins> placeholder skipped)

def test_extract_nextjs_rsc_products_ignores_non_product_lines():
    with open("fixtures/real_search_arroz.txt", encoding="utf-8") as f:
        text = f.read()
    products = extract_nextjs_rsc_products(text)
    assert len(products) == 2
    assert products[0] == {"name": "Arroz Primicia Amarillo, 500grs", "price": 3550.0, "sku": "7840045019307"}
    assert products[1] == {"name": "Arroz Primicia rojo, 500gr", "price": 13800.0, "sku": "7840045018904"}

def test_extract_woocommerce_products_ignores_bulk_discount_price():
    with open("fixtures/woocommerce_sample.html", encoding="utf-8") as f:
        html = f.read()
    products = extract_woocommerce_products(html, base_url="https://example.com.py")
    assert len(products) == 1
    assert products[0]["name"] == "GALLETA DE ARROZ NATURAL B-LIGHT 85GR (24)"
    assert products[0]["price"] == 9100.0  # primary price, not the 8.750 bulk-discount tier
    assert products[0]["url"] == "https://grutteronline.casagrutter.com.py/producto/galleta-de-arroz-natural-b-light-85gr-24/"

def test_extract_stock_products_parses_gs_price_spans():
    with open("fixtures/stock_search_arroz.html", encoding="utf-8") as f:
        html = f.read()
    products = extract_stock_products(html)
    assert len(products) == 1
    assert products[0]["name"] == "ARROZ CHINES INTEGRAL BOLSA 1KG"
    assert products[0]["price"] == 21000.0
    assert products[0]["url"] == "https://www.stock.com.py/products/10070-arroz-chines-integral-bsa-1kg.aspx"

# Regression fixtures below are real bad matches observed live in production
# (see legal/revision_tos.md discussion) — a naive "take the first search
# result" approach recorded these as prices for the wrong product entirely.

def test_select_best_match_rejects_unrelated_category():
    # Casa Rica's search for "banana"/"cebolla"/"tomate" returned dog food —
    # doesn't even contain the ingredient name.
    candidates = [ProductMatch(name="ALIMENTO P/ PERRO MASTER DOG CACHORRO 1KG", price=31650.0, url="u")]
    assert select_best_match("Banana 1kg", candidates, "alimentacion_frutas", "banana_1kg") is None

def test_select_best_match_rejects_flavored_processed_product():
    # A banana-flavored whey protein contains "banana" as a flavor, not the
    # product itself.
    candidates = [ProductMatch(name="PROTEINA LIFE BAL WHEY PROTEIN BANANA 1KG - SUPL D", price=236000.0, url="u")]
    assert select_best_match("Banana 1kg", candidates, "alimentacion_frutas", "banana_1kg") is None

def test_select_best_match_rejects_unrelated_hair_product():
    candidates = [ProductMatch(name="TRATAMIENTO CAPILAR 3EN1 BANANA SMOOTH GUISSE 1KG", price=19900.0, url="u")]
    assert select_best_match("Banana 1kg", candidates, "alimentacion_frutas", "banana_1kg") is None

def test_select_best_match_accepts_real_banana_and_skips_bad_ones_first():
    candidates = [
        ProductMatch(name="PROTEINA LIFE BAL WHEY PROTEIN BANANA 1KG - SUPL D", price=236000.0, url="bad"),
        ProductMatch(name="BANANA 1 KG KARAPE", price=5150.0, url="good"),
    ]
    result = select_best_match("Banana 1kg", candidates, "alimentacion_frutas", "banana_1kg")
    assert result is not None
    assert result.url == "good"

def test_select_best_match_rejects_potato_gnocchi_for_raw_potato():
    candidates = [ProductMatch(name="ÑOQUIS QUIERO MAS DE PAPA 1KG", price=15000.0, url="u")]
    assert select_best_match("Papa 1kg", candidates, "alimentacion_hortalizas_y_tuberculos", "papa_1kg") is None

def test_select_best_match_rejects_meat_tenderizer_for_beef():
    # Contains "carne" but not "vacuna" — fails plain containment already.
    candidates = [ProductMatch(name="ABLANDADOR DE CARNE 300GR", price=8000.0, url="u")]
    assert select_best_match("Carne vacuna (nalga) 1kg", candidates, "alimentacion_carnes", "carne_vacuna_nalga_1kg") is None

def test_select_best_match_rejects_sopa_paraguaya_for_queso_paraguay():
    # "paraguaya" is not the whole word "paraguay" — a real, tricky
    # linguistic collision between a corn-cake dish and a type of cheese.
    candidates = [ProductMatch(name="SOPA PARAGUAYA JAKARU 4 QUESOS CONG. 1KG", price=18000.0, url="u")]
    assert select_best_match("Queso Paraguay 1kg", candidates, "alimentacion_lacteos_y_huevos", "queso_paraguay_1kg") is None

def test_select_best_match_accepts_brand_prefixed_non_strict_category():
    # Toothpaste isn't a raw-ingredient category, so no processed-word
    # denylist applies — a brand prefix before the generic term is fine.
    candidates = [ProductMatch(name="PACK ORAL-B PASTA DENTAL 3D WHITE 90G", price=25000.0, url="u")]
    result = select_best_match("Pasta dental 90g", candidates, "bienes_servicios_diversos_cuidado_personal", "pasta_dental_90g")
    assert result is not None

def test_select_best_match_returns_none_for_empty_candidates():
    assert select_best_match("Banana 1kg", [], "alimentacion_frutas", "banana_1kg") is None

# Second pass of real bad matches found after the first fix shipped —
# potato/onion/egg/orange sites all surfaced processed products instead of
# the raw ingredient.

def test_select_best_match_rejects_frozen_fries_for_raw_potato():
    candidates = [
        ProductMatch(name="Papa Frita Aviko Tradicional de 450 gr.", price=17450.0, url="u1"),
        ProductMatch(name="PAPA MC CAIN P/FREIR GOLDEN LONG 1KG", price=32000.0, url="u2"),
    ]
    assert select_best_match("Papa 1kg", candidates, "alimentacion_hortalizas_y_tuberculos", "papa_1kg") is None

def test_select_best_match_rejects_dehydrated_onion_flakes():
    candidates = [ProductMatch(name="CEBOLLA ARCO IRIS DESHIDRATADA TRITURADA PAQ.25GR", price=5450.0, url="u")]
    assert select_best_match("Cebolla 1kg", candidates, "alimentacion_hortalizas_y_tuberculos", "cebolla_1kg") is None

def test_select_best_match_rejects_orange_jam():
    candidates = [ProductMatch(name="MERMELADA NARANJA FRASCO 454 GR", price=13550.0, url="u")]
    assert select_best_match("Naranja 1kg", candidates, "alimentacion_frutas", "naranja_1kg") is None

def test_select_best_match_rejects_easter_chocolate_egg_and_quail_egg_and_egg_salad():
    candidates = [
        ProductMatch(name="HUEVO DE PASCUA COSTA 85GR", price=34500.0, url="u1"),
        ProductMatch(name="HUEVO DE CODORNIZ SUN 320G", price=29900.0, url="u2"),
        ProductMatch(name="ENSALADA FRESCA C/ HUEVO X KG.", price=75000.0, url="u3"),
    ]
    assert select_best_match("Huevos docena", candidates, "alimentacion_lacteos_y_huevos", "huevos_docena") is None

def test_select_best_match_denylist_word_does_not_self_disqualify_own_canon_name():
    # Defensive case: if a denylist word were ever also part of the
    # canonical name, it must not block an otherwise-correct match.
    candidates = [ProductMatch(name="TORTA DE CHOCOLATE 500G", price=15000.0, url="u")]
    result = select_best_match("Torta 500g", candidates, "alimentacion_otros_productos", "torta_500g")
    assert result is not None

# Third pass — glued compound word, misspelling, pickled onion, egg
# noodles, and a hairbrush that happens to be orange-colored, all found
# live after the second fix shipped.

def test_select_best_match_rejects_prefritas_as_one_glued_word():
    # "PREFRITAS" contains "frita" as a substring but not as a separate
    # token — a token-set intersection check would miss this.
    candidates = [ProductMatch(name="PAPAS PREFRITAS PEPE CHEF 1KG", price=19500.0, url="u")]
    assert select_best_match("Papa 1kg", candidates, "alimentacion_hortalizas_y_tuberculos", "papa_1kg") is None

def test_select_best_match_rejects_misspelled_dehydrated_onion():
    candidates = [ProductMatch(name="CEBOLLA DESIDRATADA GRANULADA TIVA GOURMET 35GR", price=20000.0, url="u")]
    assert select_best_match("Cebolla 1kg", candidates, "alimentacion_hortalizas_y_tuberculos", "cebolla_1kg") is None

def test_select_best_match_rejects_pickled_onion():
    candidates = [ProductMatch(name="CEBOLLA BLANCA MACERADO EN VINAGRE", price=17900.0, url="u")]
    assert select_best_match("Cebolla 1kg", candidates, "alimentacion_hortalizas_y_tuberculos", "cebolla_1kg") is None

def test_select_best_match_rejects_egg_noodles_for_dozen_eggs():
    candidates = [ProductMatch(name="FIDEO ALEMANES SPAETZLE G+G CON HUEVOS 500GR", price=24950.0, url="u")]
    assert select_best_match("Huevos docena", candidates, "alimentacion_lacteos_y_huevos", "huevos_docena") is None

def test_select_best_match_rejects_orange_colored_hairbrush():
    candidates = [ProductMatch(name="PEINE ESCOVEL LIVIA NARANJA", price=21000.0, url="u")]
    assert select_best_match("Naranja 1kg", candidates, "alimentacion_frutas", "naranja_1kg") is None

def test_select_best_match_rejects_orange_essence():
    candidates = [ProductMatch(name="ESENCIA DE NARANJA MICKEY 120ML", price=8350.0, url="u")]
    assert select_best_match("Naranja 1kg", candidates, "alimentacion_frutas", "naranja_1kg") is None

# Fourth pass — quantity mismatch found live: a 900ml canonical item matched
# a completely different pack size because quantities were never compared
# (digits are dropped by _tokenize, unit words are stopwords).

def test_select_best_match_rejects_wrong_pack_size():
    candidates = [ProductMatch(name="ACEITE ALSAMAR  DE GIRASOL 1,5 LT", price=31350.0, url="u")]
    result = select_best_match(
        "Aceite de girasol 900ml", candidates, "alimentacion_aceites_y_grasas", "aceite_girasol_900ml",
    )
    assert result is None


def test_select_best_match_accepts_matching_pack_size_in_different_unit_spelling():
    candidates = [ProductMatch(name="ACEITE GIRASOL COCINERO 900 ML", price=15000.0, url="good")]
    result = select_best_match(
        "Aceite de girasol 900ml", candidates, "alimentacion_aceites_y_grasas", "aceite_girasol_900ml",
    )
    assert result is not None
    assert result.url == "good"


def test_select_best_match_ignores_quantity_when_canonical_name_has_none():
    candidates = [ProductMatch(name="Detergente Ala 3L", price=12000.0, url="good")]
    result = select_best_match("Detergente", candidates)
    assert result is not None
    assert result.url == "good"

# Fifth pass — "docena" has no leading digit ("Huevos docena", not "12
# docena"), so quantity was silently never enforced for this item at all,
# confirmed live: a 30-egg carton passed as a dozen.

def test_select_best_match_rejects_thirty_egg_carton_for_a_dozen():
    candidates = [ProductMatch(name="HUEVO CAMPERO  X 30 UNI HUEVO RICO", price=37000.0, url="u")]
    assert select_best_match("Huevos docena", candidates, "alimentacion_lacteos_y_huevos", "huevos_docena") is None


def test_select_best_match_accepts_a_dozen_eggs_written_as_12un():
    candidates = [ProductMatch(name="HUEVO NUTRIHUEVOS TIPO A CJA. 12UN", price=11250.0, url="good")]
    result = select_best_match("Huevos docena", candidates, "alimentacion_lacteos_y_huevos", "huevos_docena")
    assert result is not None
    assert result.url == "good"


def test_select_best_match_rejects_cassava_flour_for_raw_mandioca():
    candidates = [ProductMatch(name="HARINA DE MANDIOCA CODIPSA X1KG", price=21400.0, url="u")]
    assert select_best_match("Mandioca 1kg", candidates, "alimentacion_hortalizas_y_tuberculos", "mandioca_1kg") is None


def test_select_best_match_rejects_a_3x90_multipack_for_one_bar_of_soap():
    candidates = [ProductMatch(name="JABON DE TOCADOR DOVE BLANCO 3X90 GRS (16)", price=21750.0, url="u")]
    result = select_best_match(
        "Jabón de tocador unidad", candidates, "bienes_servicios_diversos_cuidado_personal", "jabon_tocador_unidad",
    )
    assert result is None


def test_select_best_match_rejects_an_x3_de_90_multipack_for_one_bar_of_soap():
    candidates = [ProductMatch(name="Jabon de Tocador Protex aloe x 3 de 90 gr.", price=13500.0, url="u")]
    result = select_best_match(
        "Jabón de tocador unidad", candidates, "bienes_servicios_diversos_cuidado_personal", "jabon_tocador_unidad",
    )
    assert result is None


def test_select_best_match_bare_unidad_does_not_force_a_weight_comparison():
    # "Jabón de tocador unidad" is priced per bar, not by weight — real bars
    # describe their weight in grams, a different axis entirely. A bare
    # "unidad"/"un" with no digit must not manufacture a quantity constraint.
    candidates = [ProductMatch(name="JABON DE TOCADOR LUX OQUIDEA NEG X 125 G", price=6500.0, url="good")]
    result = select_best_match(
        "Jabón de tocador unidad", candidates, "bienes_servicios_diversos_cuidado_personal", "jabon_tocador_unidad",
    )
    assert result is not None
    assert result.url == "good"
