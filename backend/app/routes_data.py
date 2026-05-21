"""Hardcoded route restriction data for the MVP.

Real NZ-specific known issues for common heavy haulage routes.
Sourced from NZTA route restrictions, NZHHA published guidance,
and known maintenance/upgrade history.

This is a seed dataset. A real product would have hundreds of
restrictions and customer-contributed data.
"""
from dataclasses import dataclass, field


@dataclass
class RouteIssue:
    """A known issue on a specific route."""
    title: str
    description: str
    severity: str  # "info", "warning", "blocker"
    applies_when: dict = field(default_factory=dict)
    # applies_when keys: min_width_m, min_height_m, min_length_m, min_weight_kg


@dataclass
class Route:
    """A pre-defined route with known issues."""
    id: str
    origin: str
    destination: str
    distance_km: int
    typical_via: str
    issues: list[RouteIssue] = field(default_factory=list)


# Real-ish NZ heavy haulage routes
ROUTES: dict[str, Route] = {
    "tauranga_auckland": Route(
        id="tauranga_auckland",
        origin="Tauranga (Mt Maunganui)",
        destination="Auckland (Penrose)",
        distance_km=235,
        typical_via="SH2 → SH1 (via Karangahake or SH29 Kaimai)",
        issues=[
            RouteIssue(
                title="SH29 Kaimai overhead clearance",
                description="Multiple overhead obstructions on SH29 over the Kaimai Range. Class 2 pilot required to manage clearances. Consider SH2 via Karangahake for loads >5.0m high.",
                severity="warning",
                applies_when={"min_height_m": 4.5},
            ),
            RouteIssue(
                title="Ōmanawa River Bridge (SH29)",
                description="Bridge requires BESS-registered driver for overweight loads. Subject to occasional strengthening closures. Check NZTA for current status.",
                severity="warning",
                applies_when={"min_weight_kg": 45_000},
            ),
            RouteIssue(
                title="Tauranga Eastern Link (toll road)",
                description="NZTA has approved overdimension travel on TEL up to 8.5m wide x 5.4m high. Print toll authority and carry in cab.",
                severity="info",
                applies_when={"min_width_m": 2.5},
            ),
            RouteIssue(
                title="Bombay Hills bridge restrictions",
                description="Several BESS bridges on SH1 between Pokeno and Bombay. BESS registration required for loads over standard weight.",
                severity="warning",
                applies_when={"min_weight_kg": 50_000},
            ),
            RouteIssue(
                title="Auckland Southern Motorway",
                description="Cat 4B loads on Auckland motorways require Traffic Management Plan and Auckland Transport approval in addition to NZTA permit.",
                severity="blocker",
                applies_when={"min_width_m": 5.0},
            ),
        ],
    ),
    "tauranga_hamilton": Route(
        id="tauranga_hamilton",
        origin="Tauranga (Mt Maunganui)",
        destination="Hamilton",
        distance_km=105,
        typical_via="SH29 over Kaimai",
        issues=[
            RouteIssue(
                title="SH29 Kaimai overhead clearance",
                description="Multiple overhead obstructions on SH29 over the Kaimai Range. Asset owner consent required from Powerco for loads over 4.5m height.",
                severity="warning",
                applies_when={"min_height_m": 4.5},
            ),
            RouteIssue(
                title="Ōmanawa River Bridge (SH29)",
                description="BESS-registered driver required for overweight loads. Speed restriction 20 km/h while crossing.",
                severity="warning",
                applies_when={"min_weight_kg": 45_000},
            ),
        ],
    ),
    "auckland_wellington": Route(
        id="auckland_wellington",
        origin="Auckland (Penrose)",
        destination="Wellington",
        distance_km=645,
        typical_via="SH1 via Hamilton, Taupo, Bulls",
        issues=[
            RouteIssue(
                title="Multiple BESS bridges",
                description="Long-distance route crosses 15+ BESS-restricted bridges. BESS-registered driver mandatory. Allow extra time for crawl-speed crossings.",
                severity="warning",
                applies_when={"min_weight_kg": 50_000},
            ),
            RouteIssue(
                title="Desert Road (SH1) elevation",
                description="High-altitude section between Waiouru and Turangi. Weather closures in winter affect oversize movements. Check road status before departure May-September.",
                severity="info",
            ),
            RouteIssue(
                title="Wellington Motorway height restrictions",
                description="SH1 Wellington Urban Motorway has tunnel and overhead restrictions. Loads over 4.5m height must use alternate route via SH58.",
                severity="blocker",
                applies_when={"min_height_m": 4.5},
            ),
            RouteIssue(
                title="Cat 4B engineering assessment",
                description="Long-distance Cat 4B moves often require multi-day journey with overnight stops. Chartered Engineer route assessment must cover full route.",
                severity="warning",
                applies_when={"min_width_m": 5.0},
            ),
        ],
    ),
    "tauranga_wellington": Route(
        id="tauranga_wellington",
        origin="Tauranga (Mt Maunganui)",
        destination="Wellington",
        distance_km=555,
        typical_via="SH2 via Napier, then SH2/SH1 to Wellington",
        issues=[
            RouteIssue(
                title="SH2 Eskdale to Napier",
                description="Winding coastal section with multiple bridges. BESS registration required for overweight loads on Wairoa River bridges.",
                severity="warning",
                applies_when={"min_weight_kg": 45_000},
            ),
            RouteIssue(
                title="SH2 Wairarapa BESS bridges",
                description="Multiple BESS-restricted bridges between Masterton and Featherston. Crawl-speed crossings, expect delays.",
                severity="warning",
                applies_when={"min_weight_kg": 50_000},
            ),
            RouteIssue(
                title="Rimutaka Hill Road",
                description="Steep gradient and tight corners on SH2 Rimutaka. Not suitable for loads >25m length without specific approval.",
                severity="warning",
                applies_when={"min_length_m": 25.0},
            ),
        ],
    ),
    "tauranga_rotorua": Route(
        id="tauranga_rotorua",
        origin="Tauranga",
        destination="Rotorua",
        distance_km=85,
        typical_via="SH36 or SH33",
        issues=[
            RouteIssue(
                title="SH36 width restrictions",
                description="SH36 has several narrow sections through forestry country. Loads >4.5m wide should use SH33 instead.",
                severity="warning",
                applies_when={"min_width_m": 4.5},
            ),
            RouteIssue(
                title="SH33 Paengaroa overhead",
                description="Power lines at Paengaroa intersection may require Powerco consent for loads over 4.5m high.",
                severity="info",
                applies_when={"min_height_m": 4.5},
            ),
        ],
    ),
    "auckland_whangarei": Route(
        id="auckland_whangarei",
        origin="Auckland",
        destination="Whangārei",
        distance_km=160,
        typical_via="SH1 Northern Motorway",
        issues=[
            RouteIssue(
                title="SH1 Warkworth to Silverdale toll road",
                description="NZTA has approved overdimension travel on this toll section up to 8.5m wide x 5.4m high. Loads exceeding must use bypass route. Print toll authority.",
                severity="info",
                applies_when={"min_width_m": 2.5},
            ),
            RouteIssue(
                title="Brynderwyn Hills (SH1)",
                description="Tight winding section, regular slips. Subject to closures - check NZTA road status. Pilot required for loads >3.5m wide.",
                severity="warning",
                applies_when={"min_width_m": 3.5},
            ),
        ],
    ),
}


def get_route_options() -> list[dict]:
    """Return route options for the frontend dropdown."""
    return [
        {
            "id": r.id,
            "label": f"{r.origin} → {r.destination}",
            "via": r.typical_via,
            "distance_km": r.distance_km,
        }
        for r in ROUTES.values()
    ]


def check_route(route_id: str, width_m: float, height_m: float, length_m: float, weight_kg: int) -> dict:
    """Cross-reference a load against a route's known issues."""
    if route_id not in ROUTES:
        return {"error": "Unknown route", "route_id": route_id, "issues": []}

    route = ROUTES[route_id]
    triggered_issues = []

    for issue in route.issues:
        applies = True
        for key, threshold in issue.applies_when.items():
            if key == "min_width_m" and width_m < threshold:
                applies = False
            elif key == "min_height_m" and height_m < threshold:
                applies = False
            elif key == "min_length_m" and length_m < threshold:
                applies = False
            elif key == "min_weight_kg" and weight_kg < threshold:
                applies = False
        if applies:
            triggered_issues.append({
                "title": issue.title,
                "description": issue.description,
                "severity": issue.severity,
            })

    blocker_count = sum(1 for i in triggered_issues if i["severity"] == "blocker")
    warning_count = sum(1 for i in triggered_issues if i["severity"] == "warning")
    info_count = sum(1 for i in triggered_issues if i["severity"] == "info")

    return {
        "route_id": route_id,
        "route_label": f"{route.origin} → {route.destination}",
        "distance_km": route.distance_km,
        "typical_via": route.typical_via,
        "issues": triggered_issues,
        "summary": {
            "total": len(triggered_issues),
            "blockers": blocker_count,
            "warnings": warning_count,
            "info": info_count,
            "clear_to_proceed": blocker_count == 0,
        },
    }
