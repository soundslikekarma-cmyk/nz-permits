"""Tests for free-text route checking with precise match rules.

Each test pins behaviour that survived the audit of 24 test cases:
- Right issues fire when route mentions the right corridor
- Wrong issues do NOT fire when corridor doesn't actually pass through
- Stopwords like 'to', 'via', 'the' don't count
- Aliases expand correctly
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _payload(text: str, width=6.5, height=5.2, length=14.0, weight=28000):
    return {
        "route_text": text,
        "width_m": width,
        "height_m": height,
        "length_m": length,
        "weight_kg": weight,
        "indivisible": True,
    }


def _titles(response_json):
    return [i["title"] for i in response_json["issues"]]


# ===== Plausibly correct routes =====

def test_tauranga_to_hamilton_via_sh29_only_fires_kaimai():
    r = client.post("/check-route-text", json=_payload("Tauranga to Hamilton via SH29"))
    titles = _titles(r.json())
    assert "SH29 Kaimai overhead clearance" in titles
    # Should NOT fire — these are for other corridors:
    assert "SH36 width restrictions" not in titles
    assert "Tauranga Eastern Link (toll road)" not in titles
    assert "SH1 Warkworth to Silverdale toll road" not in titles


def test_mt_maunganui_to_auckland_via_sh2_does_not_fire_sh29_kaimai():
    """SH2 via Karangahake is the alternative to SH29 Kaimai. Going SH2 means NOT going SH29."""
    r = client.post("/check-route-text", json=_payload("Mt Maunganui to Auckland via SH2"))
    titles = _titles(r.json())
    # User explicitly chose SH2 - so SH29 should not fire
    # But we do still trigger by the all_of_groups [tauranga, hamilton] - they didn't mention hamilton
    # Actually keyword "hamilton" isn't in this text, so SH29 wouldn't fire
    assert "SH29 Kaimai overhead clearance" not in titles
    # SH36 should NOT fire - they're not going to Rotorua
    assert "SH36 width restrictions" not in titles


def test_auckland_to_wellington_does_not_fire_northland_issues():
    r = client.post("/check-route-text", json=_payload("Auckland to Wellington via SH1"))
    titles = _titles(r.json())
    assert "SH1 Warkworth to Silverdale toll road" not in titles
    assert "Brynderwyn Hills (SH1)" not in titles


def test_auckland_to_whangarei_does_not_fire_wellington_or_desert():
    r = client.post("/check-route-text", json=_payload("Auckland to Whangarei via SH1"))
    titles = _titles(r.json())
    assert "Wellington Motorway height restrictions" not in titles
    assert "Desert Road (SH1) elevation" not in titles
    # SHOULD fire:
    assert "Brynderwyn Hills (SH1)" in titles


# ===== Multi-region: shared keywords must not leak =====

def test_tauranga_to_hamilton_does_not_fire_sh36():
    """The big one. Tauranga to Hamilton must not fire SH36."""
    r = client.post("/check-route-text", json=_payload("Tauranga to Hamilton"))
    titles = _titles(r.json())
    assert "SH36 width restrictions" not in titles
    assert "SH33 Paengaroa overhead" not in titles
    # Tauranga Eastern Link must NOT fire just for mentioning Tauranga
    assert "Tauranga Eastern Link (toll road)" not in titles


def test_auckland_to_hamilton_does_not_fire_sh29_kaimai():
    """Auckland to Hamilton goes via SH1, not over the Kaimais."""
    r = client.post("/check-route-text", json=_payload("Auckland to Hamilton"))
    titles = _titles(r.json())
    assert "SH29 Kaimai overhead clearance" not in titles


def test_wellington_to_napier_clean():
    """Should NOT pick up Tauranga-related issues."""
    r = client.post("/check-route-text", json=_payload("Wellington to Napier"))
    titles = _titles(r.json())
    assert "SH29 Kaimai overhead clearance" not in titles
    assert "Tauranga Eastern Link (toll road)" not in titles


def test_christchurch_to_dunedin_no_issues():
    """South Island - we have no data. Should be empty."""
    r = client.post("/check-route-text", json=_payload("Christchurch to Dunedin"))
    assert r.json()["summary"]["total"] == 0


# ===== Single-word inputs =====

def test_just_tauranga_fires_nothing():
    """Single town name alone doesn't tell us a route - no issues should fire."""
    r = client.post("/check-route-text", json=_payload("Tauranga"))
    titles = _titles(r.json())
    assert "SH36 width restrictions" not in titles
    assert "Tauranga Eastern Link (toll road)" not in titles
    # Even SH29 shouldn't fire - we don't know where they're going
    assert "SH29 Kaimai overhead clearance" not in titles


def test_just_sh1_does_not_fire_all_sh1_issues():
    """Single 'SH1' is too vague - shouldn't fire everything."""
    r = client.post("/check-route-text", json=_payload("SH1"))
    titles = _titles(r.json())
    # These need specific corridors
    assert "Auckland Southern Motorway — TMP required" not in titles
    assert "Wellington Motorway height restrictions" not in titles
    assert "SH1 Warkworth to Silverdale toll road" not in titles


def test_just_wellington_fires_minimal():
    """Wellington alone with a 5.2m high Cat 4B load SHOULD fire the Wellington Motorway height issue
    (you can't enter Wellington without the urban motorway). But shouldn't fire unrelated Auckland or
    Tauranga issues."""
    r = client.post("/check-route-text", json=_payload("Wellington"))
    titles = _titles(r.json())
    # SHOULD fire - city-entry rule for tall loads
    assert "Wellington Motorway height restrictions" in titles
    # Should NOT fire unrelated stuff
    assert "Auckland Southern Motorway — TMP required" not in titles
    assert "SH29 Kaimai overhead clearance" not in titles


# ===== Aliases =====

def test_tga_alias_expands():
    r = client.post("/check-route-text", json=_payload("tga to akl via the kaimais"))
    kw = r.json()["matched_keywords"]
    assert "tauranga" in kw
    assert "auckland" in kw
    assert "sh29" in kw


def test_kaimais_expands_to_sh29():
    r = client.post("/check-route-text", json=_payload("via the kaimais"))
    kw = r.json()["matched_keywords"]
    assert "sh29" in kw


def test_bop_expands():
    r = client.post("/check-route-text", json=_payload("BOP to Hamilton"))
    kw = r.json()["matched_keywords"]
    assert "tauranga" in kw or "bay of plenty" in kw


# ===== Stopwords =====

def test_stopwords_not_in_matched_keywords():
    r = client.post("/check-route-text", json=_payload("going from Tauranga to Hamilton via SH29"))
    kw = set(r.json()["matched_keywords"])
    for stopword in ["to", "via", "from", "going", "the", "and"]:
        assert stopword not in kw, f"Stopword '{stopword}' should not be in matched_keywords"


def test_nonsense_input_no_issues():
    r = client.post("/check-route-text", json=_payload("back roads through nowhere"))
    assert r.json()["summary"]["total"] == 0


# ===== Pre-defined dropdown still works =====

def test_existing_check_route_still_works():
    payload = {
        "route_id": "tauranga_auckland",
        "width_m": 6.5,
        "height_m": 5.2,
        "length_m": 14.0,
        "weight_kg": 28000,
    }
    r = client.post("/check-route", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["summary"]["total"] >= 1


# ===== Heavy loads expose weight-gated issues =====

def test_heavy_load_triggers_bombay_bridges_with_route():
    """Heavy + on the right corridor should fire Bombay."""
    r = client.post("/check-route-text", json=_payload("Tauranga to Auckland via SH1 Bombay Pokeno", weight=60000))
    titles = _titles(r.json())
    assert "Bombay Hills bridge restrictions" in titles


def test_heavy_load_alone_no_bombay():
    """Just being heavy without mentioning Bombay/Pokeno does not fire that issue."""
    r = client.post("/check-route-text", json=_payload("Tauranga to Hamilton", weight=60000))
    titles = _titles(r.json())
    assert "Bombay Hills bridge restrictions" not in titles


# ===== Validation =====

def test_empty_route_text_rejected():
    r = client.post("/check-route-text", json=_payload(""))
    assert r.status_code == 422


def test_mt_maunganui_to_auckland_via_sh2_fires_auckland_motorway():
    """6.5m wide Cat 4B going to Auckland - should fire motorway TMP regardless of road named."""
    r = client.post("/check-route-text", json=_payload("Mt Maunganui to Auckland via SH2"))
    titles = _titles(r.json())
    assert "Auckland Southern Motorway — TMP required" in titles


def test_south_auckland_destination_fires_auckland_motorway():
    """South Auckland implies entering Auckland - same trigger."""
    r = client.post("/check-route-text", json=_payload("Mt Maunganui to South Auckland"))
    titles = _titles(r.json())
    assert "Auckland Southern Motorway — TMP required" in titles


def test_tauranga_wellington_fires_wellington_motorway_for_tall_load():
    """5.2m high load going to Wellington fires motorway height rule even if user says SH2."""
    r = client.post("/check-route-text", json=_payload("Tauranga to Wellington via SH2 and Napier"))
    titles = _titles(r.json())
    assert "Wellington Motorway height restrictions" in titles


def test_short_load_to_wellington_does_not_fire_motorway():
    """A short truck to Wellington should NOT fire the height-gated motorway rule."""
    r = client.post("/check-route-text", json=_payload("Wellington", height=4.0))
    titles = _titles(r.json())
    assert "Wellington Motorway height restrictions" not in titles


def test_narrow_load_to_auckland_does_not_fire_motorway():
    """A normal-width load to Auckland should NOT fire the width-gated motorway rule."""
    r = client.post("/check-route-text", json=_payload("Auckland", width=2.5))
    titles = _titles(r.json())
    assert "Auckland Southern Motorway — TMP required" not in titles
