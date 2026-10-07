import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Award,
  CheckCircle2,
  CircleAlert,
  Clock3,
  Download,
  FileBadge2,
  Loader2,
  Plus,
  RefreshCw,
  Sparkles,
  Trash2,
  Users,
  XCircle,
} from "lucide-react";
import "./index.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const emptyRecipient = () => ({
  name: "",
  email: "",
  course_name: "",
});

function App() {
  const [eventName, setEventName] = useState("AI & Machine Learning Workshop 2026");
  const [issuerName, setIssuerName] = useState("Parul University");
  const [recipients, setRecipients] = useState([
    { name: "", email: "", course_name: "" },
  ]);
  const [job, setJob] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const completed = (job?.success_count || 0) + (job?.failure_count || 0);
  const progress = job?.progress_percent || 0;

  const canSubmit = useMemo(
    () =>
      eventName.trim() &&
      issuerName.trim() &&
      recipients.length > 0 &&
      recipients.every(
        (r) => r.name.trim() && r.email.trim() && r.course_name.trim()
      ),
    [eventName, issuerName, recipients]
  );

  const updateRecipient = (index, field, value) => {
    setRecipients((current) =>
      current.map((recipient, i) =>
        i === index ? { ...recipient, [field]: value } : recipient
      )
    );
  };

  const addRecipient = () =>
    setRecipients((current) => [...current, emptyRecipient()]);

  const removeRecipient = (index) => {
    setRecipients((current) => current.filter((_, i) => i !== index));
  };

  const submitJob = async (event) => {
    event.preventDefault();
    if (!canSubmit) return;

    setSubmitting(true);
    setError("");
    setJob(null);

    try {
      const response = await fetch(`${API_BASE}/api/v1/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_name: eventName,
          issuer_name: issuerName,
          recipients,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        const detail = Array.isArray(data.detail)
          ? data.detail.map((x) => x.msg).join(", ")
          : data.detail || "Unable to create generation job.";
        throw new Error(detail);
      }

      setJob(data);
    } catch (err) {
      setError(
        err.message.includes("Failed to fetch")
          ? "Cannot connect to the application server. Make sure the service is running and CORS is configured."
          : err.message
      );
    } finally {
      setSubmitting(false);
    }
  };

  useEffect(() => {
    if (!job?.job_id) return;

    let timer;
    const poll = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/v1/jobs/${job.job_id}`);
        if (!response.ok) throw new Error("Could not read job status.");
        const data = await response.json();
        setJob(data);

        if (
          data.status === "pending" ||
          data.status === "processing"
        ) {
          timer = setTimeout(poll, 1000);
        }
      } catch (err) {
        setError(err.message);
      }
    };

    poll();
    return () => clearTimeout(timer);
  }, [job?.job_id]);

  const reset = () => {
    setJob(null);
    setError("");
    setRecipients([emptyRecipient()]);
  };

  return (
    <div className="min-h-screen text-zinc-100">
      <header className="border-b border-white/5 bg-zinc-950/50 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500 shadow-lg shadow-indigo-500/25">
              <Award size={21} />
            </div>
            <div>
              <p className="text-sm font-bold tracking-tight">CERTIFLOW</p>
              <p className="text-[11px] text-zinc-500">Certificate management platform</p>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-10 lg:py-14">
        <section className="mb-10 max-w-3xl">
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
            Generate hundreds of certificates
            <span className="block bg-gradient-to-r from-indigo-300 via-sky-300 to-cyan-200 bg-clip-text text-transparent">
              from one simple workflow.
            </span>
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-zinc-400">
            Create a bulk generation job, monitor it in real time, and download
            every successful certificate from one modern dashboard.
          </p>
        </section>

        {error && (
          <div className="mb-6 flex items-start gap-3 rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-200">
            <CircleAlert className="mt-0.5 shrink-0" size={18} />
            <div className="flex-1">{error}</div>
            <button onClick={() => setError("")} className="text-red-300">
              <XCircle size={17} />
            </button>
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-[1.1fr_.9fr]">
          <section className="glass rounded-3xl p-6 shadow-glow sm:p-8">
            <div className="mb-7 flex items-center justify-between">
              <div>
                <p className="text-lg font-bold">Generation details</p>
                <p className="mt-1 text-sm text-zinc-500">
                  One request can contain multiple recipients.
                </p>
              </div>
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-zinc-800">
                <FileBadge2 size={21} className="text-indigo-300" />
              </div>
            </div>

            <form onSubmit={submitJob} className="space-y-6">
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="mb-2 block text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    Event name
                  </span>
                  <input
                    className="input"
                    value={eventName}
                    onChange={(e) => setEventName(e.target.value)}
                    placeholder="AI Workshop 2026"
                  />
                </label>

                <label className="block">
                  <span className="mb-2 block text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    Issuer
                  </span>
                  <input
                    className="input"
                    value={issuerName}
                    onChange={(e) => setIssuerName(e.target.value)}
                    placeholder="Your organization"
                  />
                </label>
              </div>

              <div>
                <div className="mb-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold">Recipients</p>
                    <p className="text-xs text-zinc-600">
                      {recipients.length} recipient{recipients.length !== 1 ? "s" : ""}
                    </p>
                  </div>
                  <button type="button" onClick={addRecipient} className="btn-secondary">
                    <Plus size={15} /> Add recipient
                  </button>
                </div>

                <div className="space-y-3">
                  {recipients.map((recipient, index) => (
                    <div
                      key={index}
                      className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4"
                    >
                      <div className="mb-3 flex items-center justify-between">
                        <span className="text-xs font-semibold text-zinc-500">
                          RECIPIENT {String(index + 1).padStart(2, "0")}
                        </span>
                        {recipients.length > 1 && (
                          <button
                            type="button"
                            onClick={() => removeRecipient(index)}
                            className="text-zinc-600 transition hover:text-red-400"
                          >
                            <Trash2 size={16} />
                          </button>
                        )}
                      </div>

                      <div className="grid gap-3 sm:grid-cols-3">
                        <input
                          className="input"
                          placeholder="Full name"
                          value={recipient.name}
                          onChange={(e) =>
                            updateRecipient(index, "name", e.target.value)
                          }
                        />
                        <input
                          className="input"
                          type="email"
                          placeholder="Email address"
                          value={recipient.email}
                          onChange={(e) =>
                            updateRecipient(index, "email", e.target.value)
                          }
                        />
                        <input
                          className="input"
                          placeholder="Course / achievement"
                          value={recipient.course_name}
                          onChange={(e) =>
                            updateRecipient(index, "course_name", e.target.value)
                          }
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <button
                className="btn-primary w-full py-3.5"
                disabled={!canSubmit || submitting}
              >
                {submitting ? (
                  <>
                    <Loader2 className="animate-spin" size={18} />
                    Creating job...
                  </>
                ) : (
                  <>
                    <Sparkles size={18} />
                    Generate certificates
                  </>
                )}
              </button>
            </form>
          </section>

          <section className="space-y-6">
            <div className="glass rounded-3xl p-6 sm:p-8">
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <p className="text-lg font-bold">Generation status</p>
                  <p className="mt-1 text-sm text-zinc-500">
                    {job ? `Job #${job.job_id}` : "No active job"}
                  </p>
                </div>
                <StatusBadge status={job?.status} />
              </div>

              {job ? (
                <>
                  <div className="mb-6">
                    <div className="mb-2 flex justify-between text-xs">
                      <span className="text-zinc-500">Progress</span>
                      <span className="font-semibold text-zinc-200">
                        {progress.toFixed(0)}%
                      </span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-zinc-800">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-cyan-400 transition-all duration-500"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <p className="mt-2 text-xs text-zinc-600">
                      {completed} of {job.total_count} certificates processed
                    </p>
                  </div>

                  <div className="grid grid-cols-3 gap-3">
                    <Metric icon={<Users size={16} />} value={job.total_count} label="Total" />
                    <Metric icon={<CheckCircle2 size={16} />} value={job.success_count} label="Success" />
                    <Metric icon={<XCircle size={16} />} value={job.failure_count} label="Failed" />
                  </div>
                </>
              ) : (
                <div className="rounded-2xl border border-dashed border-zinc-800 p-8 text-center">
                  <Clock3 className="mx-auto mb-3 text-zinc-700" size={28} />
                  <p className="text-sm font-medium text-zinc-400">
                    Your job status will appear here
                  </p>
                  <p className="mt-1 text-xs text-zinc-600">
                    Submit recipients to start generation.
                  </p>
                </div>
              )}
            </div>

            {job?.certificates?.length > 0 && (
              <div className="glass rounded-3xl p-6 sm:p-8">
                <div className="mb-5 flex items-center justify-between">
                  <div>
                    <p className="text-lg font-bold">Certificates</p>
                    <p className="mt-1 text-sm text-zinc-500">
                      Generated files for this job
                    </p>
                  </div>
                  {job.status === "completed" || job.status === "completed_with_errors" ? (
                    <button className="btn-secondary" onClick={reset}>
                      <RefreshCw size={15} /> New job
                    </button>
                  ) : null}
                </div>

                <div className="space-y-2">
                  {job.certificates.map((certificate) => (
                    <div
                      key={certificate.id}
                      className="flex items-center gap-3 rounded-2xl border border-zinc-800 bg-zinc-950/50 p-3"
                    >
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-zinc-800">
                        {certificate.certificate_status === "completed" ? (
                          <CheckCircle2 size={18} className="text-emerald-400" />
                        ) : (
                          <XCircle size={18} className="text-red-400" />
                        )}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-semibold">
                          {certificate.recipient_name}
                        </p>
                        <p className="truncate text-xs text-zinc-600">
                          {certificate.course_name}
                        </p>
                      </div>

                      {certificate.certificate_status === "completed" ? (
                        <a
                          className="btn-secondary shrink-0 px-3"
                          href={`${API_BASE}/api/v1/certificates/${certificate.id}/download`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          <Download size={15} />
                          <span className="hidden sm:inline">PDF</span>
                        </a>
                      ) : (
                        <span className="max-w-32 text-right text-xs text-red-400">
                          {certificate.error_message || "Generation failed"}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        </div>
      </main>

      <footer className="mx-auto max-w-7xl px-6 pb-8 pt-4 text-center text-xs text-zinc-700">
        CertiFlow · Bulk Certificate Management
      </footer>
    </div>
  );
}

function Metric({ icon, value, label }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-950/50 p-4">
      <div className="mb-2 text-indigo-300">{icon}</div>
      <p className="text-xl font-bold">{value}</p>
      <p className="text-xs text-zinc-600">{label}</p>
    </div>
  );
}

function StatusBadge({ status }) {
  const styles = {
    pending: "border-amber-400/20 bg-amber-400/10 text-amber-300",
    processing: "border-sky-400/20 bg-sky-400/10 text-sky-300",
    completed: "border-emerald-400/20 bg-emerald-400/10 text-emerald-300",
    completed_with_errors:
      "border-orange-400/20 bg-orange-400/10 text-orange-300",
    failed: "border-red-400/20 bg-red-400/10 text-red-300",
  };

  const label = (status || "idle").replaceAll("_", " ");

  return (
    <span
      className={`rounded-full border px-3 py-1.5 text-[11px] font-semibold capitalize ${
        styles[status] || "border-zinc-700 bg-zinc-800 text-zinc-400"
      }`}
    >
      {label}
    </span>
  );
}

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);