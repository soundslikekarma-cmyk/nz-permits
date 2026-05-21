"""Tests for the load classifier."""
import pytest
from app.classifier import (
    LoadInput,
    Category,
    PilotClass,
    classify_load,
)


def test_standard_load_no_permit():
    """A normal truck-sized load needs no permit."""
    load = LoadInput(width_m=2.5, height_m=4.0, length_m=20.0, weight_kg=40_000)
    result = classify_load(load)
    assert result.category == Category.STANDARD
    assert not result.overdimension
    assert not result.overweight
    assert not result.requires_permit
    assert result.pilots.front_count == 0


def test_cat_1_wide_load():
    """A 3.0m wide load is Cat 1, no permit, no pilot."""
    load = LoadInput(width_m=3.0, height_m=4.0, length_m=20.0, weight_kg=40_000)
    result = classify_load(load)
    assert result.category == Category.CAT_1
    assert result.overdimension
    assert not result.requires_permit
    assert result.pilots.front_count == 0


def test_cat_2_needs_class_1_pilot():
    """A 3.5m wide load needs 1 Class 1 front pilot."""
    load = LoadInput(width_m=3.5, height_m=4.0, length_m=20.0, weight_kg=40_000)
    result = classify_load(load)
    assert result.category == Category.CAT_2
    assert result.pilots.front_count == 1
    assert result.pilots.front_class == PilotClass.CLASS_1
    assert result.pilots.rear_count == 0


def test_cat_3_needs_permit_and_class_2_pilot():
    """A 4.0m wide load is Cat 3, needs permit and Class 2 front pilot."""
    load = LoadInput(width_m=4.0, height_m=4.0, length_m=20.0, weight_kg=40_000)
    result = classify_load(load)
    assert result.category == Category.CAT_3
    assert result.requires_permit
    assert not result.requires_engineering_assessment
    assert result.pilots.front_count == 1
    assert result.pilots.front_class == PilotClass.CLASS_2


def test_cat_3_wide_needs_rear_pilot():
    """A 4.8m wide load needs Class 2 front and rear pilot."""
    load = LoadInput(width_m=4.8, height_m=4.0, length_m=20.0, weight_kg=40_000)
    result = classify_load(load)
    assert result.category == Category.CAT_3
    assert result.pilots.front_count == 1
    assert result.pilots.rear_count == 1
    assert result.pilots.rear_class == PilotClass.CLASS_2


def test_cat_4b_house_move():
    """A 6.5m wide house is Cat 4B, requires engineering assessment + 2+1 pilots."""
    load = LoadInput(width_m=6.5, height_m=5.2, length_m=14.0, weight_kg=28_000)
    result = classify_load(load)
    assert result.category == Category.CAT_4B
    assert result.requires_permit
    assert result.requires_engineering_assessment
    assert result.pilots.front_count == 2
    assert result.pilots.rear_count == 1
    assert any("Cat 4B" in n for n in result.notes)
    assert any("overhead" in n.lower() for n in result.notes)


def test_overweight_only():
    """A standard-size but heavy load flags overweight."""
    load = LoadInput(width_m=2.5, height_m=4.0, length_m=20.0, weight_kg=65_000)
    result = classify_load(load)
    assert result.overweight
    assert not result.overdimension
    assert any("Overweight" in n for n in result.notes)


def test_overheight_triggers_consent_note():
    """A tall load triggers asset owner consent note."""
    load = LoadInput(width_m=2.5, height_m=4.8, length_m=20.0, weight_kg=40_000)
    result = classify_load(load)
    assert result.overdimension
    assert any("Overhead" in n or "overhead" in n.lower() for n in result.notes)


def test_long_load_triggers_kiwirail_note():
    """A long load (>25m) triggers KiwiRail consent note."""
    load = LoadInput(width_m=2.5, height_m=4.0, length_m=28.0, weight_kg=40_000)
    result = classify_load(load)
    assert any("KiwiRail" in n for n in result.notes)


def test_divisible_load_flagged():
    """A divisible load is flagged as a problem for Cat 3+ permits."""
    load = LoadInput(width_m=4.0, height_m=4.0, length_m=20.0, weight_kg=40_000, indivisible=False)
    result = classify_load(load)
    assert any("divisible" in n.lower() for n in result.notes)


def test_boundary_width_exactly_3_10():
    """Width exactly at 3.10m should still be Cat 1 (boundary check)."""
    load = LoadInput(width_m=3.10, height_m=4.0, length_m=20.0, weight_kg=40_000)
    result = classify_load(load)
    assert result.category == Category.CAT_1
    assert result.pilots.front_count == 0  # boundary inclusive of "no pilot"


def test_overweight_narrow_load_still_needs_permit():
    """An overweight load needs a permit even if narrow (Cat 1)."""
    load = LoadInput(width_m=3.0, height_m=4.0, length_m=10.0, weight_kg=400_000)
    result = classify_load(load)
    assert result.overweight is True
    assert result.requires_permit is True, "Overweight loads must require a permit"


def test_overweight_standard_dimension_still_needs_permit():
    """A standard-width overweight load needs a permit."""
    load = LoadInput(width_m=2.5, height_m=4.0, length_m=20.0, weight_kg=60_000)
    result = classify_load(load)
    assert result.category == Category.STANDARD
    assert result.overweight is True
    assert result.requires_permit is True


def test_at_new_weight_threshold():
    """44,500kg is at the boundary — should NOT be overweight."""
    load = LoadInput(width_m=2.5, height_m=4.0, length_m=20.0, weight_kg=44_500)
    result = classify_load(load)
    assert result.overweight is False
