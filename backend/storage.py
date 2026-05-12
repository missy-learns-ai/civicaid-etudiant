import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

from backend.models.roadmap import GuidanceCard
from backend.models.student_profile import StudentProfile


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/civicaid.db")


CAMPUS_FRANCE_BANK_URL = "https://www.campusfrance.org/en/getting-a-bank-account"
CAF_STUDENT_HOUSING_AID_URL = (
    "https://www.caf.fr/allocataires/actualites/actualites-nationales/"
    "etudiants-tout-savoir-sur-l-aide-au-logement-0"
)
AMELI_FOREIGN_STUDENTS_URL = (
    "https://www.ameli.fr/assure/droits-demarches/etudes-stages/etudiant/"
    "french-social-security-registration-process-foreign-students"
)
SERVICE_PUBLIC_VLS_TS_VALIDATION_URL = "https://www.service-public.gouv.fr/particuliers/vosdroits/R52684"

GUIDANCE_CARD_SEEDS = [
    {
        "id": "bank_account_missing_campus_france",
        "step_id": "bank_rib",
        "blocker_key": "bank_account_missing",
        "scope": "caf",
        "title": "Prepare for a French bank appointment",
        "why_it_matters": (
            "A French bank account and RIB are often needed for rent, subscriptions, "
            "health reimbursements, wages, and CAF-related payments."
        ),
        "documents": [
            "Passport or identity document",
            "Proof of residence",
            "Certificate of enrolment or student card",
        ],
        "suggested_actions": [
            "Ask your university international office whether it has partner banks or onboarding days.",
            "Prepare the required documents before booking or visiting a bank branch.",
            "If you do not yet have accommodation, ask your institution whether its address can be used temporarily.",
            "Compare account fees before choosing a bank.",
            "If a bank refuses to open an account, check the Banque de France right-to-account process.",
        ],
        "source_title": "Campus France - Getting a bank account",
        "source_url": CAMPUS_FRANCE_BANK_URL,
        "priority": 10,
        "locale": "en",
        "active": True,
    },
    {
        "id": "rib_missing_campus_france",
        "step_id": "bank_rib",
        "blocker_key": "rib_missing",
        "scope": "caf",
        "title": "Get your RIB before starting CAF paperwork",
        "why_it_matters": (
            "CAF and many other French services use a RIB to send payments or reimbursements."
        ),
        "documents": [],
        "suggested_actions": [
            "Check your banking app or online account for a downloadable RIB.",
            "Ask your bank branch for a RIB if it is not visible online.",
            "Do not share your IBAN or full bank details with this assistant.",
        ],
        "source_title": "Campus France - Getting a bank account",
        "source_url": CAMPUS_FRANCE_BANK_URL,
        "priority": 20,
        "locale": "en",
        "active": True,
    },
    {
        "id": "caf_prerequisites_campus_france",
        "step_id": "caf_high_level",
        "blocker_key": "rib_missing",
        "scope": "caf",
        "title": "Remove the payment blocker before CAF",
        "why_it_matters": (
            "A RIB helps CAF identify where housing-aid payments should be sent if your file is accepted."
        ),
        "documents": ["RIB from a French or compatible bank account"],
        "suggested_actions": [
            "Finish the bank/RIB step before spending time on the CAF form.",
            "Keep a digital copy of your RIB ready for uploads or form entry.",
        ],
        "source_title": "CAF - Students: housing aid",
        "source_url": CAF_STUDENT_HOUSING_AID_URL,
        "priority": 10,
        "locale": "en",
        "active": True,
    },
    {
        "id": "caf_housing_contract_campus_france",
        "step_id": "caf_high_level",
        "blocker_key": "rental_contract_missing",
        "scope": "caf",
        "title": "Get housing proof before applying for CAF",
        "why_it_matters": (
            "CAF housing aid depends on your housing situation, so a rental contract or housing certificate is a key prerequisite."
        ),
        "documents": [
            "Rental contract, lease, or residence certificate",
            "Proof of address if available",
        ],
        "suggested_actions": [
            "Ask your landlord, residence, or housing provider for the official housing document.",
            "Check that your name, address, dates, and rent details are clear on the document.",
            "Keep a digital copy ready before starting a CAF file.",
        ],
        "source_title": "CAF - Students: housing aid",
        "source_url": CAF_STUDENT_HOUSING_AID_URL,
        "priority": 20,
        "locale": "en",
        "active": True,
    },
    {
        "id": "housing_search_campus_france",
        "step_id": "housing_setup",
        "blocker_key": "permanent_housing_missing",
        "scope": "caf",
        "title": "Secure stable housing before deeper CAF preparation",
        "why_it_matters": (
            "Without stable housing, it is hard to prepare a CAF housing-aid file because the file depends on your accommodation."
        ),
        "documents": ["Housing offer, residence booking, rental contract, or housing certificate"],
        "suggested_actions": [
            "Prioritize a longer-term room, residence, or apartment before starting detailed CAF paperwork.",
            "Ask your school housing office or international office about student residences and partner housing options.",
            "Once housing is confirmed, request a written contract or certificate immediately.",
        ],
        "source_title": "CAF - Students: housing aid",
        "source_url": CAF_STUDENT_HOUSING_AID_URL,
        "priority": 10,
        "locale": "en",
        "active": True,
    },
    {
        "id": "vls_ts_validation_campus_france",
        "step_id": "vls_ts_validation",
        "blocker_key": "visa_not_validated",
        "scope": "full",
        "title": "Validate your VLS-TS before relying on other services",
        "why_it_matters": (
            "VLS-TS validation confirms your right to stay after arrival and can affect later administrative steps."
        ),
        "documents": [
            "Valid email address",
            "Visa information",
            "Arrival date in France",
            "French address",
            "Payment card for the online tax or electronic stamp",
        ],
        "suggested_actions": [
            "Use the official foreigner administration portal to validate the VLS-TS.",
            "Save the confirmation after validation.",
            "Keep the confirmation available for future administrative steps.",
        ],
        "source_title": "Service-Public - VLS-TS validation online",
        "source_url": SERVICE_PUBLIC_VLS_TS_VALIDATION_URL,
        "priority": 10,
        "locale": "en",
        "active": True,
    },
    {
        "id": "ameli_registration_campus_france",
        "step_id": "ameli_registration",
        "blocker_key": "certificat_scolarite_missing",
        "scope": "full",
        "title": "Prepare the documents for student health insurance",
        "why_it_matters": (
            "Health insurance registration helps you access reimbursements for healthcare in France."
        ),
        "documents": [
            "Certificate of enrolment for the current academic year",
            "Identity document",
            "Visa or residence document",
            "Civil-status document if requested",
            "RIB for reimbursements",
        ],
        "suggested_actions": [
            "Finish university registration first so you can obtain enrolment proof.",
            "Prepare digital copies before starting the health insurance registration.",
            "Keep your provisional certificate once the process starts.",
        ],
        "source_title": "Ameli - Social security registration for foreign students",
        "source_url": AMELI_FOREIGN_STUDENTS_URL,
        "priority": 10,
        "locale": "en",
        "active": True,
    },
]


def _is_postgres() -> bool:
    return DATABASE_URL.startswith(("postgres://", "postgresql://"))


def _postgres_url() -> str:
    if DATABASE_URL.startswith("postgres://"):
        return DATABASE_URL.replace("postgres://", "postgresql://", 1)
    return DATABASE_URL


def _sqlite_path() -> Path:
    raw_path = DATABASE_URL.removeprefix("sqlite:///")
    path = Path(raw_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


@contextmanager
def _sqlite_connection() -> Iterator[sqlite3.Connection]:
    path = _sqlite_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


@contextmanager
def _postgres_connection():
    import psycopg

    with psycopg.connect(_postgres_url()) as connection:
        yield connection


@contextmanager
def _connection():
    if _is_postgres():
        with _postgres_connection() as connection:
            yield connection
    else:
        with _sqlite_connection() as connection:
            yield connection


def init_db() -> None:
    if _is_postgres():
        with _connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS student_profiles (
                        student_id TEXT PRIMARY KEY,
                        profile_json JSONB NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS call_summaries (
                        id BIGSERIAL PRIMARY KEY,
                        student_id TEXT NOT NULL,
                        conversation_id TEXT,
                        summary TEXT NOT NULL,
                        saved_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS guidance_cards (
                        id TEXT PRIMARY KEY,
                        step_id TEXT NOT NULL,
                        blocker_key TEXT,
                        scope TEXT NOT NULL DEFAULT 'full',
                        title TEXT NOT NULL,
                        why_it_matters TEXT NOT NULL,
                        documents_json JSONB NOT NULL,
                        suggested_actions_json JSONB NOT NULL,
                        source_title TEXT,
                        source_url TEXT,
                        priority INTEGER NOT NULL DEFAULT 100,
                        locale TEXT NOT NULL DEFAULT 'en',
                        active BOOLEAN NOT NULL DEFAULT TRUE
                    )
                    """
                )
    else:
        with _connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS student_profiles (
                    student_id TEXT PRIMARY KEY,
                    profile_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS guidance_cards (
                    id TEXT PRIMARY KEY,
                    step_id TEXT NOT NULL,
                    blocker_key TEXT,
                    scope TEXT NOT NULL DEFAULT 'full',
                    title TEXT NOT NULL,
                    why_it_matters TEXT NOT NULL,
                    documents_json TEXT NOT NULL,
                    suggested_actions_json TEXT NOT NULL,
                    source_title TEXT,
                    source_url TEXT,
                    priority INTEGER NOT NULL DEFAULT 100,
                    locale TEXT NOT NULL DEFAULT 'en',
                    active INTEGER NOT NULL DEFAULT 1
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS call_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    conversation_id TEXT,
                    summary TEXT NOT NULL,
                    saved_at TEXT NOT NULL
                )
                """
            )

    seed_guidance_cards()


def seed_guidance_cards() -> None:
    with _connection() as connection:
        if _is_postgres():
            from psycopg.types.json import Json

            with connection.cursor() as cursor:
                for card in GUIDANCE_CARD_SEEDS:
                    cursor.execute(
                        """
                        INSERT INTO guidance_cards (
                            id, step_id, blocker_key, scope, title, why_it_matters,
                            documents_json, suggested_actions_json, source_title,
                            source_url, priority, locale, active
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            step_id = EXCLUDED.step_id,
                            blocker_key = EXCLUDED.blocker_key,
                            scope = EXCLUDED.scope,
                            title = EXCLUDED.title,
                            why_it_matters = EXCLUDED.why_it_matters,
                            documents_json = EXCLUDED.documents_json,
                            suggested_actions_json = EXCLUDED.suggested_actions_json,
                            source_title = EXCLUDED.source_title,
                            source_url = EXCLUDED.source_url,
                            priority = EXCLUDED.priority,
                            locale = EXCLUDED.locale,
                            active = EXCLUDED.active
                        """,
                        (
                            card["id"],
                            card["step_id"],
                            card["blocker_key"],
                            card["scope"],
                            card["title"],
                            card["why_it_matters"],
                            Json(card["documents"]),
                            Json(card["suggested_actions"]),
                            card["source_title"],
                            card["source_url"],
                            card["priority"],
                            card["locale"],
                            card["active"],
                        ),
                    )
            return

        for card in GUIDANCE_CARD_SEEDS:
            connection.execute(
                """
                INSERT INTO guidance_cards (
                    id, step_id, blocker_key, scope, title, why_it_matters,
                    documents_json, suggested_actions_json, source_title,
                    source_url, priority, locale, active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    step_id = excluded.step_id,
                    blocker_key = excluded.blocker_key,
                    scope = excluded.scope,
                    title = excluded.title,
                    why_it_matters = excluded.why_it_matters,
                    documents_json = excluded.documents_json,
                    suggested_actions_json = excluded.suggested_actions_json,
                    source_title = excluded.source_title,
                    source_url = excluded.source_url,
                    priority = excluded.priority,
                    locale = excluded.locale,
                    active = excluded.active
                """,
                (
                    card["id"],
                    card["step_id"],
                    card["blocker_key"],
                    card["scope"],
                    card["title"],
                    card["why_it_matters"],
                    json.dumps(card["documents"]),
                    json.dumps(card["suggested_actions"]),
                    card["source_title"],
                    card["source_url"],
                    card["priority"],
                    card["locale"],
                    1 if card["active"] else 0,
                ),
            )


def get_profile(student_id: str) -> Optional[StudentProfile]:
    with _connection() as connection:
        if _is_postgres():
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT profile_json FROM student_profiles WHERE student_id = %s",
                    (student_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                profile_data = row[0]
        else:
            row = connection.execute(
                "SELECT profile_json FROM student_profiles WHERE student_id = ?",
                (student_id,),
            ).fetchone()
            if row is None:
                return None
            profile_data = json.loads(row["profile_json"])

    return StudentProfile.model_validate(profile_data)


def save_profile(profile: StudentProfile) -> None:
    profile_data = profile.model_dump(mode="json")

    with _connection() as connection:
        if _is_postgres():
            from psycopg.types.json import Json

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO student_profiles (student_id, profile_json, updated_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (student_id)
                    DO UPDATE SET profile_json = EXCLUDED.profile_json, updated_at = NOW()
                    """,
                    (profile.student_id, Json(profile_data)),
                )
        else:
            connection.execute(
                """
                INSERT INTO student_profiles (student_id, profile_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(student_id)
                DO UPDATE SET profile_json = excluded.profile_json, updated_at = excluded.updated_at
                """,
                (
                    profile.student_id,
                    json.dumps(profile_data),
                    datetime.utcnow().isoformat(),
                ),
            )


def profile_exists(student_id: str) -> bool:
    return get_profile(student_id) is not None


def get_guidance_cards(
    step_id: str,
    blocker_keys: list[str] | None = None,
    scope: str = "full",
    locale: str = "en",
) -> list[GuidanceCard]:
    blocker_keys = blocker_keys or []

    with _connection() as connection:
        if _is_postgres():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id, step_id, blocker_key, scope, title, why_it_matters,
                        documents_json, suggested_actions_json, source_title,
                        source_url, priority, locale
                    FROM guidance_cards
                    WHERE active = TRUE
                        AND step_id = %s
                        AND locale = %s
                        AND scope IN (%s, 'full')
                    ORDER BY priority ASC, id ASC
                    """,
                    (step_id, locale, scope),
                )
                rows = cursor.fetchall()
                raw_cards = [
                    {
                        "id": row[0],
                        "step_id": row[1],
                        "blocker_key": row[2],
                        "scope": row[3],
                        "title": row[4],
                        "why_it_matters": row[5],
                        "documents": row[6],
                        "suggested_actions": row[7],
                        "source_title": row[8],
                        "source_url": row[9],
                        "priority": row[10],
                        "locale": row[11],
                    }
                    for row in rows
                ]
        else:
            try:
                rows = connection.execute(
                    """
                    SELECT
                        id, step_id, blocker_key, scope, title, why_it_matters,
                        documents_json, suggested_actions_json, source_title,
                        source_url, priority, locale
                    FROM guidance_cards
                    WHERE active = 1
                        AND step_id = ?
                        AND locale = ?
                        AND scope IN (?, 'full')
                    ORDER BY priority ASC, id ASC
                    """,
                    (step_id, locale, scope),
                ).fetchall()
            except sqlite3.OperationalError as exc:
                if "no such table" in str(exc):
                    return []
                raise
            raw_cards = [
                {
                    "id": row["id"],
                    "step_id": row["step_id"],
                    "blocker_key": row["blocker_key"],
                    "scope": row["scope"],
                    "title": row["title"],
                    "why_it_matters": row["why_it_matters"],
                    "documents": json.loads(row["documents_json"]),
                    "suggested_actions": json.loads(row["suggested_actions_json"]),
                    "source_title": row["source_title"],
                    "source_url": row["source_url"],
                    "priority": row["priority"],
                    "locale": row["locale"],
                }
                for row in rows
            ]

    matching_cards = [
        card
        for card in raw_cards
        if card["blocker_key"] is None or card["blocker_key"] in blocker_keys
    ]

    return [GuidanceCard.model_validate(card) for card in matching_cards]


def add_call_summary(
    student_id: str,
    summary: str,
    conversation_id: Optional[str] = None,
) -> None:
    with _connection() as connection:
        if _is_postgres():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO call_summaries (student_id, conversation_id, summary)
                    VALUES (%s, %s, %s)
                    """,
                    (student_id, conversation_id, summary),
                )
        else:
            connection.execute(
                """
                INSERT INTO call_summaries (student_id, conversation_id, summary, saved_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    student_id,
                    conversation_id,
                    summary,
                    datetime.utcnow().isoformat(),
                ),
            )


def list_call_summaries() -> list[dict]:
    with _connection() as connection:
        if _is_postgres():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT student_id, conversation_id, summary, saved_at
                    FROM call_summaries
                    ORDER BY saved_at DESC
                    """
                )
                rows = cursor.fetchall()
                return [
                    {
                        "student_id": row[0],
                        "conversation_id": row[1],
                        "summary": row[2],
                        "saved_at": row[3].isoformat(),
                    }
                    for row in rows
                ]

        rows = connection.execute(
            """
            SELECT student_id, conversation_id, summary, saved_at
            FROM call_summaries
            ORDER BY saved_at DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]
