from datetime import date, datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class NormalizedStrEnum(str, Enum):
    @classmethod
    def _missing_(cls, value):
        if not isinstance(value, str):
            return None

        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")

        for member in cls:
            if normalized in (member.name.lower(), member.value):
                return member

        return None


class NationalityCategory(NormalizedStrEnum):
    NON_EU = "non_eu"
    EU_EEA_SWISS = "eu_eea_swiss"
    FRENCH = "french"
    UNKNOWN = "unknown"


class VisaType(NormalizedStrEnum):
    VLS_TS_STUDENT = "vls_ts_student"
    STUDENT_RESIDENCE_PERMIT = "student_residence_permit"
    SHORT_STAY_VISA = "short_stay_visa"
    OTHER = "other"
    UNKNOWN = "unknown"


class BasicStatus(NormalizedStrEnum):
    DONE = "done"
    NOT_DONE = "not_done"
    IN_PROGRESS = "in_progress"
    EXEMPT = "exempt"
    UNKNOWN = "unknown"


class HousingStatus(NormalizedStrEnum):
    PERMANENT = "permanent"
    TEMPORARY = "temporary"
    SEARCHING = "searching"
    UNKNOWN = "unknown"


class ConfidenceLevel(NormalizedStrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ToolRequestModel(BaseModel):
    """
    Base model for payloads sent by external tool callers.

    Tool platforms can include extra metadata, omit demo defaults, or send
    empty strings for unknown optional values. Keep that tolerance at the API
    edge while the core stored models remain strict.
    """

    model_config = ConfigDict(extra="ignore")

    @field_validator("*", mode="before")
    @classmethod
    def empty_string_to_none(cls, value):
        if value == "":
            return None
        return value


class StudentProfile(BaseModel):
    """
    Core profile collected from the ElevenLabs voice intake.

    Important:
    - Do not store passport number.
    - Do not store visa number.
    - Do not store full address.
    - Do not store IBAN.
    - Do not store uploaded documents.
    """

    model_config = ConfigDict(extra="forbid")

    student_id: str = Field(
        ...,
        description="Internal demo/user identifier. Do not use government IDs.",
    )
    name: Optional[str] = Field(
        default=None,
        description="Student display name for the dashboard. Do not use government IDs.",
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Scope
    nationality_category: NationalityCategory = Field(default=NationalityCategory.UNKNOWN)
    country: Optional[str] = Field(
        default=None,
        description="Country of origin, e.g. India, Morocco, Brazil.",
    )

    # Arrival and visa
    has_arrived: Optional[bool] = Field(default=None)
    arrival_date: Optional[date] = Field(default=None)
    visa_type: VisaType = Field(default=VisaType.UNKNOWN)
    visa_validated: Optional[bool] = Field(default=None)
    visa_expiry_date: Optional[date] = Field(default=None)
    has_french_address: Optional[bool] = Field(
        default=None,
        description="Only stores whether the student has an address, not the address itself.",
    )

    # University / CVEC
    cvec_status: BasicStatus = Field(default=BasicStatus.UNKNOWN)
    university_registration_status: BasicStatus = Field(default=BasicStatus.UNKNOWN)
    has_certificat_scolarite: Optional[bool] = Field(default=None)
    has_student_card: Optional[bool] = Field(default=None)

    # Health insurance
    ameli_registered: Optional[bool] = Field(default=None)

    # Bank / RIB
    has_bank_account: Optional[bool] = Field(default=None)
    has_rib: Optional[bool] = Field(
        default=None,
        description="Only stores whether the student has a RIB, not the IBAN.",
    )

    # Housing
    housing_status: HousingStatus = Field(default=HousingStatus.UNKNOWN)
    has_permanent_housing: Optional[bool] = Field(default=None)
    has_rental_contract: Optional[bool] = Field(default=None)

    # CAF high-level intent
    wants_caf: Optional[bool] = Field(default=None)

    # Roadmap presentation intent
    preferred_roadmap_scope: Optional[str] = Field(
        default=None,
        description="Last roadmap scope requested by the agent, such as 'caf' or 'full'.",
    )

    # Intake quality
    profile_confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM)
    unknown_fields: List[str] = Field(default_factory=list)

    def required_phase_1_fields(self) -> List[str]:
        return [
            "nationality_category",
            "has_arrived",
            "arrival_date",
            "visa_type",
            "visa_validated",
            "has_french_address",
            "cvec_status",
            "university_registration_status",
            "has_certificat_scolarite",
            "ameli_registered",
            "has_bank_account",
            "has_rib",
            "has_permanent_housing",
            "has_rental_contract",
            "wants_caf",
            "visa_expiry_date",
        ]

    def profile_completion_score(self) -> float:
        """
        Returns a completion score from 0.0 to 1.0 based on Phase 1 fields.
        """
        fields = self.required_phase_1_fields()
        completed = 0

        for field_name in fields:
            value = getattr(self, field_name)

            if value is None:
                continue

            if isinstance(value, Enum) and value.value == "unknown":
                continue

            completed += 1

        return round(completed / len(fields), 2)


class StudentProfilePatch(ToolRequestModel):
    """
    Partial profile update sent by ElevenLabs tool calls.

    Use this when the agent learns new facts during the conversation.
    """

    nationality_category: Optional[NationalityCategory] = None
    name: Optional[str] = None
    country: Optional[str] = None

    has_arrived: Optional[bool] = None
    arrival_date: Optional[date] = None
    visa_type: Optional[VisaType] = None
    visa_validated: Optional[bool] = None
    visa_expiry_date: Optional[date] = None
    has_french_address: Optional[bool] = None

    cvec_status: Optional[BasicStatus] = None
    university_registration_status: Optional[BasicStatus] = None
    has_certificat_scolarite: Optional[bool] = None
    has_student_card: Optional[bool] = None

    ameli_registered: Optional[bool] = None

    has_bank_account: Optional[bool] = None
    has_rib: Optional[bool] = None

    housing_status: Optional[HousingStatus] = None
    has_permanent_housing: Optional[bool] = None
    has_rental_contract: Optional[bool] = None

    wants_caf: Optional[bool] = None
    preferred_roadmap_scope: Optional[str] = None

    profile_confidence: Optional[ConfidenceLevel] = None
    unknown_fields: Optional[List[str]] = None


class StudentProfileUpdateRequest(ToolRequestModel):
    """
    Request body for the backend tool:
    POST /tools/update-student-profile
    """

    student_id: str = "demo_001"
    patch: StudentProfilePatch = Field(default_factory=StudentProfilePatch)
    source: str = Field(
        default="elevenlabs_agent",
        description="Where this update came from.",
    )

    @model_validator(mode="before")
    @classmethod
    def accept_flat_patch_fields(cls, data):
        if not isinstance(data, dict):
            return data

        normalized = dict(data)

        if "patch" in normalized and normalized["patch"] in ("", None):
            normalized["patch"] = {}

        if "patch" in normalized:
            return normalized

        patch_fields = set(StudentProfilePatch.model_fields)
        patch_data = {
            key: normalized.pop(key)
            for key in list(normalized)
            if key in patch_fields
        }

        if patch_data:
            normalized["patch"] = patch_data

        return normalized


class StudentProfileUpdateResponse(BaseModel):
    """
    Response returned to ElevenLabs after profile update.
    Keep this short because the agent may use it during voice conversation.
    """

    student_id: str
    status: str
    profile_completion: float
    updated_fields: List[str]
