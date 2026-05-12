from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

from backend.models.student_profile import (
    ConfidenceLevel,
    NormalizedStrEnum,
    ToolRequestModel,
)


class RoadmapStatus(NormalizedStrEnum):
    DONE = "done"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    URGENT = "urgent"
    FUTURE = "future"
    NOT_RELEVANT = "not_relevant"
    UNKNOWN = "unknown"


class RoadmapStepId(NormalizedStrEnum):
    VLS_TS_VALIDATION = "vls_ts_validation"
    CVEC_UNIVERSITY_REGISTRATION = "cvec_university_registration"
    AMELI_REGISTRATION = "ameli_registration"
    BANK_RIB = "bank_rib"
    HOUSING_SETUP = "housing_setup"
    CAF_HIGH_LEVEL = "caf_high_level"
    RESIDENCE_RENEWAL = "residence_renewal"


class RoadmapScope(NormalizedStrEnum):
    FULL = "full"
    CAF = "caf"


class SourceReference(BaseModel):
    """
    Reference to an official source from source_registry.csv.
    """

    model_config = ConfigDict(extra="forbid")

    source_id: str
    title: Optional[str] = None
    publisher: Optional[str] = None
    url: Optional[str] = None


class RoadmapStep(BaseModel):
    """
    One step in the student's arrival roadmap.
    """

    model_config = ConfigDict(extra="forbid")

    step_id: RoadmapStepId
    title: str
    status: RoadmapStatus
    priority: int = Field(
        ...,
        description="Lower number means higher priority.",
    )

    explanation: str
    next_action: str

    blocking_items: List[str] = Field(default_factory=list)
    dependencies: List[RoadmapStepId] = Field(default_factory=list)

    due_date: Optional[date] = None
    renewal_window_start: Optional[date] = None
    renewal_window_end: Optional[date] = None

    source_ids: List[str] = Field(default_factory=list)
    sources: List[SourceReference] = Field(default_factory=list)

    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class ArrivalRoadmap(BaseModel):
    """
    Full roadmap generated after the intake conversation.
    """

    model_config = ConfigDict(extra="forbid")

    roadmap_id: str
    student_id: str
    scope: RoadmapScope = RoadmapScope.FULL
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    title: str = "Your Non-EU Student Arrival Roadmap"
    summary: str

    steps: List[RoadmapStep]

    top_priority_step_id: Optional[RoadmapStepId] = None
    overall_status: RoadmapStatus = RoadmapStatus.IN_PROGRESS

    unknowns_to_resolve: List[str] = Field(default_factory=list)
    safety_disclaimer: str = (
        "This roadmap helps you organize your administrative steps. "
        "It does not submit official applications, replace official portals, "
        "or guarantee eligibility, legal status, or approval."
    )


class GenerateArrivalRoadmapRequest(ToolRequestModel):
    """
    Request body for:
    POST /tools/generate-arrival-roadmap
    """

    student_id: str = "demo_001"
    roadmap_scope: RoadmapScope = RoadmapScope.FULL


class GenerateArrivalRoadmapResponse(BaseModel):
    """
    Response returned to ElevenLabs after roadmap generation.
    """

    roadmap_status: str
    student_id: str
    top_priority: Optional[str] = None
    voice_summary: str
    roadmap: ArrivalRoadmap


class RenewalWindowRequest(ToolRequestModel):
    """
    Request body for:
    POST /tools/calculate-renewal-window
    """

    visa_expiry_date: date


class RenewalWindowResponse(BaseModel):
    renewal_window_start: date
    renewal_window_end: date
