"""FastAPI entry point for the NZ Heavy Haulage Permits MVP."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.classifier import LoadInput, classify_load
from app.models import (
    ClassificationResponse,
    LoadRequest,
    PilotInfo,
    CATEGORY_LABELS,
    PERMIT_STATUS_LABELS,
)

app = FastAPI(
    title="NZ Heavy Haulage Permits",
    description="MVP: load classification and permit assistance for NZ heavy haulage operators.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "name": "NZ Heavy Haulage Permits"}


@app.post("/classify", response_model=ClassificationResponse)
def classify(load: LoadRequest) -> ClassificationResponse:
    """Classify a load against VDAM Rule 2016 and return permit/pilot requirements."""
    result = classify_load(
        LoadInput(
            width_m=load.width_m,
            height_m=load.height_m,
            length_m=load.length_m,
            weight_kg=load.weight_kg,
            indivisible=load.indivisible,
        )
    )
    if result.requires_engineering_assessment:
        permit_status = "cat_4b"
    else:
        is_overdim_permit = result.category.value in ("cat_3", "cat_4a")
        if is_overdim_permit and result.overweight:
            permit_status = "both"
        elif is_overdim_permit:
            permit_status = "overdimension"
        elif result.overweight:
            permit_status = "overweight"
        else:
            permit_status = "none"

    return ClassificationResponse(
        category=result.category.value,
        category_label=CATEGORY_LABELS[result.category.value],
        permit_status=permit_status,
        permit_status_label=PERMIT_STATUS_LABELS[permit_status],
        overdimension=result.overdimension,
        overweight=result.overweight,
        requires_permit=result.requires_permit,
        requires_engineering_assessment=result.requires_engineering_assessment,
        pilots=PilotInfo(
            front_count=result.pilots.front_count,
            front_class=result.pilots.front_class.value,
            rear_count=result.pilots.rear_count,
            rear_class=result.pilots.rear_class.value,
        ),
        notes=result.notes,
    )
