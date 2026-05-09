import os
from datetime import date, datetime
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, field_validator

from backend.models.student_profile import (
    StudentProfile,
    StudentProfilePatch,
    StudentProfileUpdateRequest,
    StudentProfileUpdateResponse,
    NationalityCategory,
    VisaType,
    BasicStatus,
    HousingStatus,
)
from backend.models.roadmap import (
    GenerateArrivalRoadmapRequest,
    GenerateArrivalRoadmapResponse,
    RenewalWindowRequest,
    RenewalWindowResponse,
)
from backend.services.deadline_calculator import calculate_renewal_window
from backend.services.roadmap_engine import generate_arrival_roadmap_response
from backend.storage import (
    add_call_summary,
    get_profile,
    init_db,
    list_call_summaries,
    profile_exists,
    save_profile,
)


app = FastAPI(
    title="CivicAid Étudiant Backend",
    description="Backend tools for the ElevenLabs non-EU student arrival roadmap agent.",
    version="0.1.0",
)

# For local frontend development later.
# In production, restrict this to your actual frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TOOL_TOKEN = os.getenv("CIVICAID_TOOL_TOKEN")


def verify_tool_token(
    x_civicaid_tool_token: Optional[str] = Header(default=None),
) -> None:
    """
    Optional protection for deployed ElevenLabs tool endpoints.

    If CIVICAID_TOOL_TOKEN is unset, tools remain open for local/demo testing.
    If set, callers must send X-CivicAid-Tool-Token with the same value.
    """
    if TOOL_TOKEN and x_civicaid_tool_token != TOOL_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing tool token.")


@app.on_event("startup")
def startup() -> None:
    init_db()


# ---------------------------------------------------------------------
# Shared tool request model
# ---------------------------------------------------------------------

class ToolBaseModel(BaseModel):
    """
    Base model for ElevenLabs tool calls.

    Why:
    - ElevenLabs may send partial arguments.
    - It may sometimes send extra metadata fields.
    - It may send empty strings for optional values.

    This prevents avoidable FastAPI 422 validation errors.
    """

    model_config = ConfigDict(extra="ignore")

    @field_validator("*", mode="before")
    @classmethod
    def empty_string_to_none(cls, value):
        if value == "":
            return None
        return value


# ---------------------------------------------------------------------
# Extra request/response models
# ---------------------------------------------------------------------

class SaveCallSummaryRequest(ToolBaseModel):
    student_id: str = "demo_001"
    summary: str
    conversation_id: Optional[str] = None


class SaveCallSummaryResponse(BaseModel):
    status: str
    student_id: str


class DebugProfileResponse(BaseModel):
    student_id: str
    profile: StudentProfile


class UpdateScopeProfileRequest(ToolBaseModel):
    student_id: str = "demo_001"
    nationality_category: Optional[NationalityCategory] = None
    country: Optional[str] = None


class UpdateArrivalVisaProfileRequest(ToolBaseModel):
    student_id: str = "demo_001"
    has_arrived: Optional[bool] = None
    arrival_date: Optional[date] = None
    visa_type: Optional[VisaType] = None
    visa_validated: Optional[bool] = None
    has_french_address: Optional[bool] = None


class UpdateUniversityProfileRequest(ToolBaseModel):
    student_id: str = "demo_001"
    cvec_status: Optional[BasicStatus] = None
    university_registration_status: Optional[BasicStatus] = None
    has_certificat_scolarite: Optional[bool] = None
    has_student_card: Optional[bool] = None


class UpdateAmeliProfileRequest(ToolBaseModel):
    student_id: str = "demo_001"
    ameli_registered: Optional[bool] = None


class UpdateBankProfileRequest(ToolBaseModel):
    student_id: str = "demo_001"
    has_bank_account: Optional[bool] = None
    has_rib: Optional[bool] = None


class UpdateHousingCafProfileRequest(ToolBaseModel):
    student_id: str = "demo_001"
    housing_status: Optional[HousingStatus] = None
    has_permanent_housing: Optional[bool] = None
    has_rental_contract: Optional[bool] = None
    wants_caf: Optional[bool] = None


class UpdateRenewalProfileRequest(ToolBaseModel):
    student_id: str = "demo_001"
    visa_expiry_date: Optional[date] = None


# ---------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "civicaid-etudiant-backend",
        "version": "0.1.0",
    }


# ---------------------------------------------------------------------
# Helper: apply profile patch
# ---------------------------------------------------------------------

def apply_profile_patch(
    student_id: str,
    patch: StudentProfilePatch,
) -> StudentProfileUpdateResponse:
    existing_profile = get_profile(student_id)

    if existing_profile is None:
        existing_profile = StudentProfile(student_id=student_id)

    patch_data = patch.model_dump(exclude_unset=True)

    # Remove None values so partial tool calls do not erase existing data.
    patch_data = {
        key: value
        for key, value in patch_data.items()
        if value is not None
    }

    if not patch_data:
        return StudentProfileUpdateResponse(
            student_id=student_id,
            status="no_fields_updated",
            profile_completion=existing_profile.profile_completion_score(),
            updated_fields=[],
        )

    current_data = existing_profile.model_dump()
    current_data.update(patch_data)
    current_data["updated_at"] = datetime.utcnow()

    try:
        updated_profile = StudentProfile(**current_data)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid profile update: {str(exc)}",
        ) from exc

    updated_profile.unknown_fields = [
        field_name
        for field_name in updated_profile.required_phase_1_fields()
        if _is_unknown_value(getattr(updated_profile, field_name))
    ]

    save_profile(updated_profile)

    return StudentProfileUpdateResponse(
        student_id=student_id,
        status="updated",
        profile_completion=updated_profile.profile_completion_score(),
        updated_fields=list(patch_data.keys()),
    )


def _is_unknown_value(value) -> bool:
    if value is None:
        return True

    if hasattr(value, "value") and value.value == "unknown":
        return True

    return False


# ---------------------------------------------------------------------
# Tool 1: update_student_profile
# ---------------------------------------------------------------------

@app.post(
    "/tools/update-student-profile",
    response_model=StudentProfileUpdateResponse,
)
def update_student_profile(
    request: StudentProfileUpdateRequest,
    _: None = Depends(verify_tool_token),
) -> StudentProfileUpdateResponse:
    return apply_profile_patch(
        student_id=request.student_id,
        patch=request.patch,
    )


# ---------------------------------------------------------------------
# Mini endpoints for ElevenLabs tools
# ---------------------------------------------------------------------

@app.post(
    "/tools/update-scope-profile",
    response_model=StudentProfileUpdateResponse,
)
def update_scope_profile(
    request: UpdateScopeProfileRequest,
    _: None = Depends(verify_tool_token),
) -> StudentProfileUpdateResponse:
    patch = StudentProfilePatch(
        nationality_category=request.nationality_category,
        country=request.country,
    )
    return apply_profile_patch(request.student_id, patch)


@app.post(
    "/tools/update-arrival-visa-profile",
    response_model=StudentProfileUpdateResponse,
)
def update_arrival_visa_profile(
    request: UpdateArrivalVisaProfileRequest,
    _: None = Depends(verify_tool_token),
) -> StudentProfileUpdateResponse:
    patch = StudentProfilePatch(
        has_arrived=request.has_arrived,
        arrival_date=request.arrival_date,
        visa_type=request.visa_type,
        visa_validated=request.visa_validated,
        has_french_address=request.has_french_address,
    )
    return apply_profile_patch(request.student_id, patch)


@app.post(
    "/tools/update-university-profile",
    response_model=StudentProfileUpdateResponse,
)
def update_university_profile(
    request: UpdateUniversityProfileRequest,
    _: None = Depends(verify_tool_token),
) -> StudentProfileUpdateResponse:
    patch = StudentProfilePatch(
        cvec_status=request.cvec_status,
        university_registration_status=request.university_registration_status,
        has_certificat_scolarite=request.has_certificat_scolarite,
        has_student_card=request.has_student_card,
    )
    return apply_profile_patch(request.student_id, patch)


@app.post(
    "/tools/update-ameli-profile",
    response_model=StudentProfileUpdateResponse,
)
def update_ameli_profile(
    request: UpdateAmeliProfileRequest,
    _: None = Depends(verify_tool_token),
) -> StudentProfileUpdateResponse:
    patch = StudentProfilePatch(
        ameli_registered=request.ameli_registered,
    )
    return apply_profile_patch(request.student_id, patch)


@app.post(
    "/tools/update-bank-profile",
    response_model=StudentProfileUpdateResponse,
)
def update_bank_profile(
    request: UpdateBankProfileRequest,
    _: None = Depends(verify_tool_token),
) -> StudentProfileUpdateResponse:
    patch = StudentProfilePatch(
        has_bank_account=request.has_bank_account,
        has_rib=request.has_rib,
    )
    return apply_profile_patch(request.student_id, patch)


@app.post(
    "/tools/update-housing-caf-profile",
    response_model=StudentProfileUpdateResponse,
)
def update_housing_caf_profile(
    request: UpdateHousingCafProfileRequest,
    _: None = Depends(verify_tool_token),
) -> StudentProfileUpdateResponse:
    patch = StudentProfilePatch(
        housing_status=request.housing_status,
        has_permanent_housing=request.has_permanent_housing,
        has_rental_contract=request.has_rental_contract,
        wants_caf=request.wants_caf,
    )
    return apply_profile_patch(request.student_id, patch)


@app.post(
    "/tools/update-renewal-profile",
    response_model=StudentProfileUpdateResponse,
)
def update_renewal_profile(
    request: UpdateRenewalProfileRequest,
    _: None = Depends(verify_tool_token),
) -> StudentProfileUpdateResponse:
    patch = StudentProfilePatch(
        visa_expiry_date=request.visa_expiry_date,
    )
    return apply_profile_patch(request.student_id, patch)


# ---------------------------------------------------------------------
# Tool 2: generate_arrival_roadmap
# ---------------------------------------------------------------------

@app.post(
    "/tools/generate-arrival-roadmap",
    response_model=GenerateArrivalRoadmapResponse,
)
def generate_arrival_roadmap(
    request: GenerateArrivalRoadmapRequest,
    _: None = Depends(verify_tool_token),
) -> GenerateArrivalRoadmapResponse:
    """
    ElevenLabs calls this near the end of the intake.

    The backend, not the LLM, decides roadmap status, blockers,
    priorities, renewal windows, and next actions.
    """

    profile = get_profile(request.student_id)

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No student profile found for student_id={request.student_id}. "
                "Call update_student_profile first."
            ),
        )

    return generate_arrival_roadmap_response(profile)


# ---------------------------------------------------------------------
# Tool 3: calculate_renewal_window
# ---------------------------------------------------------------------

@app.post(
    "/tools/calculate-renewal-window",
    response_model=RenewalWindowResponse,
)
def calculate_renewal_window_endpoint(
    request: RenewalWindowRequest,
    _: None = Depends(verify_tool_token),
) -> RenewalWindowResponse:
    start, end = calculate_renewal_window(request.visa_expiry_date)

    return RenewalWindowResponse(
        renewal_window_start=start,
        renewal_window_end=end,
    )


# ---------------------------------------------------------------------
# Tool 4: save_call_summary
# ---------------------------------------------------------------------

@app.post(
    "/tools/save-call-summary",
    response_model=SaveCallSummaryResponse,
)
def save_call_summary(
    request: SaveCallSummaryRequest,
    _: None = Depends(verify_tool_token),
) -> SaveCallSummaryResponse:
    """
    Store a short summary for the dashboard.

    Store a short summary in the configured database.
    """

    if not profile_exists(request.student_id):
        raise HTTPException(
            status_code=404,
            detail=f"No student profile found for student_id={request.student_id}.",
        )

    add_call_summary(
        student_id=request.student_id,
        conversation_id=request.conversation_id,
        summary=request.summary,
    )

    return SaveCallSummaryResponse(
        status="saved",
        student_id=request.student_id,
    )


# ---------------------------------------------------------------------
# Debug endpoints for local development only
# ---------------------------------------------------------------------

@app.get(
    "/debug/profile/{student_id}",
    response_model=DebugProfileResponse,
)
def get_debug_profile(
    student_id: str,
    _: None = Depends(verify_tool_token),
) -> DebugProfileResponse:
    profile = get_profile(student_id)

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail=f"No student profile found for student_id={student_id}.",
        )

    return DebugProfileResponse(
        student_id=student_id,
        profile=profile,
    )


@app.get("/debug/call-summaries")
def get_debug_call_summaries(
    _: None = Depends(verify_tool_token),
):
    items = list_call_summaries()
    return {
        "count": len(items),
        "items": items,
    }
