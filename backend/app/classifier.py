from dataclasses import dataclass
from enum import Enum


class Category(str, Enum):
    """VDAM Rule overdimension/overweight categories."""
    STANDARD = "standard"  # Within normal limits, no permit needed
    CAT_1 = "cat_1"        # Minor overdim, operating rules apply
    CAT_2 = "cat_2"        # Larger overdim, more rules
    CAT_3 = "cat_3"        # Big overdim, permit required
    CAT_4A = "cat_4a"      # Very large, permit + extra
    CAT_4B = "cat_4b"      # Largest, permit + engineering assessment


class PilotClass(str, Enum):
    NONE = "none"
    CLASS_1 = "class_1"
    CLASS_2 = "class_2"


@dataclass
class LoadInput:
    width_m: float
    height_m: float
    length_m: float          # Total combination length
    weight_kg: int
    indivisible: bool = True


@dataclass
class PilotRequirement:
    front_count: int
    front_class: PilotClass
    rear_count: int
    rear_class: PilotClass


@dataclass
class ClassificationResult:
    category: Category
    overdimension: bool
    overweight: bool
    pilots: PilotRequirement
    requires_permit: bool
    requires_engineering_assessment: bool   # Cat 4B
    notes: list[str]                         # Warnings, requirements, callouts


# VDAM thresholds (Land Transport Rule: Vehicle Dimensions and Mass 2016)
STANDARD_WIDTH_M = 2.55
STANDARD_HEIGHT_M = 4.30
STANDARD_LENGTH_M = 22.00   # Standard truck-trailer combination
STANDARD_WEIGHT_KG = 44_000  # Simplified — actual depends on axle config

CAT_1_MAX_WIDTH = 3.10
CAT_2_MAX_WIDTH = 3.70
CAT_3_MAX_WIDTH = 5.00
# Cat 4 = >5.00m wide

KIWIRAIL_LENGTH_THRESHOLD_M = 25.0
OVERHEIGHT_CONSENT_THRESHOLD_M = 4.30


def classify_load(load: LoadInput) -> ClassificationResult:
    """
    Classify a load against VDAM Rule 2016 and determine pilot/permit requirements.

    Width drives category (primary determinant for overdimension).
    Weight drives overweight permit separately.
    Length and height add additional requirements.
    """
    notes: list[str] = []

    # Overdimension check
    is_overdim_width = load.width_m > STANDARD_WIDTH_M
    is_overdim_height = load.height_m > STANDARD_HEIGHT_M
    is_overdim_length = load.length_m > STANDARD_LENGTH_M
    overdimension = is_overdim_width or is_overdim_height or is_overdim_length

    # Overweight check (simplified)
    overweight = load.weight_kg > STANDARD_WEIGHT_KG

    # Determine category from width
    if load.width_m > CAT_3_MAX_WIDTH:
        category = Category.CAT_4B  # >5m → engineering assessment required
    elif load.width_m > CAT_2_MAX_WIDTH:
        category = Category.CAT_3
    elif load.width_m > CAT_1_MAX_WIDTH:
        category = Category.CAT_2
    elif load.width_m > STANDARD_WIDTH_M:
        category = Category.CAT_1
    else:
        category = Category.STANDARD

    # Pilot requirements based on width
    pilots = _determine_pilots(load.width_m, category)

    # Permit requirements
    requires_permit = category in (Category.CAT_3, Category.CAT_4A, Category.CAT_4B)
    requires_engineering = category == Category.CAT_4B

    # Notes / warnings
    if overweight:
        notes.append(f"Overweight: {load.weight_kg:,} kg exceeds standard {STANDARD_WEIGHT_KG:,} kg. Separate overweight permit required.")
    if is_overdim_height:
        notes.append(f"Overheight: {load.height_m}m exceeds {STANDARD_HEIGHT_M}m. Asset owner consent required for overhead obstructions (power lines).")
    if load.length_m > KIWIRAIL_LENGTH_THRESHOLD_M:
        notes.append(f"Long load: {load.length_m}m exceeds {KIWIRAIL_LENGTH_THRESHOLD_M}m. KiwiRail consent required for level crossings.")
    if requires_engineering:
        notes.append("Cat 4B: Chartered Professional Engineer assessment required before NZTA will accept permit.")
    if not load.indivisible:
        notes.append("Load is divisible. Indivisibility is required for Cat 3+ overdimension permits.")

    return ClassificationResult(
        category=category,
        overdimension=overdimension,
        overweight=overweight,
        pilots=pilots,
        requires_permit=requires_permit,
        requires_engineering_assessment=requires_engineering,
        notes=notes,
    )


def _determine_pilots(width_m: float, category: Category) -> PilotRequirement:
    """
    Pilot requirements per VDAM Rule (simplified).

    Up to 3.10m: no pilot
    3.10m - 3.70m: 1 Class 1 front pilot
    3.70m - 4.50m: 1 Class 2 front pilot
    4.50m - 5.00m: 1 Class 2 front + 1 Class 2 rear
    5.00m+: 2 Class 2 front + 1 Class 2 rear (Cat 4)
    """
    if width_m <= 3.10:
        return PilotRequirement(0, PilotClass.NONE, 0, PilotClass.NONE)
    elif width_m <= 3.70:
        return PilotRequirement(1, PilotClass.CLASS_1, 0, PilotClass.NONE)
    elif width_m <= 4.50:
        return PilotRequirement(1, PilotClass.CLASS_2, 0, PilotClass.NONE)
    elif width_m <= 5.00:
        return PilotRequirement(1, PilotClass.CLASS_2, 1, PilotClass.CLASS_2)
    else:  # Cat 4
        return PilotRequirement(2, PilotClass.CLASS_2, 1, PilotClass.CLASS_2)
