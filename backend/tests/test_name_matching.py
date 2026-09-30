from app.utils.name_matching import normalize_name


def test_strips_accents():
    assert normalize_name("Đorđe Petrović") == "dorde petrovic"
    assert normalize_name("Rayan Aït-Nouri") == "rayan ait nouri"


def test_lowercases_and_strips_punctuation():
    assert normalize_name("O'Reilly") == "o reilly"
    assert normalize_name("Jean-Paul") == "jean paul"


def test_collapses_whitespace():
    assert normalize_name("  Erling   Haaland  ") == "erling haaland"


def test_matching_names_normalize_identically():
    assert normalize_name("Ferdi Kadıoğlu") == normalize_name("Ferdi Kadioglu")
