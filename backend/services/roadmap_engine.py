from uuid import uuid4

from backend.models.student_profile import (
    StudentProfile,
    NationalityCategory,
    VisaType,
    BasicStatus,
    HousingStatus,
    ConfidenceLevel,
)

from backend.models.roadmap import (
    ArrivalRoadmap,
    RoadmapStep,
    RoadmapStatus,
    RoadmapStepId,
    RoadmapScope,
    GenerateArrivalRoadmapResponse,
)

from backend.services.deadline_calculator import calculate_renewal_window
from backend.storage import get_guidance_cards


def _has_university_proof(profile: StudentProfile) -> bool:
    return bool(profile.has_certificat_scolarite or profile.has_student_card)


def _is_done_status(status: BasicStatus) -> bool:
    return status in {BasicStatus.DONE, BasicStatus.EXEMPT}


def _make_step(
    step_id: RoadmapStepId,
    title: str,
    status: RoadmapStatus,
    priority: int,
    explanation: str,
    next_action: str,
    blocking_items: list[str] | None = None,
    dependencies: list[RoadmapStepId] | None = None,
    source_ids: list[str] | None = None,
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
    renewal_window_start=None,
    renewal_window_end=None,
) -> RoadmapStep:
    return RoadmapStep(
        step_id=step_id,
        title=title,
        status=status,
        priority=priority,
        explanation=explanation,
        next_action=next_action,
        blocking_items=blocking_items or [],
        dependencies=dependencies or [],
        source_ids=source_ids or [],
        confidence=confidence,
        renewal_window_start=renewal_window_start,
        renewal_window_end=renewal_window_end,
    )


def build_vls_ts_step(profile: StudentProfile) -> RoadmapStep:
    if profile.nationality_category != NationalityCategory.NON_EU:
        return _make_step(
            step_id=RoadmapStepId.VLS_TS_VALIDATION,
            title="Validate VLS-TS",
            status=RoadmapStatus.NOT_RELEVANT,
            priority=99,
            explanation="This Phase 1 roadmap is designed for non-EU students.",
            next_action="Use this version only if you are a non-EU student arriving in France.",
            source_ids=[],
            confidence=ConfidenceLevel.HIGH,
        )

    if profile.visa_type != VisaType.VLS_TS_STUDENT:
        return _make_step(
            step_id=RoadmapStepId.VLS_TS_VALIDATION,
            title="Validate VLS-TS",
            status=RoadmapStatus.UNKNOWN,
            priority=1,
            explanation="Your visa type is not confirmed as VLS-TS étudiant.",
            next_action="Check your visa type. This roadmap is optimized for students with a VLS-TS étudiant.",
            blocking_items=["visa_type_unknown_or_not_vls_ts"],
            source_ids=["campus_france_vls_ts", "service_public_f2231"],
            confidence=ConfidenceLevel.LOW,
        )

    if profile.has_arrived is False:
        return _make_step(
            step_id=RoadmapStepId.VLS_TS_VALIDATION,
            title="Validate VLS-TS",
            status=RoadmapStatus.FUTURE,
            priority=1,
            explanation="You have not arrived in France yet, so VLS-TS validation is a future post-arrival step.",
            next_action="Prepare your visa details, future arrival date, French address, email, and payment method or electronic stamp.",
            blocking_items=["not_arrived_yet"],
            source_ids=["campus_france_vls_ts"],
            confidence=ConfidenceLevel.HIGH,
        )

    if profile.visa_validated is True:
        return _make_step(
            step_id=RoadmapStepId.VLS_TS_VALIDATION,
            title="Validate VLS-TS",
            status=RoadmapStatus.DONE,
            priority=99,
            explanation="You said your VLS-TS is already validated.",
            next_action="Keep your validation confirmation available for future administrative steps.",
            source_ids=["campus_france_vls_ts"],
            confidence=ConfidenceLevel.MEDIUM,
        )

    if profile.visa_validated is False:
        blockers = ["visa_not_validated"]

        if profile.has_french_address is False:
            blockers.append("french_address_missing")

        return _make_step(
            step_id=RoadmapStepId.VLS_TS_VALIDATION,
            title="Validate VLS-TS",
            status=RoadmapStatus.URGENT,
            priority=1,
            explanation="You arrived in France with a VLS-TS and have not validated it yet.",
            next_action="Validate your VLS-TS on the official foreigner administration portal.",
            blocking_items=blockers,
            source_ids=["campus_france_vls_ts", "service_public_f2231"],
            confidence=ConfidenceLevel.HIGH,
        )

    return _make_step(
        step_id=RoadmapStepId.VLS_TS_VALIDATION,
        title="Validate VLS-TS",
        status=RoadmapStatus.UNKNOWN,
        priority=1,
        explanation="It is not clear whether your VLS-TS has been validated.",
        next_action="Check whether you received a confirmation after validating your VLS-TS online.",
        blocking_items=["visa_validation_status_unknown"],
        source_ids=["campus_france_vls_ts"],
        confidence=ConfidenceLevel.MEDIUM,
    )


def build_university_step(profile: StudentProfile) -> RoadmapStep:
    if _has_university_proof(profile):
        return _make_step(
            step_id=RoadmapStepId.CVEC_UNIVERSITY_REGISTRATION,
            title="Complete CVEC and university registration",
            status=RoadmapStatus.DONE,
            priority=99,
            explanation="You have a certificat de scolarité or student card, so your university registration appears complete for Phase 1 purposes.",
            next_action="Keep your certificat de scolarité or student card available for Ameli, banking, housing, and future administrative steps.",
            source_ids=["etudiant_gouv_cvec"],
            confidence=ConfidenceLevel.MEDIUM,
        )

    if profile.cvec_status == BasicStatus.NOT_DONE:
        return _make_step(
            step_id=RoadmapStepId.CVEC_UNIVERSITY_REGISTRATION,
            title="Complete CVEC and university registration",
            status=RoadmapStatus.BLOCKED,
            priority=2,
            explanation="Your university registration appears blocked or incomplete because CVEC is not done.",
            next_action="Complete CVEC or obtain your CVEC attestation, then finish administrative registration at your institution.",
            blocking_items=["cvec_attestation_missing", "certificat_scolarite_missing"],
            source_ids=["etudiant_gouv_cvec"],
            confidence=ConfidenceLevel.MEDIUM,
        )

    if _is_done_status(profile.cvec_status):
        return _make_step(
            step_id=RoadmapStepId.CVEC_UNIVERSITY_REGISTRATION,
            title="Complete CVEC and university registration",
            status=RoadmapStatus.IN_PROGRESS,
            priority=2,
            explanation="Your CVEC appears done or exempt, but you do not yet have a certificat de scolarité or student card.",
            next_action="Finish administrative registration with your institution and obtain your certificat de scolarité or student card.",
            blocking_items=["certificat_scolarite_missing"],
            source_ids=["etudiant_gouv_cvec"],
            confidence=ConfidenceLevel.MEDIUM,
        )

    return _make_step(
        step_id=RoadmapStepId.CVEC_UNIVERSITY_REGISTRATION,
        title="Complete CVEC and university registration",
        status=RoadmapStatus.UNKNOWN,
        priority=2,
        explanation="It is not clear whether your CVEC and university registration are complete.",
        next_action="Check whether you have your CVEC attestation and certificat de scolarité.",
        blocking_items=["cvec_status_unknown", "university_registration_status_unknown"],
        source_ids=["etudiant_gouv_cvec"],
        confidence=ConfidenceLevel.LOW,
    )


def build_ameli_step(profile: StudentProfile) -> RoadmapStep:
    if profile.ameli_registered is True:
        return _make_step(
            step_id=RoadmapStepId.AMELI_REGISTRATION,
            title="Register for Ameli health insurance",
            status=RoadmapStatus.DONE,
            priority=99,
            explanation="You said you have already registered for French health insurance.",
            next_action="Keep your provisional or final certificate available and follow future steps for your Vitale card if applicable.",
            source_ids=["ameli_foreign_students"],
            confidence=ConfidenceLevel.MEDIUM,
        )

    blockers = []

    if profile.visa_validated is False:
        blockers.append("vls_ts_validation_or_residence_documentation")

    if not _has_university_proof(profile):
        blockers.append("certificat_scolarite_missing")

    if blockers:
        return _make_step(
            step_id=RoadmapStepId.AMELI_REGISTRATION,
            title="Register for Ameli health insurance",
            status=RoadmapStatus.BLOCKED,
            priority=3,
            explanation="Ameli registration appears blocked because earlier administrative documents are not ready yet.",
            next_action="After validating your VLS-TS and obtaining your certificat de scolarité or student card, register through the dedicated Ameli foreign-student portal.",
            blocking_items=blockers,
            dependencies=[
                RoadmapStepId.VLS_TS_VALIDATION,
                RoadmapStepId.CVEC_UNIVERSITY_REGISTRATION,
            ],
            source_ids=["ameli_foreign_students", "campus_france_arrival"],
            confidence=ConfidenceLevel.MEDIUM,
        )

    if profile.visa_validated is True and _has_university_proof(profile):
        return _make_step(
            step_id=RoadmapStepId.AMELI_REGISTRATION,
            title="Register for Ameli health insurance",
            status=RoadmapStatus.READY,
            priority=3,
            explanation="Your visa validation and university registration evidence appear ready.",
            next_action="Register through the dedicated Ameli foreign-student portal.",
            dependencies=[
                RoadmapStepId.VLS_TS_VALIDATION,
                RoadmapStepId.CVEC_UNIVERSITY_REGISTRATION,
            ],
            source_ids=["ameli_foreign_students", "campus_france_arrival"],
            confidence=ConfidenceLevel.MEDIUM,
        )

    return _make_step(
        step_id=RoadmapStepId.AMELI_REGISTRATION,
        title="Register for Ameli health insurance",
        status=RoadmapStatus.UNKNOWN,
        priority=3,
        explanation="It is not clear whether you are ready to register for Ameli.",
        next_action="Confirm whether your VLS-TS is validated and whether you have a certificat de scolarité or student card.",
        blocking_items=["ameli_readiness_unknown"],
        source_ids=["ameli_foreign_students"],
        confidence=ConfidenceLevel.LOW,
    )


def build_bank_rib_step(profile: StudentProfile) -> RoadmapStep:
    if profile.has_bank_account is True and profile.has_rib is True:
        return _make_step(
            step_id=RoadmapStepId.BANK_RIB,
            title="Open bank account and get RIB",
            status=RoadmapStatus.DONE,
            priority=99,
            explanation="You already have a bank account and RIB.",
            next_action="Keep your RIB available for reimbursements, rent, CAF, and other payments.",
            source_ids=["campus_france_bank"],
            confidence=ConfidenceLevel.MEDIUM,
        )

    if profile.has_bank_account is True and profile.has_rib is False:
        return _make_step(
            step_id=RoadmapStepId.BANK_RIB,
            title="Open bank account and get RIB",
            status=RoadmapStatus.IN_PROGRESS,
            priority=4,
            explanation="You have a bank account but do not have your RIB yet.",
            next_action="Ask your bank or check your banking app for your RIB. Do not share your IBAN with this assistant.",
            blocking_items=["rib_missing"],
            source_ids=["campus_france_bank"],
            confidence=ConfidenceLevel.MEDIUM,
        )

    if profile.has_french_address is True and _has_university_proof(profile):
        return _make_step(
            step_id=RoadmapStepId.BANK_RIB,
            title="Open bank account and get RIB",
            status=RoadmapStatus.READY,
            priority=4,
            explanation="You appear to have the basic documents often needed to open a bank account.",
            next_action="Prepare identification, proof of residence, and your certificat de scolarité or student card to open a bank account.",
            dependencies=[RoadmapStepId.CVEC_UNIVERSITY_REGISTRATION],
            source_ids=["campus_france_bank"],
            confidence=ConfidenceLevel.MEDIUM,
        )

    return _make_step(
        step_id=RoadmapStepId.BANK_RIB,
        title="Open bank account and get RIB",
        status=RoadmapStatus.BLOCKED,
        priority=4,
        explanation="Opening a bank account may be harder until you have proof of residence and enrollment evidence.",
        next_action="Prepare identification, proof of residence, and proof of enrollment or student card. If you lack permanent housing, ask your institution whether its international office address can be used temporarily.",
        blocking_items=["proof_of_residence_or_enrollment_missing"],
        dependencies=[RoadmapStepId.CVEC_UNIVERSITY_REGISTRATION],
        source_ids=["campus_france_bank"],
        confidence=ConfidenceLevel.LOW,
    )


def build_housing_step(profile: StudentProfile) -> RoadmapStep:
    if profile.has_permanent_housing is True and profile.has_rental_contract is True:
        return _make_step(
            step_id=RoadmapStepId.HOUSING_SETUP,
            title="Secure permanent housing",
            status=RoadmapStatus.DONE,
            priority=99,
            explanation="You said you have permanent housing and a rental contract.",
            next_action="Keep your rental contract or housing certificate available for future administrative steps.",
            source_ids=["caf_student_housing"],
            confidence=ConfidenceLevel.MEDIUM,
        )

    if profile.has_permanent_housing is True and profile.has_rental_contract is False:
        return _make_step(
            step_id=RoadmapStepId.HOUSING_SETUP,
            title="Secure permanent housing",
            status=RoadmapStatus.IN_PROGRESS,
            priority=5,
            explanation="You have permanent housing but do not yet have a rental contract or housing certificate.",
            next_action="Ask your landlord, residence, or housing provider for a rental contract or housing certificate.",
            blocking_items=["rental_contract_missing"],
            source_ids=["caf_student_housing"],
            confidence=ConfidenceLevel.MEDIUM,
        )

    if profile.has_permanent_housing is False or profile.housing_status in {
        HousingStatus.TEMPORARY,
        HousingStatus.SEARCHING,
    }:
        return _make_step(
            step_id=RoadmapStepId.HOUSING_SETUP,
            title="Secure permanent housing",
            status=RoadmapStatus.BLOCKED,
            priority=5,
            explanation="You do not appear to have permanent housing yet, which can block later steps such as CAF preparation.",
            next_action="Secure longer-term housing and keep your rental contract or housing certificate.",
            blocking_items=["permanent_housing_missing"],
            source_ids=["caf_student_housing"],
            confidence=ConfidenceLevel.MEDIUM,
        )

    return _make_step(
        step_id=RoadmapStepId.HOUSING_SETUP,
        title="Secure permanent housing",
        status=RoadmapStatus.UNKNOWN,
        priority=5,
        explanation="It is not clear whether you have permanent housing or a rental contract.",
        next_action="Confirm whether you have long-term accommodation and a rental contract or housing certificate.",
        blocking_items=["housing_status_unknown"],
        source_ids=["caf_student_housing"],
        confidence=ConfidenceLevel.LOW,
    )


def build_caf_step(profile: StudentProfile) -> RoadmapStep:
    if profile.wants_caf is False:
        return _make_step(
            step_id=RoadmapStepId.CAF_HIGH_LEVEL,
            title="Prepare CAF housing aid",
            status=RoadmapStatus.NOT_RELEVANT,
            priority=99,
            explanation="You said you do not want CAF guidance right now.",
            next_action="You can revisit CAF housing aid later if you want to check whether it is relevant.",
            source_ids=["caf_student_housing"],
            confidence=ConfidenceLevel.MEDIUM,
        )

    if profile.wants_caf is None:
        return _make_step(
            step_id=RoadmapStepId.CAF_HIGH_LEVEL,
            title="Prepare CAF housing aid",
            status=RoadmapStatus.UNKNOWN,
            priority=6,
            explanation="It is not clear whether you want to prepare for CAF housing aid.",
            next_action="Decide whether you want to check CAF housing-aid readiness.",
            blocking_items=["caf_intent_unknown"],
            source_ids=["caf_student_housing"],
            confidence=ConfidenceLevel.LOW,
        )

    blockers = []

    if profile.has_permanent_housing is False:
        blockers.append("permanent_housing_missing")

    if profile.has_rental_contract is False:
        blockers.append("rental_contract_missing")

    if profile.has_rib is False:
        blockers.append("rib_missing")

    if blockers:
        return _make_step(
            step_id=RoadmapStepId.CAF_HIGH_LEVEL,
            title="Prepare CAF housing aid",
            status=RoadmapStatus.BLOCKED,
            priority=6,
            explanation="CAF preparation appears blocked because one or more basic items are missing.",
            next_action="Before deep CAF preparation, make sure you have housing, a rental contract or housing certificate, and a RIB.",
            blocking_items=blockers,
            dependencies=[
                RoadmapStepId.BANK_RIB,
                RoadmapStepId.HOUSING_SETUP,
            ],
            source_ids=["caf_student_housing"],
            confidence=ConfidenceLevel.HIGH,
        )

    if (
        profile.wants_caf is True
        and profile.has_permanent_housing is True
        and profile.has_rental_contract is True
        and profile.has_rib is True
    ):
        return _make_step(
            step_id=RoadmapStepId.CAF_HIGH_LEVEL,
            title="Prepare CAF housing aid",
            status=RoadmapStatus.READY,
            priority=6,
            explanation="You appear to have the basic items needed for deeper CAF readiness.",
            next_action="Proceed to a deeper CAF readiness check in Phase 2.",
            dependencies=[
                RoadmapStepId.BANK_RIB,
                RoadmapStepId.HOUSING_SETUP,
            ],
            source_ids=["caf_student_housing"],
            confidence=ConfidenceLevel.MEDIUM,
        )

    return _make_step(
        step_id=RoadmapStepId.CAF_HIGH_LEVEL,
        title="Prepare CAF housing aid",
        status=RoadmapStatus.UNKNOWN,
        priority=6,
        explanation="CAF readiness could not be determined from the available information.",
        next_action="Confirm whether you have housing, a rental contract, and a RIB.",
        blocking_items=["caf_readiness_unknown"],
        source_ids=["caf_student_housing"],
        confidence=ConfidenceLevel.LOW,
    )


def build_residence_renewal_step(profile: StudentProfile) -> RoadmapStep:
    if profile.visa_expiry_date:
        start, end = calculate_renewal_window(profile.visa_expiry_date)

        return _make_step(
            step_id=RoadmapStepId.RESIDENCE_RENEWAL,
            title="Track residence renewal",
            status=RoadmapStatus.FUTURE,
            priority=7,
            explanation="Your visa expiry date is known, so this can be tracked as a future reminder.",
            next_action="Track your renewal window from 4 months before expiry to 2 months before expiry.",
            renewal_window_start=start,
            renewal_window_end=end,
            source_ids=["service_public_f2231"],
            confidence=ConfidenceLevel.HIGH,
        )

    return _make_step(
        step_id=RoadmapStepId.RESIDENCE_RENEWAL,
        title="Track residence renewal",
        status=RoadmapStatus.UNKNOWN,
        priority=7,
        explanation="Your visa expiry date is not known, so the renewal reminder cannot be calculated yet.",
        next_action="Check the expiry date on your visa or residence document.",
        blocking_items=["visa_expiry_date_unknown"],
        source_ids=["service_public_f2231"],
        confidence=ConfidenceLevel.MEDIUM,
    )


def sort_steps(steps: list[RoadmapStep]) -> list[RoadmapStep]:
    return sorted(steps, key=lambda step: step.priority)


def attach_guidance_cards(
    steps: list[RoadmapStep],
    scope: RoadmapScope,
) -> list[RoadmapStep]:
    for step in steps:
        step.guidance_cards = get_guidance_cards(
            step_id=step.step_id.value,
            blocker_keys=step.blocking_items,
            scope=scope.value,
        )

    return steps


def scope_steps(steps: list[RoadmapStep], scope: RoadmapScope) -> list[RoadmapStep]:
    if scope == RoadmapScope.FULL:
        return steps

    if scope == RoadmapScope.CAF:
        step_by_id = {step.step_id: step for step in steps}
        scoped_ids = [
            RoadmapStepId.VLS_TS_VALIDATION,
            RoadmapStepId.AMELI_REGISTRATION,
            RoadmapStepId.BANK_RIB,
            RoadmapStepId.HOUSING_SETUP,
            RoadmapStepId.CAF_HIGH_LEVEL,
        ]
        scoped_steps = [
            step_by_id[step_id]
            for step_id in scoped_ids
            if step_id in step_by_id
        ]

        ameli_step = step_by_id.get(RoadmapStepId.AMELI_REGISTRATION)
        university_step = step_by_id.get(RoadmapStepId.CVEC_UNIVERSITY_REGISTRATION)
        if (
            ameli_step
            and university_step
            and "certificat_scolarite_missing" in ameli_step.blocking_items
        ):
            scoped_steps.insert(1, university_step)

        return scoped_steps

    return steps


def determine_top_priority(steps: list[RoadmapStep]) -> RoadmapStepId | None:
    actionable_statuses = {
        RoadmapStatus.URGENT,
        RoadmapStatus.BLOCKED,
        RoadmapStatus.READY,
        RoadmapStatus.IN_PROGRESS,
        RoadmapStatus.UNKNOWN,
        RoadmapStatus.FUTURE,
    }

    actionable_steps = [
        step for step in sort_steps(steps)
        if step.status in actionable_statuses
    ]

    if not actionable_steps:
        return None

    return actionable_steps[0].step_id


def determine_overall_status(steps: list[RoadmapStep]) -> RoadmapStatus:
    statuses = {step.status for step in steps}

    if RoadmapStatus.URGENT in statuses:
        return RoadmapStatus.URGENT

    if RoadmapStatus.BLOCKED in statuses:
        return RoadmapStatus.BLOCKED

    if RoadmapStatus.IN_PROGRESS in statuses:
        return RoadmapStatus.IN_PROGRESS

    if RoadmapStatus.READY in statuses:
        return RoadmapStatus.READY

    return RoadmapStatus.UNKNOWN


def collect_unknowns(profile: StudentProfile, scope: RoadmapScope) -> list[str]:
    unknowns = []

    if scope == RoadmapScope.CAF:
        field_names = [
            "nationality_category",
            "country",
            "visa_validated",
            "ameli_registered",
            "has_bank_account",
            "has_rib",
            "housing_status",
            "has_permanent_housing",
            "has_rental_contract",
            "wants_caf",
        ]
    else:
        field_names = profile.required_phase_1_fields()

    for field_name in field_names:
        value = getattr(profile, field_name)

        if value is None:
            unknowns.append(field_name)
            continue

        if hasattr(value, "value") and value.value == "unknown":
            unknowns.append(field_name)

    return unknowns


def build_summary(steps: list[RoadmapStep], scope: RoadmapScope) -> str:
    urgent_steps = [step for step in steps if step.status == RoadmapStatus.URGENT]
    blocked_steps = [step for step in steps if step.status == RoadmapStatus.BLOCKED]
    ready_steps = [step for step in steps if step.status == RoadmapStatus.READY]

    if scope == RoadmapScope.CAF:
        if blocked_steps:
            return (
                f"Your CAF roadmap has {len(blocked_steps)} blocked prerequisite(s). "
                f"Start with: {blocked_steps[0].title}."
            )

        if ready_steps:
            return "Your CAF prerequisites look ready. Review the CAF step and verify details on official websites."

        return "Your CAF-focused roadmap has been generated. Review each prerequisite before applying."

    if urgent_steps:
        return (
            f"Your top priority is: {urgent_steps[0].title}. "
            f"You also have {len(blocked_steps)} blocked step(s) to resolve."
        )

    if blocked_steps:
        return (
            f"You have {len(blocked_steps)} blocked step(s). "
            f"Start with: {blocked_steps[0].title}."
        )

    if ready_steps:
        return (
            f"You have {len(ready_steps)} step(s) ready to complete. "
            f"Start with: {ready_steps[0].title}."
        )

    return "Your roadmap has been generated. Review each step and verify important information on official websites."


def generate_arrival_roadmap(
    profile: StudentProfile,
    scope: RoadmapScope = RoadmapScope.FULL,
) -> ArrivalRoadmap:
    steps = [
        build_vls_ts_step(profile),
        build_university_step(profile),
        build_ameli_step(profile),
        build_bank_rib_step(profile),
        build_housing_step(profile),
        build_caf_step(profile),
        build_residence_renewal_step(profile),
    ]

    steps = attach_guidance_cards(sort_steps(scope_steps(steps, scope)), scope)
    summary = build_summary(steps, scope)
    title = "Your Non-EU Student Arrival Roadmap"
    if scope == RoadmapScope.CAF:
        title = "Your CAF Housing Aid Roadmap"

    return ArrivalRoadmap(
        roadmap_id=f"roadmap_{profile.student_id}_{uuid4().hex[:8]}",
        student_id=profile.student_id,
        scope=scope,
        title=title,
        summary=summary,
        steps=steps,
        top_priority_step_id=determine_top_priority(steps),
        overall_status=determine_overall_status(steps),
        unknowns_to_resolve=collect_unknowns(profile, scope),
    )


def generate_arrival_roadmap_response(
    profile: StudentProfile,
    scope: RoadmapScope = RoadmapScope.FULL,
) -> GenerateArrivalRoadmapResponse:
    roadmap = generate_arrival_roadmap(profile, scope)

    top_priority = None
    if roadmap.top_priority_step_id:
        for step in roadmap.steps:
            if step.step_id == roadmap.top_priority_step_id:
                top_priority = step.title
                break

    return GenerateArrivalRoadmapResponse(
        roadmap_status="generated",
        student_id=profile.student_id,
        top_priority=top_priority,
        voice_summary=roadmap.summary,
        roadmap=roadmap,
    )
