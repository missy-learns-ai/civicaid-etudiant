from datetime import date

from backend.models.student_profile import (
    StudentProfile,
    NationalityCategory,
    VisaType,
    BasicStatus,
    HousingStatus,
)

from backend.models.roadmap import RoadmapStatus, RoadmapStepId

from backend.services.roadmap_engine import generate_arrival_roadmap
from backend.services.deadline_calculator import calculate_renewal_window


def get_step(roadmap, step_id):
    for step in roadmap.steps:
        if step.step_id == step_id:
            return step

    raise AssertionError(f"Step not found: {step_id}")


def test_demo_student_profile_generates_expected_roadmap():
    profile = StudentProfile(
        student_id="demo_001",
        nationality_category=NationalityCategory.NON_EU,
        country="India",
        has_arrived=True,
        arrival_date=date(2026, 9, 10),
        visa_type=VisaType.VLS_TS_STUDENT,
        visa_validated=False,
        visa_expiry_date=date(2027, 9, 9),
        has_french_address=True,
        cvec_status=BasicStatus.NOT_DONE,
        university_registration_status=BasicStatus.IN_PROGRESS,
        has_certificat_scolarite=False,
        has_student_card=False,
        ameli_registered=False,
        has_bank_account=False,
        has_rib=False,
        housing_status=HousingStatus.TEMPORARY,
        has_permanent_housing=False,
        has_rental_contract=False,
        wants_caf=True,
    )

    roadmap = generate_arrival_roadmap(profile)

    vls_step = get_step(roadmap, RoadmapStepId.VLS_TS_VALIDATION)
    assert vls_step.status == RoadmapStatus.URGENT
    assert "visa_not_validated" in vls_step.blocking_items

    university_step = get_step(roadmap, RoadmapStepId.CVEC_UNIVERSITY_REGISTRATION)
    assert university_step.status == RoadmapStatus.BLOCKED
    assert "cvec_attestation_missing" in university_step.blocking_items

    ameli_step = get_step(roadmap, RoadmapStepId.AMELI_REGISTRATION)
    assert ameli_step.status == RoadmapStatus.BLOCKED

    caf_step = get_step(roadmap, RoadmapStepId.CAF_HIGH_LEVEL)
    assert caf_step.status == RoadmapStatus.BLOCKED
    assert "rib_missing" in caf_step.blocking_items
    assert "rental_contract_missing" in caf_step.blocking_items

    renewal_step = get_step(roadmap, RoadmapStepId.RESIDENCE_RENEWAL)
    assert renewal_step.status == RoadmapStatus.FUTURE
    assert renewal_step.renewal_window_start == date(2027, 5, 9)
    assert renewal_step.renewal_window_end == date(2027, 7, 9)

    assert roadmap.top_priority_step_id == RoadmapStepId.VLS_TS_VALIDATION


def test_ameli_ready_when_visa_and_university_are_done():
    profile = StudentProfile(
        student_id="demo_002",
        nationality_category=NationalityCategory.NON_EU,
        country="Morocco",
        has_arrived=True,
        arrival_date=date(2026, 9, 10),
        visa_type=VisaType.VLS_TS_STUDENT,
        visa_validated=True,
        visa_expiry_date=date(2027, 9, 9),
        has_french_address=True,
        cvec_status=BasicStatus.DONE,
        university_registration_status=BasicStatus.DONE,
        has_certificat_scolarite=True,
        has_student_card=True,
        ameli_registered=False,
        has_bank_account=False,
        has_rib=False,
        housing_status=HousingStatus.PERMANENT,
        has_permanent_housing=True,
        has_rental_contract=True,
        wants_caf=True,
    )

    roadmap = generate_arrival_roadmap(profile)
    ameli_step = get_step(roadmap, RoadmapStepId.AMELI_REGISTRATION)

    assert ameli_step.status == RoadmapStatus.READY
    assert ameli_step.blocking_items == []


def test_caf_ready_when_basic_items_exist():
    profile = StudentProfile(
        student_id="demo_003",
        nationality_category=NationalityCategory.NON_EU,
        country="Brazil",
        has_arrived=True,
        arrival_date=date(2026, 9, 10),
        visa_type=VisaType.VLS_TS_STUDENT,
        visa_validated=True,
        visa_expiry_date=date(2027, 9, 9),
        has_french_address=True,
        cvec_status=BasicStatus.DONE,
        university_registration_status=BasicStatus.DONE,
        has_certificat_scolarite=True,
        has_student_card=True,
        ameli_registered=True,
        has_bank_account=True,
        has_rib=True,
        housing_status=HousingStatus.PERMANENT,
        has_permanent_housing=True,
        has_rental_contract=True,
        wants_caf=True,
    )

    roadmap = generate_arrival_roadmap(profile)
    caf_step = get_step(roadmap, RoadmapStepId.CAF_HIGH_LEVEL)

    assert caf_step.status == RoadmapStatus.READY
    assert caf_step.blocking_items == []


def test_renewal_window_calculation():
    start, end = calculate_renewal_window(date(2027, 9, 30))

    assert start == date(2027, 5, 30)
    assert end == date(2027, 7, 30)


def test_non_eu_scope_rule():
    profile = StudentProfile(
        student_id="demo_004",
        nationality_category=NationalityCategory.EU_EEA_SWISS,
        country="Germany",
        has_arrived=True,
        arrival_date=date(2026, 9, 10),
        visa_type=VisaType.UNKNOWN,
        visa_validated=None,
    )

    roadmap = generate_arrival_roadmap(profile)
    vls_step = get_step(roadmap, RoadmapStepId.VLS_TS_VALIDATION)

    assert vls_step.status == RoadmapStatus.NOT_RELEVANT