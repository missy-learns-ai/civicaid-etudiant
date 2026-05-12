from backend import storage
from backend.app import (
    SaveCallSummaryRequest,
    UpdateAmeliProfileRequest,
    UpdateArrivalVisaProfileRequest,
    UpdateBankProfileRequest,
    UpdateHousingCafProfileRequest,
    UpdateRenewalProfileRequest,
    UpdateScopeProfileRequest,
    UpdateUniversityProfileRequest,
    generate_arrival_roadmap,
    save_call_summary,
    update_ameli_profile,
    update_arrival_visa_profile,
    update_bank_profile,
    update_housing_caf_profile,
    update_renewal_profile,
    update_scope_profile,
    update_university_profile,
)
from backend.models.roadmap import GenerateArrivalRoadmapRequest, RoadmapScope, RoadmapStepId


def test_all_profile_update_tools_persist_and_generate_roadmap(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_URL", f"sqlite:///{tmp_path / 'tools.db'}")
    storage.init_db()

    student_id = "tool_test_001"

    tool_results = [
        update_scope_profile(
            UpdateScopeProfileRequest(
                student_id=student_id,
                nationality_category="non_eu",
                country="Nepal",
            )
        ),
        update_arrival_visa_profile(
            UpdateArrivalVisaProfileRequest(
                student_id=student_id,
                has_arrived=True,
                arrival_date="2025-10-25",
                visa_type="vls_ts_student",
                visa_validated=False,
                has_french_address=True,
            )
        ),
        update_university_profile(
            UpdateUniversityProfileRequest(
                student_id=student_id,
                cvec_status="not_done",
                university_registration_status="in_progress",
                has_certificat_scolarite=False,
                has_student_card=False,
            )
        ),
        update_ameli_profile(
            UpdateAmeliProfileRequest(
                student_id=student_id,
                ameli_registered=False,
            )
        ),
        update_bank_profile(
            UpdateBankProfileRequest(
                student_id=student_id,
                has_bank_account=False,
                has_rib=False,
            )
        ),
        update_housing_caf_profile(
            UpdateHousingCafProfileRequest(
                student_id=student_id,
                housing_status="temporary",
                has_permanent_housing=False,
                has_rental_contract=False,
                wants_caf=True,
            )
        ),
        update_renewal_profile(
            UpdateRenewalProfileRequest(
                student_id=student_id,
                visa_expiry_date="2027-09-09",
            )
        ),
    ]

    assert all(result.status == "updated" for result in tool_results)
    assert tool_results[-1].profile_completion == 1.0

    profile = storage.get_profile(student_id)
    assert profile is not None
    assert profile.country == "Nepal"
    assert profile.profile_completion_score() == 1.0

    roadmap_response = generate_arrival_roadmap(
        GenerateArrivalRoadmapRequest(student_id=student_id)
    )
    assert roadmap_response.roadmap_status == "generated"
    assert len(roadmap_response.roadmap.steps) == 7

    caf_response = generate_arrival_roadmap(
        GenerateArrivalRoadmapRequest(
            student_id=student_id,
            roadmap_scope=RoadmapScope.CAF,
        )
    )
    caf_step_ids = [step.step_id for step in caf_response.roadmap.steps]
    bank_step = next(
        step
        for step in caf_response.roadmap.steps
        if step.step_id == RoadmapStepId.BANK_RIB
    )

    assert RoadmapStepId.RESIDENCE_RENEWAL not in caf_step_ids
    assert bank_step.guidance_cards
    assert bank_step.guidance_cards[0].source_url == "https://www.campusfrance.org/en/organise-arrival-France"

    summary_response = save_call_summary(
        SaveCallSummaryRequest(
            student_id=student_id,
            summary="Non-sensitive tool endpoint smoke test summary.",
        )
    )
    assert summary_response.status == "saved"
    assert storage.list_call_summaries()[0]["student_id"] == student_id
