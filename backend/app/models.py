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
    weight_kg: int = Field(gt=0, le=300_000, description="Total weight, kilograms")
    indivisible: bool = Field(default=True, description="Is the load indivisible?")


class PilotInfo(BaseModel):
    front_count: int
    front_class: str
    rear_count: int
    rear_class: str


class ClassificationResponse(BaseModel):
    """Result of classifying a load."""
    category: str
    category_label: str  # Human-readable label
    overdimension: bool
    overweight: bool
    requires_permit: bool
    requires_engineering_assessment: bool
    pilots: PilotInfo
    notes: list[str]


CATEGORY_LABELS = {
    "standard": "Standard (no permit required)",
    "cat_1": "Category 1 — minor overdimension",
    "cat_2": "Category 2 — overdimension",
    "cat_3": "Category 3 — permit required",
    "cat_4a": "Category 4A — permit required (very large)",
    "cat_4b": "Category 4B — permit + engineering assessment required",
}
