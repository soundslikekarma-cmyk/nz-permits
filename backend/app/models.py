"""API request/response models. Pydantic v2."""
from pydantic import BaseModel, Field, ConfigDict


class LoadRequest(BaseModel):
    """Incoming load to classify."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "width_m": 6.5,
            "height_m": 5.2,
            "length_m": 14.0,
            "weight_kg": 28000,
            "indivisible": True,
        }
    })

    width_m: float = Field(gt=0, le=15, description="Total width including overhang, metres")
    height_m: float = Field(gt=0, le=8, description="Total height from ground, metres")
    length_m: float = Field(gt=0, le=50, description="Total combination length, metres")
    weight_kg: int = Field(gt=0, le=500_000, description="Total weight, kilograms")
    indivisible: bool = Field(default=True, description="Is the load indivisible?")


class PilotInfo(BaseModel):
    front_count: int
    front_class: str
    rear_count: int
    rear_class: str


class ClassificationResponse(BaseModel):
    """Result of classifying a load."""
    category: str
    category_label: str
    permit_status: str          # NEW
    permit_status_label: str    # NEW
    overdimension: bool
    overweight: bool
    requires_permit: bool
    requires_engineering_assessment: bool
    pilots: PilotInfo
    notes: list[str]


CATEGORY_LABELS = {
    "standard": "Standard",
    "cat_1": "Category 1 — minor overdimension",
    "cat_2": "Category 2 — overdimension",
    "cat_3": "Category 3 — permit required",
    "cat_4a": "Category 4A — permit required (very large)",
    "cat_4b": "Category 4B — permit + engineering assessment required",
}


PERMIT_STATUS_LABELS = {
    "none": "No permit required",
    "overweight": "Overweight permit required",
    "overdimension": "Overdimension permit required",
    "both": "Overdimension + overweight permits required",
    "cat_4b": "Cat 4B — permit + engineering assessment required",
}


class RouteCheckRequest(BaseModel):
    """Combined request: classify a load AND check it against a route."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "route_id": "tauranga_auckland",
            "width_m": 6.5,
            "height_m": 5.2,
            "length_m": 14.0,
            "weight_kg": 28000,
            "indivisible": True,
        }
    })
    route_id: str = Field(description="One of the predefined route IDs")
    width_m: float = Field(gt=0, le=15)
    height_m: float = Field(gt=0, le=8)
    length_m: float = Field(gt=0, le=50)
    weight_kg: int = Field(gt=0, le=500_000)
    indivisible: bool = True


class RouteIssueResponse(BaseModel):
    title: str
    description: str
    severity: str


class RouteSummary(BaseModel):
    total: int
    blockers: int
    warnings: int
    info: int
    clear_to_proceed: bool


class RouteCheckResponse(BaseModel):
    route_id: str
    route_label: str
    distance_km: int
    typical_via: str
    issues: list[RouteIssueResponse]
    summary: RouteSummary


class RouteOption(BaseModel):
    id: str
    label: str
    via: str
    distance_km: int
