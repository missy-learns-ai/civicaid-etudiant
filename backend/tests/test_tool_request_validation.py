from datetime import date

from backend.models.roadmap import (
    GenerateArrivalRoadmapRequest,
    RenewalWindowRequest,
)
from backend.models.student_profile import (
    BasicStatus,
    NationalityCategory,
    StudentProfileUpdateRequest,
    VisaType,
)


def test_update_student_profile_accepts_flat_tool_payload():
    request = StudentProfileUpdateRequest.model_validate(
        {
            "nationality_category": "non_eu",
            "country": "India",
            "has_arrived": True,
            "arrival_date": "2026-09-10",
            "visa_type": "vls_ts_student",
            "visa_validated": False,
            "tool_call_id": "ignored_metadata",
        }
    )

    assert request.student_id == "demo_001"
    assert request.patch.nationality_category == NationalityCategory.NON_EU
    assert request.patch.country == "India"
    assert request.patch.arrival_date == date(2026, 9, 10)
    assert request.patch.visa_type == VisaType.VLS_TS_STUDENT
    assert request.patch.visa_validated is False


def test_update_student_profile_ignores_extra_fields_inside_patch():
    request = StudentProfileUpdateRequest.model_validate(
        {
            "student_id": "demo_002",
            "patch": {
                "visa_type": "vls_ts_student",
                "unused_tool_note": "ignored",
            },
        }
    )

    assert request.student_id == "demo_002"
    assert request.patch.visa_type == VisaType.VLS_TS_STUDENT


def test_update_student_profile_converts_empty_optional_strings():
    request = StudentProfileUpdateRequest.model_validate(
        {
            "student_id": "demo_003",
            "patch": {
                "country": "",
            },
        }
    )

    assert request.patch.country is None


def test_tool_enums_accept_common_swagger_variants():
    request = StudentProfileUpdateRequest.model_validate(
        {
            "nationality_category": "NON_EU",
            "visa_type": "VLS-TS-STUDENT",
            "cvec_status": "In Progress",
        }
    )

    assert request.patch.nationality_category == NationalityCategory.NON_EU
    assert request.patch.visa_type == VisaType.VLS_TS_STUDENT
    assert request.patch.cvec_status == BasicStatus.IN_PROGRESS


def test_generate_roadmap_defaults_demo_student_and_ignores_metadata():
    request = GenerateArrivalRoadmapRequest.model_validate(
        {
            "conversation_id": "ignored_metadata",
        }
    )

    assert request.student_id == "demo_001"


def test_renewal_window_ignores_metadata():
    request = RenewalWindowRequest.model_validate(
        {
            "visa_expiry_date": "2027-09-09",
            "tool_call_id": "ignored_metadata",
        }
    )

    assert request.visa_expiry_date == date(2027, 9, 9)
