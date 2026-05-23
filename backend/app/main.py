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
from app.routes_data import get_route_options, check_route, check_route_text
from app.models import RouteCheckRequest, RouteCheckResponse, RouteOption, RouteCheckTextRequest, RouteCheckTextResponse

from fastapi import HTTPException, Query
from app.database import init_db, create_job, get_job, list_jobs, delete_job
from app.models import SaveJobRequest, JobResponse, DeleteResponse

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


@app.on_event("startup")
def on_startup() -> None:
    init_db()


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


@app.get("/routes", response_model=list[RouteOption])
def list_routes() -> list[RouteOption]:
    """List all pre-defined heavy haulage routes available for checking."""
    return [RouteOption(**r) for r in get_route_options()]


@app.post("/check-route", response_model=RouteCheckResponse)
def check_route_endpoint(req: RouteCheckRequest) -> RouteCheckResponse:
    """Check a load against a pre-defined route's known issues."""
    result = check_route(
        route_id=req.route_id,
        width_m=req.width_m,
        height_m=req.height_m,
        length_m=req.length_m,
        weight_kg=req.weight_kg,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return RouteCheckResponse(**result)


@app.post("/check-route-text", response_model=RouteCheckTextResponse)
def check_route_text_endpoint(req: RouteCheckTextRequest) -> RouteCheckTextResponse:
    """Check a load against a free-text route description."""
    result = check_route_text(
        text=req.route_text,
        width_m=req.width_m,
        height_m=req.height_m,
        length_m=req.length_m,
        weight_kg=req.weight_kg,
    )
    return RouteCheckTextResponse(**result)


@app.post("/jobs", response_model=JobResponse, status_code=201)
def save_job(req: SaveJobRequest) -> JobResponse:
    """Save a new job for a device."""
    job = create_job(
        device_id=req.device_id,
        name=req.name,
        load_input=req.load_input,
        classification=req.classification,
        route_check=req.route_check,
    )
    return JobResponse(**job)


@app.get("/jobs", response_model=list[JobResponse])
def list_jobs_endpoint(
    device_id: str = Query(..., min_length=8, max_length=100),
    limit: int = Query(50, ge=1, le=200),
) -> list[JobResponse]:
    """List jobs belonging to a device."""
    jobs = list_jobs(device_id=device_id, limit=limit)
    return [JobResponse(**j) for j in jobs]


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job_endpoint(job_id: str) -> JobResponse:
    """Fetch a specific job by ID."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(**job)


@app.delete("/jobs/{job_id}", response_model=DeleteResponse)
def delete_job_endpoint(
    job_id: str,
    device_id: str = Query(..., min_length=8, max_length=100),
) -> DeleteResponse:
    """Delete a job. Requires the device_id that owns it."""
    deleted = delete_job(job_id=job_id, device_id=device_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Job not found or not owned by device")
    return DeleteResponse(deleted=True, job_id=job_id)
