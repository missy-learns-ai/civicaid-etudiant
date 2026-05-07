import json
import os
import csv
from html import escape
import urllib.error
import urllib.request
from typing import Any

import streamlit as st
import streamlit.components.v1 as components


def get_default_api_base_url() -> str:
    explicit_url = os.getenv("CIVICAID_API_BASE_URL")
    if explicit_url:
        return explicit_url

    render_host = os.getenv("CIVICAID_API_HOST")
    render_port = os.getenv("CIVICAID_API_PORT")
    if render_host and render_port:
        return f"http://{render_host}:{render_port}"

    return "http://127.0.0.1:8000"


DEFAULT_API_BASE_URL = get_default_api_base_url()
DEFAULT_TOOL_TOKEN = os.getenv("CIVICAID_TOOL_TOKEN")
DEFAULT_STUDENT_ID = "demo_001"
DEFAULT_ELEVENLABS_AGENT_ID = os.getenv(
    "ELEVENLABS_AGENT_ID",
    "agent_0301kqspeqntenb8stq8k9nnwc5q",
)
PRODUCT_DESCRIPTION = (
    "CivicAid Étudiant is a voice-guided assistant that helps non-EU students "
    "arriving in France make sense of their administrative journey. Through a "
    "simple conversation, it identifies what applies to each student, highlights "
    "urgent next steps, and turns confusing procedures into a clear, practical "
    "action plan."
)
SOURCE_REGISTRY_PATH = "data/sources/source_registry.csv"

DEMO_PROFILE_PATCH = {
    "name": "Pratistha Thapa",
    "nationality_category": "non_eu",
    "country": "Nepal",
    "has_arrived": True,
    "arrival_date": "2026-09-10",
    "visa_type": "vls_ts_student",
    "visa_validated": False,
    "visa_expiry_date": "2027-09-09",
    "has_french_address": True,
    "cvec_status": "not_done",
    "university_registration_status": "in_progress",
    "has_certificat_scolarite": False,
    "has_student_card": False,
    "ameli_registered": False,
    "has_bank_account": False,
    "has_rib": False,
    "housing_status": "temporary",
    "has_permanent_housing": False,
    "has_rental_contract": False,
    "wants_caf": True,
}

STATUS_META = {
    "urgent": ("Urgent", "#b42318", "#fff1f3"),
    "blocked": ("Blocked", "#b54708", "#fff7ed"),
    "ready": ("Ready", "#047857", "#ecfdf3"),
    "in_progress": ("In progress", "#175cd3", "#eff8ff"),
    "done": ("Done", "#067647", "#ecfdf3"),
    "future": ("Future", "#475467", "#f8fafc"),
    "unknown": ("Unknown", "#6941c6", "#f4f3ff"),
    "not_relevant": ("Not relevant", "#667085", "#f8fafc"),
}

BLOCKER_COPY = {
    "visa_not_validated": (
        "VLS-TS not validated",
        "Validate your student VLS-TS on the official foreigner administration portal.",
    ),
    "french_address_missing": (
        "French address missing",
        "You need a French address before some post-arrival administrative steps can move forward.",
    ),
    "visa_type_unknown_or_not_vls_ts": (
        "Visa type needs confirmation",
        "Check whether your visa is a VLS-TS etudiant or another residence document.",
    ),
    "not_arrived_yet": (
        "Arrival not confirmed",
        "This step becomes active once you have arrived in France.",
    ),
    "visa_validation_status_unknown": (
        "Visa validation status unknown",
        "Confirm whether you received the online VLS-TS validation confirmation.",
    ),
    "cvec_attestation_missing": (
        "CVEC attestation missing",
        "Complete CVEC or retrieve your CVEC attestation before final university registration.",
    ),
    "certificat_scolarite_missing": (
        "Certificate of enrollment missing",
        "Finish university administrative registration and obtain a certificat de scolarite or student card.",
    ),
    "cvec_status_unknown": (
        "CVEC status unknown",
        "Check whether your CVEC is done, exempt, in progress, or still not started.",
    ),
    "university_registration_status_unknown": (
        "University registration status unknown",
        "Confirm whether administrative registration at your institution is complete.",
    ),
    "vls_ts_validation_or_residence_documentation": (
        "Visa or residence proof not ready",
        "Ameli usually needs residence documentation such as VLS-TS validation or an equivalent residence document.",
    ),
    "ameli_readiness_unknown": (
        "Ameli readiness unknown",
        "Confirm whether your visa validation and enrollment proof are ready.",
    ),
    "rib_missing": (
        "RIB missing",
        "Get your French bank account details document before using services that require bank information.",
    ),
    "proof_of_residence_or_enrollment_missing": (
        "Residence or enrollment proof missing",
        "Prepare proof of residence and proof of enrollment before opening a bank account.",
    ),
    "permanent_housing_missing": (
        "Permanent housing missing",
        "Secure longer-term housing before preparing housing-linked steps like CAF.",
    ),
    "rental_contract_missing": (
        "Rental contract missing",
        "Ask your landlord, residence, or housing provider for a rental contract or housing certificate.",
    ),
    "housing_status_unknown": (
        "Housing status unknown",
        "Confirm whether your housing is temporary, permanent, or still being searched for.",
    ),
    "caf_intent_unknown": (
        "CAF intent unknown",
        "Decide whether you want to prepare for CAF housing-aid readiness.",
    ),
    "caf_readiness_unknown": (
        "CAF readiness unknown",
        "Confirm whether you have housing, a rental contract, and a RIB.",
    ),
    "visa_expiry_date_unknown": (
        "Visa expiry date unknown",
        "Check the expiry date on your visa or residence document.",
    ),
}

STEP_COPY = {
    "vls_ts_validation": "VLS-TS validation",
    "cvec_university_registration": "CVEC and university registration",
    "ameli_registration": "Ameli registration",
    "bank_rib": "Bank account and RIB",
    "housing_setup": "Housing setup",
    "caf_high_level": "CAF readiness",
    "residence_renewal": "Residence renewal",
}


def api_url(path: str) -> str:
    return f"{st.session_state.api_base_url.rstrip('/')}{path}"


def api_request(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if DEFAULT_TOOL_TOKEN:
        headers["X-CivicAid-Tool-Token"] = DEFAULT_TOOL_TOKEN

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        api_url(path),
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            detail = json.loads(body)
        except json.JSONDecodeError:
            detail = body
        raise RuntimeError(f"{exc.code} {exc.reason}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Could not reach the FastAPI backend at {st.session_state.api_base_url}."
        ) from exc


def seed_demo_profile(student_id: str) -> dict[str, Any]:
    return api_request(
        "POST",
        "/tools/update-student-profile",
        {
            "student_id": student_id,
            "patch": DEMO_PROFILE_PATCH,
            "source": "streamlit_dashboard",
        },
    )


def fetch_profile(student_id: str) -> dict[str, Any]:
    return api_request("GET", f"/debug/profile/{student_id}")


def generate_roadmap(student_id: str) -> dict[str, Any]:
    return api_request(
        "POST",
        "/tools/generate-arrival-roadmap",
        {"student_id": student_id},
    )


def autoload_profile_and_roadmap(student_id: str) -> None:
    if st.session_state.profile_response is None:
        try:
            st.session_state.profile_response = fetch_profile(student_id)
        except RuntimeError:
            return

    if st.session_state.roadmap_response is None and st.session_state.profile_response:
        try:
            st.session_state.roadmap_response = generate_roadmap(student_id)
        except RuntimeError:
            return


@st.cache_data
def load_source_registry() -> dict[str, dict[str, str]]:
    sources: dict[str, dict[str, str]] = {}
    try:
        with open(SOURCE_REGISTRY_PATH, newline="", encoding="utf-8") as source_file:
            for row in csv.DictReader(source_file):
                sources[row["source_id"]] = row
    except FileNotFoundError:
        return {}
    return sources


def status_label(status: str) -> str:
    return STATUS_META.get(status, (status.replace("_", " ").title(), "#344054", "#f9fafb"))[0]


def humanize_field_name(value: str) -> str:
    if value in STEP_COPY:
        return STEP_COPY[value]
    return value.replace("_", " ").replace("vls ts", "VLS-TS").replace("rib", "RIB").title()


def humanize_value(value: Any) -> str:
    if value is True:
        return "Yes"
    if value is False:
        return "No"
    if value is None:
        return "Unknown"
    if isinstance(value, str):
        normalized = value.replace("_", " ")
        replacements = {
            "non eu": "Non-EU",
            "eu eea swiss": "EU / EEA / Swiss",
            "vls ts student": "VLS-TS student",
            "not done": "Not done",
            "in progress": "In progress",
            "temporary": "Temporary",
            "permanent": "Permanent",
            "searching": "Searching",
        }
        return replacements.get(normalized, normalized.capitalize())
    return str(value)


def blocker_copy(blocker: str) -> tuple[str, str]:
    return BLOCKER_COPY.get(
        blocker,
        (humanize_field_name(blocker), "Review this item before continuing."),
    )


def render_status_badge(status: str) -> None:
    label, color, background = STATUS_META.get(
        status,
        (status.replace("_", " ").title(), "#344054", "#f9fafb"),
    )
    st.markdown(
        f"""
        <span class="status-badge" style="color:{color}; background:{background}; border-color:{color}22;">
            {label}
        </span>
        """,
        unsafe_allow_html=True,
    )


def render_card_grid(cards: list[tuple[str, str, str]], height: int = 130) -> None:
    card_markup = "".join(
        f'<div class="summary-card {accent}">'
        f"<span>{escape(label)}</span>"
        f"<strong>{escape(value)}</strong>"
        "</div>"
        for label, value, accent in cards
    )
    components.html(
        f"""
        <style>
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat({len(cards)}, minmax(0, 1fr));
            gap: 14px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }}
        .summary-card {{
            background: #ffffff;
            border: 1px solid #d0d5dd;
            border-radius: 8px;
            border-top-width: 5px;
            min-height: 104px;
            padding: 16px;
            box-sizing: border-box;
        }}
        .summary-card.blue {{ border-top-color: #002395; }}
        .summary-card.red {{ border-top-color: #ED2939; }}
        .summary-card.neutral {{ border-top-color: #98a2b3; }}
        .summary-card span {{
            color: #667085;
            display: block;
            font-size: 12px;
            font-weight: 800;
            text-transform: uppercase;
            margin-bottom: 10px;
        }}
        .summary-card strong {{
            color: #101828;
            display: block;
            font-size: 18px;
            line-height: 1.25;
            font-weight: 850;
        }}
        @media (max-width: 900px) {{
            .summary-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
        }}
        @media (max-width: 640px) {{
            .summary-grid {{ grid-template-columns: 1fr; }}
        }}
        </style>
        <div class="summary-grid">{card_markup}</div>
        """,
        height=height,
    )


def render_progress(profile: dict[str, Any] | None, roadmap: dict[str, Any] | None) -> None:
    completion = 0
    if profile:
        tracked_fields = [field for field in DEMO_PROFILE_PATCH if field != "name"]
        completed = [
            field
            for field in tracked_fields
            if profile.get(field) not in (None, "unknown")
        ]
        completion = round((len(completed) / len(tracked_fields)) * 100)

    steps = roadmap.get("steps", []) if roadmap else []
    urgent_or_blocked = len(
        [step for step in steps if step.get("status") in {"urgent", "blocked"}]
    )
    ready_or_done = len(
        [step for step in steps if step.get("status") in {"ready", "done", "in_progress"}]
    )

    render_card_grid(
        [
            ("Profile completion", f"{completion}%", "blue"),
            ("Roadmap steps", str(len(steps)) if steps else "Not generated", "neutral"),
            ("Needs attention", str(urgent_or_blocked), "red"),
            ("Ready / moving", str(ready_or_done), "blue"),
        ],
        height=130,
    )


def render_priority_panel(response: dict[str, Any] | None) -> None:
    if not response:
        st.markdown(
            """
            <div class="priority-panel empty">
                <span>Next best action</span>
                <strong>Seed the demo profile, then generate the roadmap.</strong>
                <p>The dashboard will show the student's highest-priority administrative step here.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    roadmap = response.get("roadmap", {})
    top_priority_id = roadmap.get("top_priority_step_id")
    steps = roadmap.get("steps", [])
    top_step = next((step for step in steps if step.get("step_id") == top_priority_id), None)

    if not top_step:
        st.info("No top priority is available yet.")
        return

    label, color, background = STATUS_META.get(
        top_step.get("status", "unknown"),
        ("Unknown", "#344054", "#f9fafb"),
    )
    st.markdown(
        f"""
        <div class="priority-panel" style="border-color:{color}33; background:{background};">
            <span>Next best action</span>
            <strong>{escape(top_step.get("title", "Review roadmap"))}</strong>
            <em style="color:{color};">{label}</em>
            <p>{escape(top_step.get("next_action", ""))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_profile(profile: dict[str, Any]) -> None:
    core_fields = [
        ("Student name", profile.get("name")),
        ("Nationality", profile.get("nationality_category")),
        ("Country", profile.get("country")),
        ("Arrived", profile.get("has_arrived")),
        ("Arrival date", profile.get("arrival_date")),
        ("Visa type", profile.get("visa_type")),
        ("Visa validated", profile.get("visa_validated")),
        ("Visa expiry", profile.get("visa_expiry_date")),
        ("French address", profile.get("has_french_address")),
    ]

    admin_fields = [
        ("CVEC", profile.get("cvec_status")),
        ("University registration", profile.get("university_registration_status")),
        ("Certificat de scolarite", profile.get("has_certificat_scolarite")),
        ("Student card", profile.get("has_student_card")),
        ("Ameli", profile.get("ameli_registered")),
        ("Bank account", profile.get("has_bank_account")),
        ("RIB", profile.get("has_rib")),
        ("Housing", profile.get("housing_status")),
        ("Permanent housing", profile.get("has_permanent_housing")),
        ("Rental contract", profile.get("has_rental_contract")),
        ("Wants CAF", profile.get("wants_caf")),
    ]

    def profile_section(title: str, fields: list[tuple[str, Any]], accent: str) -> str:
        items = ""
        for label, value in fields:
            display_value = value if label == "Student name" and isinstance(value, str) else humanize_value(value)
            items += (
                '<div class="profile-field">'
                f"<span>{escape(label)}</span>"
                f"<strong>{escape(display_value)}</strong>"
                "</div>"
            )
        return (
            f'<section class="profile-panel {accent}">'
            f"<h3>{escape(title)}</h3>"
            f'<div class="profile-grid">{items}</div>'
            "</section>"
        )

    st.markdown(profile_section("Identity & Visa", core_fields, "blue"), unsafe_allow_html=True)
    st.markdown(profile_section("Admin readiness", admin_fields, "red"), unsafe_allow_html=True)

    unknown_fields = profile.get("unknown_fields") or []
    if unknown_fields:
        st.warning("Unknown fields: " + ", ".join(humanize_field_name(field) for field in unknown_fields))


def render_roadmap_summary(response: dict[str, Any]) -> None:
    roadmap = response.get("roadmap", {})

    render_card_grid(
        [
            ("Roadmap status", humanize_value(response.get("roadmap_status", "unknown")), "blue"),
            ("Overall state", status_label(roadmap.get("overall_status", "unknown")), "red"),
            ("Top priority", response.get("top_priority") or "None", "blue"),
        ],
        height=130,
    )

    st.info(response.get("voice_summary") or roadmap.get("summary") or "Roadmap generated.")

    unknowns = roadmap.get("unknowns_to_resolve") or []
    if unknowns:
        st.warning("Still unknown: " + ", ".join(humanize_field_name(field) for field in unknowns))


def source_items_for_step(step: dict[str, Any]) -> list[dict[str, str]]:
    source_registry = load_source_registry()
    sources = step.get("sources") or []
    source_ids = step.get("source_ids") or []

    return sources or [
        source_registry.get(source_id, {"source_id": source_id, "title": source_id})
        for source_id in source_ids
    ]


def render_step_card(step: dict[str, Any]) -> None:
    status = step.get("status", "unknown")
    status_text, status_color, status_background = STATUS_META.get(
        status,
        (humanize_value(status), "#344054", "#f8fafc"),
    )
    accent = "red" if status in {"urgent", "blocked"} else "blue"
    blockers = step.get("blocking_items") or []
    dependencies = step.get("dependencies") or []
    source_items = source_items_for_step(step)

    blockers_html = ""
    if blockers:
        blocker_rows = ""
        for blocker in blockers:
            title, description = blocker_copy(blocker)
            blocker_rows += (
                '<div class="blocker-row">'
                f"<strong>{escape(title)}</strong>"
                f"<span>{escape(description)}</span>"
                "</div>"
            )
        blockers_html = f'<div class="step-section"><h4>Blockers</h4>{blocker_rows}</div>'

    dependencies_html = ""
    if dependencies:
        dependencies_html = (
            '<div class="step-meta">'
            f"<span>Depends on</span><strong>{escape(', '.join(humanize_field_name(item) for item in dependencies))}</strong>"
            "</div>"
        )

    renewal_start = step.get("renewal_window_start")
    renewal_end = step.get("renewal_window_end")
    renewal_html = ""
    if renewal_start and renewal_end:
        renewal_html = (
            '<div class="step-meta">'
            f"<span>Renewal window</span><strong>{escape(renewal_start)} to {escape(renewal_end)}</strong>"
            "</div>"
        )

    sources_html = ""
    if source_items:
        source_links = ""
        for source in source_items:
            title = source.get("title") or source.get("source_id") or "Source"
            publisher = source.get("publisher")
            url = source.get("url")
            label = f"{title} ({publisher})" if publisher else title
            if url:
                source_links += (
                    f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">'
                    f"{escape(label)}</a>"
                )
            else:
                source_links += f"<span>{escape(label)}</span>"
        sources_html = f'<div class="source-links">{source_links}</div>'

    step_html = (
        f'<article class="roadmap-card {accent}">'
        '<div class="roadmap-card-header">'
        "<div>"
        f'<span class="step-number">Step {escape(str(step.get("priority", "")))}</span>'
        f'<h3>{escape(step.get("title", "Roadmap step"))}</h3>'
        "</div>"
        f'<span class="status-badge" style="color:{status_color}; background:{status_background}; border-color:{status_color}22;">'
        f"{escape(status_text)}</span>"
        "</div>"
        f'<p class="step-explanation">{escape(step.get("explanation", ""))}</p>'
        '<div class="next-action-card">'
        "<span>Next action</span>"
        f'<strong>{escape(step.get("next_action", "No next action available."))}</strong>'
        "</div>"
        f"{blockers_html}"
        f'<div class="step-meta-grid">{dependencies_html}{renewal_html}</div>'
        f"{sources_html}"
        "</article>"
    )
    st.markdown(step_html, unsafe_allow_html=True)


def render_roadmap_steps(response: dict[str, Any]) -> None:
    steps = response.get("roadmap", {}).get("steps", [])
    if not steps:
        st.info("No roadmap steps are available yet.")
        return

    st.caption("Each step includes the status, blockers, next action, dependencies, renewal timing when relevant, and official sources.")

    for step in steps:
        render_step_card(step)


def render_voice_widget() -> None:
    agent_id = st.session_state.get("elevenlabs_agent_id", "").strip()
    dynamic_variables = {
        "student_id": st.session_state.get("student_id", DEFAULT_STUDENT_ID),
        "api_base_url": st.session_state.get("api_base_url", DEFAULT_API_BASE_URL),
        "product_context": "CivicAid Étudiant student dashboard",
    }

    if agent_id:
        widget_html = f"""
        <style>
        body {{
            margin: 0;
            background: #ffffff;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }}
        .voice-frame {{
            border: 1px solid transparent;
            border-radius: 8px;
            background: #ffffff;
            height: 214px;
            max-width: 560px;
            margin: 0 auto;
            box-sizing: border-box;
            padding: 10px 18px;
            position: relative;
            overflow: hidden;
        }}
        .voice-title {{
            color: #101828;
            font-size: 22px;
            font-weight: 850;
            letter-spacing: 0;
            line-height: 1.1;
            margin: 0;
            text-align: center;
        }}
        .widget-slot {{
            bottom: 0;
            left: 0;
            right: 0;
            min-height: 148px;
            position: absolute;
            z-index: 1;
            display: flex;
            align-items: flex-end;
            justify-content: center;
        }}
        </style>
        <div class="voice-frame">
            <h2 class="voice-title">Tell us where you are</h2>
            <div class="widget-slot">
                <elevenlabs-convai
                    agent-id="{escape(agent_id, quote=True)}"
                    dynamic-variables='{escape(json.dumps(dynamic_variables), quote=True)}'
                    override-first-message="Hi, I am CivicAid Étudiant. I can help organize your student administrative steps in France. Are you ready to begin?"
                ></elevenlabs-convai>
            </div>
            <script
                src="https://unpkg.com/@elevenlabs/convai-widget-embed"
                async
                type="text/javascript"
            ></script>
        </div>
        """
        components.html(widget_html, height=224)
        return

    st.markdown(
        """
        <div class="voice-placeholder">
            <div class="voice-mark">
                <span></span>
                <span></span>
                <span></span>
            </div>
            <div>
                <strong>Voice session unavailable</strong>
                <p>The assistant will appear here when the voice agent is configured.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --text: #182230;
            --muted: #667085;
            --line: #eaecf0;
            --panel: #ffffff;
            --soft: #f8fafc;
            --ink: #101828;
            --blue: #002395;
            --red: #ED2939;
            --pale-blue: #eef4ff;
            --pale-red: #fff1f3;
            --font-sans: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        html, body, [class*="css"], .stApp {
            font-family: var(--font-sans);
        }

        button, input, textarea, select {
            font-family: var(--font-sans);
        }

        .main .block-container {
            padding-top: 1.4rem;
            max-width: 1240px;
        }

        h1, h2, h3 {
            color: var(--text);
            font-family: var(--font-sans);
            letter-spacing: 0;
        }

        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 14px 16px;
        }

        div[data-testid="stMetric"] label {
            color: var(--muted);
        }

        .hero-shell {
            border: 1px solid #d0d5dd;
            border-radius: 8px;
            background: #ffffff;
            padding: 24px;
            margin-bottom: 18px;
            position: relative;
            overflow: hidden;
        }

        .hero-shell::before {
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 8px;
            background: var(--blue);
        }

        .hero-shell::after {
            content: "";
            position: absolute;
            inset: 0 0 0 auto;
            width: 8px;
            background: var(--red);
        }

        .hero-kicker {
            color: var(--blue);
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0;
            margin-bottom: 6px;
        }

        .hero-title {
            color: var(--ink);
            font-size: 2.35rem;
            line-height: 1.05;
            font-weight: 900;
            margin: 0 0 10px;
        }

        .hero-title .blue-word {
            color: var(--blue);
        }

        .hero-title .red-word {
            color: var(--red);
        }

        .hero-copy {
            color: #344054;
            max-width: 880px;
            margin: 0;
            font-size: 1rem;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 14px;
            margin: 0 0 16px;
        }

        .summary-card {
            background: #ffffff;
            border: 1px solid #d0d5dd;
            border-radius: 8px;
            padding: 16px;
            min-height: 104px;
            border-top-width: 5px;
        }

        .summary-card.blue {
            border-top-color: var(--blue);
        }

        .summary-card.red {
            border-top-color: var(--red);
        }

        .summary-card span {
            color: var(--muted);
            display: block;
            font-size: 0.78rem;
            font-weight: 800;
            text-transform: uppercase;
            margin-bottom: 10px;
        }

        .summary-card strong {
            color: var(--ink);
            display: block;
            font-size: 1.15rem;
            line-height: 1.25;
            font-weight: 850;
        }

        .profile-panel {
            background: #ffffff;
            border: 1px solid #d0d5dd;
            border-radius: 8px;
            border-top-width: 5px;
            padding: 20px;
            margin-bottom: 18px;
            box-shadow: 0 12px 30px rgba(16, 24, 40, 0.04);
        }

        .profile-panel.blue {
            border-top-color: var(--blue);
        }

        .profile-panel.red {
            border-top-color: var(--red);
        }

        .profile-panel h3 {
            margin: 0 0 14px;
            font-size: 1.22rem;
            font-weight: 850;
        }

        .profile-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
        }

        .profile-field {
            border: 1px solid #e4e7ec;
            border-radius: 8px;
            padding: 14px;
            background: #ffffff;
            min-height: 74px;
        }

        .profile-field span {
            color: var(--muted);
            display: block;
            font-size: 0.76rem;
            font-weight: 800;
            text-transform: uppercase;
            margin-bottom: 8px;
        }

        .profile-field strong {
            color: var(--ink);
            display: block;
            font-size: 1rem;
            line-height: 1.2;
        }

        .roadmap-card {
            background: #ffffff;
            border: 1px solid #d0d5dd;
            border-top-width: 5px;
            border-radius: 8px;
            padding: 20px;
            margin: 0 0 18px;
            box-shadow: 0 12px 30px rgba(16, 24, 40, 0.04);
        }

        .roadmap-card.blue {
            border-top-color: var(--blue);
        }

        .roadmap-card.red {
            border-top-color: var(--red);
        }

        .roadmap-card-header {
            display: grid;
            grid-template-columns: minmax(0, 1fr) minmax(120px, 180px);
            gap: 14px;
            align-items: start;
        }

        .roadmap-card h3 {
            color: var(--ink);
            margin: 4px 0 0;
            font-size: 1.28rem;
            line-height: 1.2;
            font-weight: 850;
        }

        .step-number {
            color: var(--muted);
            display: block;
            font-size: 0.76rem;
            font-weight: 800;
            text-transform: uppercase;
        }

        .step-explanation {
            color: #344054;
            margin: 14px 0;
        }

        .next-action-card {
            border: 1px solid #b2ddff;
            border-radius: 8px;
            background: #eff8ff;
            padding: 12px;
            margin: 12px 0;
        }

        .next-action-card span,
        .step-section h4,
        .step-meta span {
            color: var(--muted);
            display: block;
            font-size: 0.76rem;
            font-weight: 800;
            text-transform: uppercase;
            margin: 0 0 6px;
        }

        .next-action-card strong {
            color: #101828;
            display: block;
            font-size: 1rem;
            line-height: 1.35;
        }

        .step-section {
            margin-top: 14px;
        }

        .step-meta-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 12px;
            margin-top: 12px;
        }

        .step-meta {
            border: 1px solid #eaecf0;
            border-radius: 8px;
            padding: 10px 12px;
            background: #fcfcfd;
        }

        .step-meta strong {
            color: #101828;
            display: block;
            font-size: 0.95rem;
        }

        .source-links {
            border-top: 1px solid #eaecf0;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 14px;
            padding-top: 14px;
        }

        .source-links a,
        .source-links span {
            border: 1px solid #d0d5dd;
            border-radius: 999px;
            color: var(--blue);
            display: inline-flex;
            font-size: 0.84rem;
            font-weight: 700;
            line-height: 1.2;
            padding: 7px 10px;
            text-decoration: none;
        }

        .priority-panel {
            border: 1px solid #d0d5dd;
            border-radius: 8px;
            padding: 18px;
            min-height: 214px;
            box-sizing: border-box;
        }

        .priority-panel.empty {
            background: #f8fafc;
        }

        .priority-panel span {
            color: var(--muted);
            display: block;
            font-size: 0.82rem;
            font-weight: 700;
            margin-bottom: 8px;
            text-transform: uppercase;
        }

        .priority-panel strong {
            color: var(--ink);
            display: block;
            font-size: 1.35rem;
            line-height: 1.2;
            margin-bottom: 8px;
        }

        .priority-panel em {
            display: inline-block;
            font-style: normal;
            font-weight: 800;
            margin-bottom: 10px;
        }

        .priority-panel p {
            color: #344054;
            margin: 0;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 32px;
            width: 100%;
            border: 1px solid;
            border-radius: 999px;
            font-weight: 700;
            font-size: 0.86rem;
            white-space: nowrap;
        }

        .blocker-row {
            border: 1px solid #fedf89;
            background: #fffbeb;
            border-radius: 8px;
            padding: 10px 12px;
            margin: 8px 0;
        }

        .blocker-row strong {
            display: block;
            color: #93370d;
            margin-bottom: 2px;
        }

        .blocker-row span {
            color: #475467;
            display: block;
            font-size: 0.92rem;
        }

        .voice-placeholder {
            min-height: 236px;
            border: 1px dashed #9db4f3;
            border-radius: 8px;
            background: #ffffff;
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 20px;
            color: var(--text);
        }

        .voice-placeholder p {
            margin: 6px 0 0;
            color: var(--muted);
        }

        .voice-mark {
            width: 58px;
            height: 58px;
            border-radius: 50%;
            background: var(--blue);
            box-shadow: 0 0 0 8px #e0e8ff, 0 0 0 14px #fff1f3;
            flex: 0 0 auto;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 4px;
        }

        .voice-mark span {
            width: 5px;
            border-radius: 999px;
            background: white;
            display: block;
        }

        .voice-mark span:nth-child(1) {
            height: 18px;
        }

        .voice-mark span:nth-child(2) {
            height: 30px;
        }

        .voice-mark span:nth-child(3) {
            height: 22px;
        }

        .voice-frame {
            min-height: 224px;
            border: 1px solid transparent;
            border-radius: 8px;
            background: #ffffff;
            padding: 0;
        }

        div[data-testid="stTabs"] {
            margin-top: 6px;
        }

        div[data-testid="stTabs"] [role="tablist"] {
            background: #f8fafc;
            border: 1px solid #e4e7ec;
            border-radius: 8px;
            display: inline-flex;
            gap: 4px;
            padding: 5px;
        }

        div[data-testid="stTabs"] [role="tab"] {
            border-radius: 6px;
            min-height: 38px;
            padding: 0 16px;
        }

        div[data-testid="stTabs"] [role="tab"] p {
            color: #475467;
            font-size: 0.92rem;
            font-weight: 800;
            margin: 0;
        }

        div[data-testid="stTabs"] [aria-selected="true"] {
            background: #ffffff;
            border: 1px solid #d0d5dd;
            box-shadow: 0 6px 16px rgba(16, 24, 40, 0.06);
        }

        div[data-testid="stTabs"] [aria-selected="true"] p {
            color: var(--blue);
        }

        div[data-testid="stTabs"] [data-testid="stTabContent"] {
            background: #ffffff;
            border: 1px solid #eaecf0;
            border-radius: 8px;
            margin-top: 14px;
            padding: 18px;
        }

        @media (max-width: 760px) {
            .summary-grid {
                grid-template-columns: 1fr;
            }

            .profile-grid,
            .step-meta-grid,
            .roadmap-card-header {
                grid-template-columns: 1fr;
            }

            .hero-title {
                font-size: 1.85rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="CivicAid Étudiant",
        page_icon="",
        layout="wide",
    )
    apply_styles()

    st.session_state.setdefault("api_base_url", DEFAULT_API_BASE_URL)
    st.session_state.setdefault("student_id", DEFAULT_STUDENT_ID)
    st.session_state.setdefault("elevenlabs_agent_id", DEFAULT_ELEVENLABS_AGENT_ID)
    st.session_state.setdefault("profile_response", None)
    st.session_state.setdefault("roadmap_response", None)

    with st.sidebar:
        st.title("CivicAid Étudiant")
        with st.expander("Developer settings"):
            st.session_state.api_base_url = st.text_input(
                "FastAPI backend URL",
                value=st.session_state.api_base_url,
            )
            st.session_state.student_id = st.text_input(
                "Student profile id",
                value=st.session_state.student_id,
            )
            st.session_state.elevenlabs_agent_id = st.text_input(
                "ElevenLabs agent ID",
                value=st.session_state.elevenlabs_agent_id,
                placeholder="agent_...",
            )

        st.divider()

        if st.button("Seed demo profile", use_container_width=True):
            try:
                seed_demo_profile(st.session_state.student_id)
                st.session_state.profile_response = fetch_profile(st.session_state.student_id)
                st.session_state.roadmap_response = None
                st.toast("Demo profile seeded.")
            except RuntimeError as exc:
                st.error(str(exc))

        if st.button("Refresh profile", use_container_width=True):
            try:
                st.session_state.profile_response = fetch_profile(st.session_state.student_id)
            except RuntimeError as exc:
                st.error(str(exc))

        if st.button("Generate roadmap", type="primary", use_container_width=True):
            try:
                st.session_state.roadmap_response = generate_roadmap(st.session_state.student_id)
            except RuntimeError as exc:
                st.error(str(exc))

        st.caption("After a voice session, refresh the profile and generate the roadmap.")

    autoload_profile_and_roadmap(st.session_state.student_id)

    profile_response = st.session_state.profile_response
    roadmap_response = st.session_state.roadmap_response
    profile = profile_response.get("profile", {}) if profile_response else None
    roadmap = roadmap_response.get("roadmap", {}) if roadmap_response else None

    st.markdown(
        f"""
        <div class="hero-shell">
            <div class="hero-kicker">CivicAid Étudiant</div>
            <div class="hero-title">
                <span class="blue-word">Personalized roadmap</span> for non-EU students arriving in <span class="red-word">France</span>
            </div>
            <p class="hero-copy">
                {escape(PRODUCT_DESCRIPTION)}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_progress(profile, roadmap)

    top_left, top_right = st.columns([0.58, 0.42], gap="large")
    with top_left:
        render_voice_widget()

    with top_right:
        render_priority_panel(roadmap_response)

    st.divider()

    profile_tab, roadmap_tab = st.tabs(["Student profile", "Roadmap"])

    with profile_tab:
        if profile_response:
            render_profile(profile_response.get("profile", {}))
        else:
            st.info("Seed or refresh a student profile to view structured fields.")

    with roadmap_tab:
        if roadmap_response:
            render_roadmap_summary(roadmap_response)
            st.subheader("Interactive roadmap")
            render_roadmap_steps(roadmap_response)
        else:
            st.info("Generate a roadmap to display cards, blockers, and next actions.")


if __name__ == "__main__":
    main()
