"""NZ heavy haulage route data.

Each Issue has a `match_when` rule with two parts:
- any_of: list of keyword strings; mentioning ANY of these triggers the issue.
- all_of_groups: list of keyword groups; mentioning ALL keywords in ANY group triggers the issue.
  This handles corridor-only issues like "SH29 Kaimai fires if user mentions BOTH Tauranga AND Hamilton".

Filler words ("to", "via", "the", "from", "and", "then", "going", "trip", "through") are stripped before matching.

The same Issue can still appear in route_ids[] for the pre-defined dropdown.
"""
from dataclasses import dataclass, field
import re


@dataclass
class MatchRule:
    """Defines when an issue should fire from free-text input."""
    any_of: list[str] = field(default_factory=list)
    # all_of_groups: list of groups. ANY group with all its keywords matched triggers.
    all_of_groups: list[list[str]] = field(default_factory=list)


@dataclass
class Issue:
    title: str
    description: str
    severity: str  # info, warning, blocker
    match_when: MatchRule
    route_ids: list[str] = field(default_factory=list)
    applies_when: dict = field(default_factory=dict)


@dataclass
class Route:
    id: str
    origin: str
    destination: str
    distance_km: int
    typical_via: str


ROUTES: dict[str, Route] = {
    "tauranga_auckland": Route(id="tauranga_auckland", origin="Tauranga (Mt Maunganui)", destination="Auckland (Penrose)", distance_km=235, typical_via="SH2 → SH1 (via Karangahake or SH29 Kaimai)"),
    "tauranga_hamilton": Route(id="tauranga_hamilton", origin="Tauranga (Mt Maunganui)", destination="Hamilton", distance_km=105, typical_via="SH29 over Kaimai"),
    "auckland_wellington": Route(id="auckland_wellington", origin="Auckland (Penrose)", destination="Wellington", distance_km=645, typical_via="SH1 via Hamilton, Taupo, Bulls"),
    "tauranga_wellington": Route(id="tauranga_wellington", origin="Tauranga (Mt Maunganui)", destination="Wellington", distance_km=555, typical_via="SH2 via Napier, then SH2/SH1 to Wellington"),
    "tauranga_rotorua": Route(id="tauranga_rotorua", origin="Tauranga", destination="Rotorua", distance_km=85, typical_via="SH36 or SH33"),
    "auckland_whangarei": Route(id="auckland_whangarei", origin="Auckland", destination="Whangārei", distance_km=160, typical_via="SH1 Northern Motorway"),
}


# Stopwords stripped before matching. These are filler words that aren't informative.
STOPWORDS = {
    "to", "via", "the", "from", "and", "then", "going", "trip",
    "through", "a", "an", "another", "of", "by", "on", "in",
    "nz", "rural", "back", "roads", "nowhere", "paddock",
}


# Aliases expand a phrase into its canonical keywords.
# Applied AFTER stopword removal.
KEYWORD_ALIASES: dict[str, list[str]] = {
    "mt maunganui": ["tauranga", "mt maunganui", "bay of plenty"],
    "mt. maunganui": ["tauranga", "mt maunganui", "bay of plenty"],
    "mount maunganui": ["tauranga", "mt maunganui", "bay of plenty"],
    "bop": ["bay of plenty", "tauranga"],
    "akl": ["auckland"],
    "wgtn": ["wellington"],
    "tga": ["tauranga"],
    "kaimais": ["kaimai", "sh29"],
    "the kaimais": ["kaimai", "sh29"],
    "south auckland": ["south auckland", "auckland", "bombay", "pokeno"],
    "tauranga eastern link": ["tel", "tauranga eastern link"],
    "warkworth": ["warkworth", "northland"],
    "silverdale": ["silverdale", "northland"],
    "brynderwyn": ["brynderwyns", "brynderwyn"],
    "brynderwyns": ["brynderwyns", "brynderwyn"],
}


ISSUES: list[Issue] = [
    # ---- SH29 Kaimai corridor (Tauranga ↔ Hamilton) ----
    Issue(
        title="SH29 Kaimai overhead clearance",
        description="Multiple overhead obstructions on SH29 over the Kaimai Range. Class 2 pilot required to manage clearances. Consider SH2 via Karangahake for loads >5.0m high.",
        severity="warning",
        match_when=MatchRule(
            any_of=["sh29", "kaimai"],
            all_of_groups=[
                ["tauranga", "hamilton"],
                ["mt maunganui", "hamilton"],
                ["bay of plenty", "waikato"],
            ],
        ),
        route_ids=["tauranga_auckland", "tauranga_hamilton"],
        applies_when={"min_height_m": 4.5},
    ),
    Issue(
        title="Ōmanawa River Bridge (SH29)",
        description="Bridge requires BESS-registered driver for overweight loads. Speed restriction 20 km/h while crossing. Subject to occasional strengthening closures.",
        severity="warning",
        match_when=MatchRule(
            any_of=["sh29", "kaimai", "omanawa"],
            all_of_groups=[["tauranga", "hamilton"]],
        ),
        route_ids=["tauranga_auckland", "tauranga_hamilton"],
        applies_when={"min_weight_kg": 45_000},
    ),
    # ---- Tauranga Eastern Link toll (only if user mentions it) ----
    Issue(
        title="Tauranga Eastern Link (toll road)",
        description="NZTA has approved overdimension travel on TEL up to 8.5m wide x 5.4m high. Print toll authority and carry in cab.",
        severity="info",
        match_when=MatchRule(
            any_of=["tel", "tauranga eastern link", "eastern link"],
        ),
        route_ids=["tauranga_auckland"],
        applies_when={"min_width_m": 2.5},
    ),
    # ---- Bombay / Pokeno SH1 ----
    Issue(
        title="Bombay Hills bridge restrictions",
        description="Several BESS bridges on SH1 between Pokeno and Bombay. BESS registration required for loads over standard weight.",
        severity="warning",
        match_when=MatchRule(
            any_of=["bombay", "pokeno"],
            all_of_groups=[
                ["auckland", "hamilton"],
                ["south auckland"],
            ],
        ),
        route_ids=["tauranga_auckland"],
        applies_when={"min_weight_kg": 50_000},
    ),
    # ---- Auckland Southern Motorway ----
    # Only fires if user explicitly mentions Auckland AND a motorway/SH1 indicator,
    # OR mentions specific Auckland southern landmarks.
    Issue(
        title="Auckland Southern Motorway — TMP required",
        description="Cat 4B loads on Auckland motorways require Traffic Management Plan and Auckland Transport approval in addition to NZTA permit.",
        severity="blocker",
        match_when=MatchRule(
            any_of=["southern motorway", "penrose", "manukau", "auckland"],
            all_of_groups=[
                ["auckland", "sh1"],
                ["auckland", "motorway"],
            ],
        ),
        route_ids=["tauranga_auckland", "auckland_wellington"],
        applies_when={"min_width_m": 5.0},
    ),
    # ---- Long-distance SH1 BESS bridges ----
    Issue(
        title="Multiple BESS bridges (long-haul SH1)",
        description="Long-distance SH1 routes cross 15+ BESS-restricted bridges. BESS-registered driver mandatory. Allow extra time for crawl-speed crossings.",
        severity="warning",
        match_when=MatchRule(
            any_of=[],
            all_of_groups=[
                ["sh1", "auckland", "wellington"],
                ["sh1", "wellington", "hamilton"],
                ["taupo", "sh1"],
                ["bulls", "sh1"],
            ],
        ),
        route_ids=["auckland_wellington"],
        applies_when={"min_weight_kg": 50_000},
    ),
    Issue(
        title="Desert Road (SH1) elevation",
        description="High-altitude section between Waiouru and Turangi. Weather closures in winter affect oversize movements. Check road status before departure May-September.",
        severity="info",
        match_when=MatchRule(
            any_of=["desert road", "waiouru", "turangi", "central plateau"],
            all_of_groups=[
                ["auckland", "wellington", "sh1"],
            ],
        ),
        route_ids=["auckland_wellington"],
    ),
    Issue(
        title="Wellington Motorway height restrictions",
        description="SH1 Wellington Urban Motorway has tunnel and overhead restrictions. Loads over 4.5m height must use alternate route via SH58.",
        severity="blocker",
        match_when=MatchRule(
            any_of=["ngauranga", "mt victoria tunnel", "urban motorway", "wellington"],
            all_of_groups=[
                ["wellington", "sh1"],
                ["wellington", "motorway"],
            ],
        ),
        route_ids=["auckland_wellington", "tauranga_wellington"],
        applies_when={"min_height_m": 4.5},
    ),
    Issue(
        title="Cat 4B engineering assessment for long-haul",
        description="Long-distance Cat 4B moves often require multi-day journey with overnight stops. Chartered Engineer route assessment must cover full route.",
        severity="warning",
        match_when=MatchRule(
            any_of=[],
            all_of_groups=[
                ["auckland", "wellington"],
                ["tauranga", "wellington"],
                ["hamilton", "wellington"],
            ],
        ),
        route_ids=["auckland_wellington", "tauranga_wellington"],
        applies_when={"min_width_m": 5.0},
    ),
    # ---- SH2 Tauranga ↔ Wellington ----
    Issue(
        title="SH2 Eskdale to Napier",
        description="Winding coastal section with multiple bridges. BESS registration required for overweight loads on Wairoa River bridges.",
        severity="warning",
        match_when=MatchRule(
            any_of=["eskdale", "wairoa"],
            all_of_groups=[
                ["sh2", "napier"],
                ["sh2", "hawkes bay"],
                ["tauranga", "napier"],
            ],
        ),
        route_ids=["tauranga_wellington"],
        applies_when={"min_weight_kg": 45_000},
    ),
    Issue(
        title="SH2 Wairarapa BESS bridges",
        description="Multiple BESS-restricted bridges between Masterton and Featherston. Crawl-speed crossings, expect delays.",
        severity="warning",
        match_when=MatchRule(
            any_of=["wairarapa", "masterton", "featherston"],
            all_of_groups=[["sh2", "wellington"]],
        ),
        route_ids=["tauranga_wellington"],
        applies_when={"min_weight_kg": 50_000},
    ),
    Issue(
        title="Rimutaka Hill Road",
        description="Steep gradient and tight corners on SH2 Rimutaka. Not suitable for loads >25m length without specific approval.",
        severity="warning",
        match_when=MatchRule(
            any_of=["rimutaka"],
        ),
        route_ids=["tauranga_wellington"],
        applies_when={"min_length_m": 25.0},
    ),
    # ---- SH36 / SH33 (Tauranga ↔ Rotorua) ----
    Issue(
        title="SH36 width restrictions",
        description="SH36 has several narrow sections through forestry country. Loads >4.5m wide should use SH33 instead.",
        severity="warning",
        match_when=MatchRule(
            any_of=["sh36", "pyes pa"],
            all_of_groups=[["tauranga", "rotorua"]],
        ),
        route_ids=["tauranga_rotorua"],
        applies_when={"min_width_m": 4.5},
    ),
    Issue(
        title="SH33 Paengaroa overhead",
        description="Power lines at Paengaroa intersection may require Powerco consent for loads over 4.5m high.",
        severity="info",
        match_when=MatchRule(
            any_of=["sh33", "paengaroa"],
            all_of_groups=[["tauranga", "rotorua"]],
        ),
        route_ids=["tauranga_rotorua"],
        applies_when={"min_height_m": 4.5},
    ),
    # ---- SH1 Northland (Auckland ↔ Whangārei) ----
    Issue(
        title="SH1 Warkworth to Silverdale toll road",
        description="NZTA has approved overdimension travel on this toll section up to 8.5m wide x 5.4m high. Loads exceeding must use bypass route. Print toll authority.",
        severity="info",
        match_when=MatchRule(
            any_of=["warkworth", "silverdale"],
            all_of_groups=[
                ["auckland", "whangarei"],
                ["auckland", "northland"],
            ],
        ),
        route_ids=["auckland_whangarei"],
        applies_when={"min_width_m": 2.5},
    ),
    Issue(
        title="Brynderwyn Hills (SH1)",
        description="Tight winding section, regular slips. Subject to closures - check NZTA road status. Pilot required for loads >3.5m wide.",
        severity="warning",
        match_when=MatchRule(
            any_of=["brynderwyns", "brynderwyn"],
            all_of_groups=[
                ["auckland", "whangarei"],
                ["auckland", "northland"],
            ],
        ),
        route_ids=["auckland_whangarei"],
        applies_when={"min_width_m": 3.5},
    ),
]


def get_route_options() -> list[dict]:
    return [
        {"id": r.id, "label": f"{r.origin} → {r.destination}", "via": r.typical_via, "distance_km": r.distance_km}
        for r in ROUTES.values()
    ]


def _load_passes_applies_when(applies_when: dict, width_m: float, height_m: float, length_m: float, weight_kg: int) -> bool:
    for key, threshold in applies_when.items():
        if key == "min_width_m" and width_m < threshold:
            return False
        if key == "min_height_m" and height_m < threshold:
            return False
        if key == "min_length_m" and length_m < threshold:
            return False
        if key == "min_weight_kg" and weight_kg < threshold:
            return False
    return True


def _format_issues(issues: list[Issue]) -> list[dict]:
    return [{"title": i.title, "description": i.description, "severity": i.severity} for i in issues]


def _summarise(issues: list[dict]) -> dict:
    blockers = sum(1 for i in issues if i["severity"] == "blocker")
    warnings = sum(1 for i in issues if i["severity"] == "warning")
    info = sum(1 for i in issues if i["severity"] == "info")
    return {
        "total": len(issues),
        "blockers": blockers,
        "warnings": warnings,
        "info": info,
        "clear_to_proceed": blockers == 0,
    }


def check_route(route_id: str, width_m: float, height_m: float, length_m: float, weight_kg: int) -> dict:
    """Pre-defined route check (dropdown path) — unchanged semantics."""
    if route_id not in ROUTES:
        return {"error": "Unknown route", "route_id": route_id, "issues": []}
    route = ROUTES[route_id]
    triggered = [
        issue for issue in ISSUES
        if route_id in issue.route_ids
        and _load_passes_applies_when(issue.applies_when, width_m, height_m, length_m, weight_kg)
    ]
    issue_dicts = _format_issues(triggered)
    return {
        "route_id": route_id,
        "route_label": f"{route.origin} → {route.destination}",
        "distance_km": route.distance_km,
        "typical_via": route.typical_via,
        "issues": issue_dicts,
        "summary": _summarise(issue_dicts),
    }


def _extract_keywords(text: str) -> set[str]:
    """Extract canonical keywords from free-text route input.

    Steps:
    1. Lowercase, replace arrows/slashes/punctuation with spaces.
    2. Try matching multi-word aliases first (e.g. "south auckland", "mt maunganui").
    3. Tokenise remaining words, drop stopwords.
    4. Expand any token that matches a single-token alias.
    """
    if not text:
        return set()
    cleaned = re.sub(r"[→\->/,]+", " ", text.lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    found: set[str] = set()

    # Multi-word aliases (longest first so "mt maunganui" beats "mt")
    sorted_aliases = sorted(KEYWORD_ALIASES.keys(), key=lambda x: -len(x))
    consumed_ranges: list[tuple[int, int]] = []
    for alias in sorted_aliases:
        if " " not in alias:
            continue
        start = 0
        while True:
            idx = cleaned.find(alias, start)
            if idx == -1:
                break
            # Check boundaries: must be at start/end or surrounded by spaces
            end_idx = idx + len(alias)
            left_ok = (idx == 0 or cleaned[idx - 1] == " ")
            right_ok = (end_idx == len(cleaned) or cleaned[end_idx] == " ")
            if left_ok and right_ok:
                found.update(KEYWORD_ALIASES[alias])
                consumed_ranges.append((idx, end_idx))
            start = idx + 1

    # Build a mask of consumed characters so tokeniser skips them
    masked = list(cleaned)
    for s, e in consumed_ranges:
        for i in range(s, e):
            masked[i] = " "
    remainder = "".join(masked)

    # Single-word tokens
    for token in remainder.split():
        t = re.sub(r"^[^a-z0-9]+|[^a-z0-9]+$", "", token)
        if not t or t in STOPWORDS:
            continue
        found.add(t)
        # Expand single-token aliases
        if t in KEYWORD_ALIASES:
            found.update(KEYWORD_ALIASES[t])

    return found


def _issue_matches(issue: Issue, keywords: set[str]) -> bool:
    """Decide whether an issue's match_when rule is satisfied by the keyword set."""
    # any_of: any single keyword triggers
    for kw in issue.match_when.any_of:
        if kw in keywords:
            return True
    # all_of_groups: ANY group whose keywords are ALL present triggers
    for group in issue.match_when.all_of_groups:
        if group and all(kw in keywords for kw in group):
            return True
    return False


def check_route_text(text: str, width_m: float, height_m: float, length_m: float, weight_kg: int) -> dict:
    """Free-text route check (combobox path)."""
    keywords = _extract_keywords(text)
    if not keywords:
        return {
            "route_id": None,
            "route_label": (text.strip()[:200]) if text else "Unknown route",
            "distance_km": 0,
            "typical_via": "Not recognised — no keywords matched",
            "issues": [],
            "summary": _summarise([]),
            "matched_keywords": [],
        }

    triggered = [
        issue for issue in ISSUES
        if _issue_matches(issue, keywords)
        and _load_passes_applies_when(issue.applies_when, width_m, height_m, length_m, weight_kg)
    ]
    # Deduplicate by title
    seen = set()
    unique = []
    for issue in triggered:
        if issue.title not in seen:
            unique.append(issue)
            seen.add(issue.title)

    issue_dicts = _format_issues(unique)
    return {
        "route_id": None,
        "route_label": text.strip()[:200],
        "distance_km": 0,
        "typical_via": f"Free-text route ({len(keywords)} keyword{'s' if len(keywords) != 1 else ''} matched)",
        "issues": issue_dicts,
        "summary": _summarise(issue_dicts),
        "matched_keywords": sorted(keywords),
    }
