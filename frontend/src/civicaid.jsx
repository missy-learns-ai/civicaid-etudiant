import React, { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  AlertCircle,
  ArrowRight,
  Building2,
  CheckCircle2,
  ChevronRight,
  Circle,
  Clock,
  FileText,
  Heart,
  Home,
  KeyRound,
  RotateCw,
  Sparkles,
  Wallet,
} from "lucide-react";

const API_BASE_URL = import.meta.env.VITE_CIVICAID_API_BASE_URL || "http://127.0.0.1:8000";
const ELEVENLABS_AGENT_ID =
  import.meta.env.VITE_ELEVENLABS_AGENT_ID || "agent_0301kqspeqntenb8stq8k9nnwc5q";
const STUDENT_ID = import.meta.env.VITE_CIVICAID_STUDENT_ID || "demo_001";
const DEMO_PRELOADED = import.meta.env.VITE_DEMO_PRELOADED === "true";
const FORCE_LANDING_PAGE = import.meta.env.VITE_FORCE_LANDING_PAGE === "true";

const DEMO_PROFILE_PATCH = {
  name: "Pratistha Thapa",
  nationality_category: "non_eu",
  country: "Nepal",
  has_arrived: true,
  arrival_date: "2026-09-10",
  visa_type: "vls_ts_student",
  visa_validated: false,
  visa_expiry_date: "2027-09-09",
  has_french_address: true,
  cvec_status: "not_done",
  university_registration_status: "in_progress",
  has_certificat_scolarite: false,
  has_student_card: false,
  ameli_registered: false,
  has_bank_account: false,
  has_rib: false,
  housing_status: "temporary",
  has_permanent_housing: false,
  has_rental_contract: false,
  wants_caf: true,
};

const STEP_ICONS = {
  vls_ts_validation: FileText,
  cvec_university_registration: Building2,
  ameli_registration: Heart,
  bank_rib: Wallet,
  housing_setup: Home,
  caf_high_level: KeyRound,
  residence_renewal: RotateCw,
};

const STATUS_CONFIG = {
  urgent: { label: "Urgent", icon: AlertCircle, dot: "#dc2626", text: "#991b1b", bg: "#fef2f2" },
  blocked: { label: "Blocked", icon: Clock, dot: "#d97706", text: "#92400e", bg: "#fffbeb" },
  in_progress: { label: "In progress", icon: Circle, dot: "#2563eb", text: "#1e40af", bg: "#eff6ff" },
  ready: { label: "Ready", icon: CheckCircle2, dot: "#059669", text: "#065f46", bg: "#ecfdf5" },
  done: { label: "Done", icon: CheckCircle2, dot: "#059669", text: "#065f46", bg: "#ecfdf5" },
  future: { label: "Later", icon: Circle, dot: "#94a3b8", text: "#475569", bg: "#f8fafc" },
  unknown: { label: "Unknown", icon: Circle, dot: "#94a3b8", text: "#475569", bg: "#f8fafc" },
  not_relevant: { label: "Not relevant", icon: Circle, dot: "#94a3b8", text: "#475569", bg: "#f8fafc" },
};

const BLOCKER_COPY = {
  visa_not_validated: "VLS-TS not yet validated online",
  cvec_attestation_missing: "CVEC attestation needed",
  vls_ts_validation_or_residence_documentation: "Awaiting visa validation",
  certificat_scolarite_missing: "Enrollment certificate needed",
  proof_of_residence_or_enrollment_missing: "Need address and enrollment proof",
  permanent_housing_missing: "Need permanent housing",
  rib_missing: "Need RIB / bank details",
  french_address_missing: "French address missing",
  rental_contract_missing: "Rental contract missing",
  visa_expiry_date_unknown: "Visa expiry date missing",
};

const DEMO_PROFILE = {
  ...DEMO_PROFILE_PATCH,
  profile_completion: 1,
};

const DEMO_ROADMAP = {
  steps: [
    {
      step_id: "vls_ts_validation",
      priority: 1,
      title: "Validate your VLS-TS",
      status: "urgent",
      explanation:
        "Your long-stay student visa must be validated online within 3 months of arrival. Without it, you cannot legally remain in France or access most other administrative services.",
      next_action: "Complete the online validation on the official foreigner administration portal.",
      blocking_items: ["visa_not_validated"],
      sources: [{ title: "ANEF - Validation VLS-TS", publisher: "Ministère de l'Intérieur" }],
    },
    {
      step_id: "cvec_university_registration",
      priority: 2,
      title: "CVEC and university registration",
      status: "blocked",
      explanation:
        "Your administrative registration at the university is in progress. You need the CVEC attestation to finalize it and receive your student card.",
      next_action: "Pay the CVEC online and download your attestation.",
      blocking_items: ["cvec_attestation_missing"],
      sources: [{ title: "CVEC - Contribution Vie Étudiante", publisher: "CROUS" }],
    },
  ],
};

function normalizeRoadmap(response) {
  return response?.roadmap || response || null;
}

function statusConfig(status) {
  return STATUS_CONFIG[status] || STATUS_CONFIG.unknown;
}

function formatValue(value) {
  if (value === true) return "Yes";
  if (value === false) return "No";
  if (value == null || value === "") return "Unknown";
  if (typeof value !== "string") return String(value);

  const normalized = value.replaceAll("_", " ");
  const replacements = {
    "non eu": "Non-EU",
    "vls ts student": "VLS-TS student",
    "not done": "Not done",
    "in progress": "In progress",
  };

  return replacements[normalized] || normalized.replace(/\b\w/g, (char) => char.toUpperCase());
}

function toolUrl(path) {
  return `${API_BASE_URL.replace(/\/$/, "")}${path}`;
}

async function apiRequest(path, options = {}) {
  const response = await fetch(toolUrl(path), {
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const detail = await response.text();
    const error = new Error(`${response.status} ${response.statusText}: ${detail}`);
    error.status = response.status;
    throw error;
  }

  const text = await response.text();
  return text ? JSON.parse(text) : {};
}

async function fetchProfile(studentId) {
  const response = await apiRequest(`/debug/profile-status/${studentId}`);
  if (!response.exists) return null;
  return response.profile || response;
}

async function generateRoadmap(studentId) {
  const response = await apiRequest("/tools/generate-arrival-roadmap", {
    method: "POST",
    body: JSON.stringify({ student_id: studentId }),
  });
  return normalizeRoadmap(response);
}

function ElevenLabsWidget({ agentId, dynamicVariables }) {
  useEffect(() => {
    const scriptId = "elevenlabs-convai-script";
    if (document.getElementById(scriptId)) return;

    const script = document.createElement("script");
    script.id = scriptId;
    script.src = "https://unpkg.com/@elevenlabs/convai-widget-embed";
    script.async = true;
    script.type = "text/javascript";
    document.body.appendChild(script);
  }, []);

  return (
    <div className="elevenlabs-widget-slot">
      {agentId ? (
        <elevenlabs-convai
          agent-id={agentId}
          dynamic-variables={JSON.stringify(dynamicVariables)}
          override-first-message="Hi, I am CivicAid Étudiant. I can help organize your student administrative steps in France. Are you ready to begin?"
        />
      ) : (
        <div className="soft-placeholder">Voice assistant unavailable</div>
      )}
    </div>
  );
}

function StatusPill({ status }) {
  const config = statusConfig(status);
  return (
    <div className="status-pill" style={{ background: config.bg, color: config.text }}>
      <span style={{ background: config.dot }} />
      {config.label}
    </div>
  );
}

function ProgressRing({ percent, size = 112, stroke = 6 }) {
  const radius = (size - stroke) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percent / 100) * circumference;

  return (
    <div className="progress-ring" style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#f1f5f9" strokeWidth={stroke} />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#002395"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
        />
      </svg>
      <div>
        <strong>{percent}%</strong>
        <span>complete</span>
      </div>
    </div>
  );
}

function VoiceSection({ hasProfile }) {
  return (
    <section className="voice-card">
      <div className="flag-stripe" />
      <div className="dot-grid" aria-hidden="true" />
      <div className="voice-copy">
        <div className="eyebrow">
          <span className="live-dot" />
          Voice assistant ready
        </div>
        <h2>
          {hasProfile ? (
            <>
              Continue the conversation <em>any time.</em>
            </>
          ) : (
            <>
              Tell us where <em>you are.</em>
            </>
          )}
        </h2>
        <p>
          {hasProfile
            ? "Update your situation, ask questions about any step, or clarify what to do next."
            : "Start with a quick voice session. CivicAid Étudiant will turn your answers into a personalized administrative roadmap."}
        </p>
      </div>
      <div className="voice-widget-wrap">
        <ElevenLabsWidget
          agentId={ELEVENLABS_AGENT_ID}
          dynamicVariables={{
            student_id: STUDENT_ID,
            api_base_url: API_BASE_URL,
            product_context: "CivicAid Étudiant student dashboard",
          }}
        />
      </div>
    </section>
  );
}

function EmptyState({ error }) {
  const previewSteps = [
    { icon: FileText, label: "Visa validation" },
    { icon: Building2, label: "University and CVEC" },
    { icon: Heart, label: "Health insurance" },
    { icon: Wallet, label: "Bank account" },
    { icon: Home, label: "Housing" },
    { icon: KeyRound, label: "CAF housing aid" },
  ];

  return (
    <div>
      <motion.section className="landing-hero" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <div className="eyebrow blue">
          <Sparkles size={13} />
          For non-EU students arriving in France
        </div>
        <h1>
          The French administrative maze, <em>simplified.</em>
        </h1>
        <p>
          Have a quick conversation with our assistant. We build a personalized roadmap showing
          exactly what you need to do, in what order, and what is blocking what.
        </p>
      </motion.section>

      <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.08 }}>
        <VoiceSection hasProfile={false} />
      </motion.section>

      {error ? <div className="notice error">{error}</div> : null}

      <motion.section className="preview-panel" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.16 }}>
        <div className="eyebrow muted">What we will cover</div>
        <div className="preview-grid">
          {previewSteps.map((step, index) => {
            const Icon = step.icon;
            return (
              <motion.div
                className="preview-tile"
                key={step.label}
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.24 + index * 0.04 }}
              >
                <div>
                  <Icon size={16} />
                </div>
                <span>{step.label}</span>
              </motion.div>
            );
          })}
        </div>
        <div className="soft-callout">
          <Sparkles size={16} />
          Your roadmap appears here once the assistant has gathered the basics: visa type, arrival
          status, university registration, housing, and banking readiness.
        </div>
      </motion.section>
    </div>
  );
}

function StepCard({ step, index, expanded, onToggle }) {
  const config = statusConfig(step.status);
  const Icon = STEP_ICONS[step.step_id] || FileText;
  const sources = step.sources || [];

  return (
    <motion.article
      className="roadmap-step"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: index * 0.04, ease: [0.16, 1, 0.3, 1] }}
      style={{ "--status-color": config.dot }}
    >
      <button onClick={onToggle} className="step-button">
        <div className="step-index">{String(step.priority || index + 1).padStart(2, "0")}</div>
        <div className="step-icon" style={{ background: config.bg, color: config.text }}>
          <Icon size={18} />
        </div>
        <div className="step-title">
          <h3>{step.title}</h3>
          <StatusPill status={step.status} />
        </div>
        <motion.div animate={{ rotate: expanded ? 90 : 0 }} transition={{ duration: 0.25 }} className="step-chevron">
          <ChevronRight size={20} />
        </motion.div>
      </button>

      <AnimatePresence>
        {expanded ? (
          <motion.div
            className="step-detail"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.32, ease: [0.16, 1, 0.3, 1] }}
          >
            <div>
              <p>{step.explanation}</p>
              <div className="next-action">
                <span>Next action</span>
                <strong>{step.next_action}</strong>
              </div>
              {step.blocking_items?.length ? (
                <div className="blockers">
                  <span>Blockers</span>
                  <div>
                    {step.blocking_items.map((blocker) => (
                      <small key={blocker}>
                        <AlertCircle size={12} />
                        {BLOCKER_COPY[blocker] || formatValue(blocker)}
                      </small>
                    ))}
                  </div>
                </div>
              ) : null}
              {sources.length ? (
                <div className="sources">
                  {sources.map((source, sourceIndex) => (
                    <span key={source.source_id || source.title || sourceIndex}>
                      {source.title}
                      {source.publisher ? <em> · {source.publisher}</em> : null}
                    </span>
                  ))}
                </div>
              ) : null}
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </motion.article>
  );
}

function ProfileGrid({ profile }) {
  const isComplete = (value) => value != null && value !== false && value !== "unknown" && value !== "not_done";
  const fields = [
    ["Name", profile.name],
    ["Country", profile.country],
    ["Visa type", profile.visa_type],
    ["Visa validated", profile.visa_validated],
    ["Visa expires", profile.visa_expiry_date],
    ["Arrival", profile.arrival_date],
    ["French address", profile.has_french_address],
    ["CVEC", profile.cvec_status],
    ["University", profile.university_registration_status],
    ["Student card", profile.has_student_card],
    ["Ameli", profile.ameli_registered],
    ["Bank account", profile.has_bank_account],
    ["RIB", profile.has_rib],
    ["Housing", profile.housing_status],
    ["Wants CAF", profile.wants_caf],
  ];

  return (
    <div className="profile-grid-new">
      {fields.map(([label, value]) => (
        <div className="profile-chip" key={label}>
          <div>
            <span>{label}</span>
            <strong>{label === "Name" && value ? value : formatValue(value)}</strong>
          </div>
          {isComplete(value) ? <CheckCircle2 size={16} /> : <Circle size={16} />}
        </div>
      ))}
    </div>
  );
}

function PopulatedState({ profile, roadmap, error }) {
  const steps = roadmap?.steps || [];
  const [expandedStep, setExpandedStep] = useState(steps[0]?.step_id || null);
  const [activeTab, setActiveTab] = useState("roadmap");

  useEffect(() => {
    setExpandedStep(steps[0]?.step_id || null);
  }, [steps[0]?.step_id]);

  const trackedFields = Object.keys(DEMO_PROFILE_PATCH).filter((field) => field !== "name");
  const completedFields = trackedFields.filter((field) => {
    const value = profile[field];
    return value != null && value !== "unknown";
  }).length;
  const completion = Math.round((completedFields / trackedFields.length) * 100);
  const needsAttention = steps.filter((step) => ["urgent", "blocked"].includes(step.status)).length;
  const movingCount = steps.filter((step) => ["in_progress", "ready", "done"].includes(step.status)).length;
  const topStep = steps.find((step) => step.step_id === roadmap?.top_priority_step_id) || steps[0];
  const firstName = profile.name?.split(" ")[0] || "there";

  return (
    <div>
      <motion.section className="landing-hero compact" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <div className="eyebrow blue">
          <Sparkles size={13} />
          Your administrative roadmap
        </div>
        <h1>
          Bonjour, {firstName}. <em>Here is what comes next.</em>
        </h1>
        <p>
          We turned French administration into {steps.length} clear steps, prioritized for your
          situation. Talk to your assistant any time to update your status.
        </p>
      </motion.section>

      <section className="hero-grid">
        <VoiceSection hasProfile />
        <aside className="urgent-card">
          <div className="eyebrow red">
            <AlertCircle size={13} />
            Most urgent
          </div>
          <h3>{topStep?.title || "Review roadmap"}</h3>
          <p>{topStep?.next_action || "Refresh the roadmap after your voice session."}</p>
          <button
            onClick={() => {
              setActiveTab("roadmap");
              setExpandedStep(topStep?.step_id);
              document.getElementById("roadmap-anchor")?.scrollIntoView({ behavior: "smooth" });
            }}
          >
            See full step
            <ArrowRight size={14} />
          </button>
        </aside>
      </section>

      {error ? <div className="notice error">{error}</div> : null}

      <section className="metrics-panel">
        <div>
          <ProgressRing percent={completion} />
        </div>
        <Metric label="Roadmap" value={steps.length} suffix="steps" />
        <Metric label="Need attention" value={needsAttention} tone="red" />
        <Metric label="Moving forward" value={movingCount} tone="blue" />
      </section>

      <section id="roadmap-anchor" className="roadmap-tabs">
        <div className="segmented-tabs">
          {[
            ["roadmap", "Roadmap"],
            ["profile", "Your profile"],
          ].map(([id, label]) => (
            <button className={activeTab === id ? "active" : ""} onClick={() => setActiveTab(id)} key={id}>
              {label}
            </button>
          ))}
        </div>
      </section>

      <AnimatePresence mode="wait">
        {activeTab === "roadmap" ? (
          <motion.div key="roadmap" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }}>
            <div className="steps-list">
              {steps.map((step, index) => (
                <StepCard
                  key={step.step_id}
                  step={step}
                  index={index}
                  expanded={expandedStep === step.step_id}
                  onToggle={() => setExpandedStep(expandedStep === step.step_id ? null : step.step_id)}
                />
              ))}
            </div>
          </motion.div>
        ) : (
          <motion.div key="profile" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }}>
            <ProfileGrid profile={profile} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function Metric({ label, value, suffix, tone }) {
  return (
    <div className={`metric ${tone || ""}`}>
      <span>{label}</span>
      <strong>
        {value}
        {suffix ? <em>{suffix}</em> : null}
      </strong>
    </div>
  );
}

export default function CivicAid() {
  const [profile, setProfile] = useState(DEMO_PRELOADED ? DEMO_PROFILE : null);
  const [roadmap, setRoadmap] = useState(DEMO_PRELOADED ? DEMO_ROADMAP : null);
  const [error, setError] = useState("");

  const hasData = Boolean(profile && roadmap?.steps?.length);

  const refresh = useMemo(
    () => async () => {
      setError("");
      try {
        const fetchedProfile = await fetchProfile(STUDENT_ID);
        if (!fetchedProfile) {
          setProfile(null);
          setRoadmap(null);
          return;
        }

        setProfile(fetchedProfile);
        const fetchedRoadmap = await generateRoadmap(STUDENT_ID);
        setRoadmap(fetchedRoadmap);
      } catch (event) {
        if (event.status === 404) {
          setProfile(null);
          setRoadmap(null);
          return;
        }

        setError("Could not connect to the roadmap service. Please check that the backend is running.");
      }
    },
    [],
  );

  useEffect(() => {
    if (DEMO_PRELOADED || FORCE_LANDING_PAGE) return undefined;
    refresh();
    const interval = window.setInterval(() => {
      if (!profile) refresh();
    }, 8000);
    return () => window.clearInterval(interval);
  }, [profile, refresh]);

  return (
    <div className="civicaid-app">
      <header className="topbar">
        <div>
          <div className="mini-flag">
            <span />
            <span />
            <span />
          </div>
          <strong>
            CivicAid <em>Étudiant</em>
          </strong>
        </div>
      </header>

      <main>
        <AnimatePresence mode="wait">
          {hasData ? (
            <motion.div key="populated" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <PopulatedState profile={profile} roadmap={roadmap} error={error} />
            </motion.div>
          ) : (
            <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <EmptyState error={error} />
            </motion.div>
          )}
        </AnimatePresence>

        <footer>
          <span>CivicAid Étudiant · Built for international students in France</span>
          <em>Liberté, égalité, clarté.</em>
        </footer>
      </main>
    </div>
  );
}
