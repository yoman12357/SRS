import { FormEvent, useEffect, useRef, useState } from "react";
import {
  Analysis,
  Clarifications,
  approved,
  isActive,
  Json,
  label,
  Project,
  Reference,
  request,
  Review,
  Run,
  sections,
  Summary,
  Version,
  VersionSummary,
} from "./api";
import { SectionEditor } from "./SectionEditor";
import { StructuredValue } from "./StructuredValue";
import { formatElapsed, RunTiming } from "./RunTiming";
import { SRSReport } from "./SRSReport";

type ChatMessage = { role: "you" | "assistant"; text: string };

export function App() {
  const [projects, setProjects] = useState<Summary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(() =>
    localStorage.getItem("cybersrs.selected"),
  );
  const selectedRef = useRef(selectedId);
  const [project, setProject] = useState<Project | null>(null);
  const [versions, setVersions] = useState<VersionSummary[]>([]);
  const [version, setVersion] = useState<Version | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [references, setReferences] = useState<Reference[]>([]);
  const [run, setRun] = useState<Run | null>(null);
  const [section, setSection] = useState("introduction");
  const [clarifications, setClarifications] = useState<Clarifications | null>(
    null,
  );
  const [tab, setTab] = useState<"gather" | "document">("gather");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [health, setHealth] = useState("Checking local runtime");
  const [editValue, setEditValue] = useState<Json | undefined>();
  const [editActor, setEditActor] = useState<"human" | "assistant">("human");
  const [reviewer, setReviewer] = useState("");
  const [comment, setComment] = useState("");
  const [showReview, setShowReview] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [chatText, setChatText] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatBusy, setChatBusy] = useState(false);
  const disabled = busy || isActive(run);
  const base = `/projects/${selectedId}`;

  async function listProjects() {
    setProjects(await request<Summary[]>("/projects"));
  }
  function select(id: string | null) {
    if (selectedRef.current === id) return;
    selectedRef.current = id;
    setSelectedId(id);
    setError("");
    setEditValue(undefined);
    setProject(null);
    setVersion(null);
    setReviews([]);
    setVersions([]);
    setRun(null);
    setReferences([]);
    setClarifications(null);
    setAnswers({});
    setTab("gather");
    setShowChat(false);
    setMessages([]);
    setChatText("");
    setShowReview(false);
    if (id) localStorage.setItem("cybersrs.selected", id);
    else localStorage.removeItem("cybersrs.selected");
  }
  async function loadVersion(projectId: string, versionId: string) {
    const [data, history] = await Promise.all([
      request<Version>(`/projects/${projectId}/versions/${versionId}`),
      request<Review[]>(`/projects/${projectId}/versions/${versionId}/reviews`),
    ]);
    if (selectedRef.current === projectId) {
      setVersion(data);
      setReviews(history);
    }
  }
  async function refresh(id: string, loadRun = true) {
    const [data, history, docs, runs] = await Promise.all([
      request<Project>(`/projects/${id}`),
      request<VersionSummary[]>(`/projects/${id}/versions`),
      request<Reference[]>(`/projects/${id}/documents`),
      request<Run[]>(`/projects/${id}/runs`),
    ]);
    if (selectedRef.current !== id) return null;
    setProject(data);
    setVersions(history);
    setReferences(docs);
    if (history[0]) await loadVersion(id, history[0].id);
    const latest =
      loadRun && runs[0] ? await request<Run>(`/runs/${runs[0].id}`) : null;
    if (latest && selectedRef.current === id) setRun(latest);
    await listProjects();
    return latest;
  }
  async function action(work: () => Promise<void>) {
    setError("");
    setBusy(true);
    try {
      await work();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Local request failed. Retry when ready.",
      );
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    void listProjects().catch(() =>
      setError(
        "Cannot connect to the local backend. Start the application and retry.",
      ),
    );
    void request<{
      status: string;
      model: { model?: string };
      knowledge: { global: number };
    }>("/health")
      .then((data) =>
        setHealth(
          data.status === "ready"
            ? `Local Qwen ready · ${data.knowledge.global} knowledge chunks`
            : "Local model unavailable",
        ),
      )
      .catch(() => setHealth("Local runtime unavailable"));
  }, []);
  useEffect(() => {
    if (selectedId)
      void refresh(selectedId)
        .then((latest) => {
          if (
            selectedRef.current === selectedId &&
            latest?.status === "completed" &&
            latest.kind !== "analyse"
          )
            setTab("document");
        })
        .catch((err) => {
          if (selectedRef.current === selectedId) setError(err.message);
        });
  }, [selectedId]);
  useEffect(() => {
    if (!run || !isActive(run) || !selectedId) return;
    const runId = run.id;
    const id = selectedId;
    let stopped = false;
    let timer: number;
    async function poll() {
      try {
        const latest = await request<Run>(`/runs/${runId}`);
        if (stopped || selectedRef.current !== id) return;
        if (isActive(latest)) {
          setRun(latest);
        } else {
          await refresh(id, false);
          if (stopped || selectedRef.current !== id) return;
          if (latest.status === "completed" && latest.kind !== "analyse")
            setTab("document");
          if (latest.kind === "generate") setClarifications(null);
          setRun(latest);
          setError("");
          return;
        }
      } catch {
        if (!stopped && selectedRef.current === id)
          setError(
            "Waiting to reconnect. The local run keeps its saved progress.",
          );
      }
      if (!stopped) timer = window.setTimeout(poll, 1000);
    }
    timer = window.setTimeout(poll, 1000);
    return () => {
      stopped = true;
      window.clearTimeout(timer);
    };
  }, [run?.id, run?.status, selectedId]);

  function create(event: FormEvent) {
    event.preventDefault();
    void action(async () => {
      const created = await request<Project>("/projects", "POST", {
        name: name.trim() || "Untitled security project",
        description,
      });
      select(created.id);
      setProject(created);
      setName("");
      setDescription("");
      const started = await request<Run>(
        `/projects/${created.id}/analyse`,
        "POST",
      );
      if (selectedRef.current === created.id) setRun(started);
    });
  }
  function analyse() {
    void action(async () => {
      setClarifications(null);
      setRun(await request<Run>(`${base}/analyse`, "POST"));
    });
  }
  function reviewAnalysis() {
    void action(async () => {
      const reviewed = await request<Clarifications>(
        `${base}/clarifications`,
        "POST",
      );
      if (selectedRef.current === selectedId) setClarifications(reviewed);
    });
  }
  function generate(event: FormEvent) {
    event.preventDefault();
    if (!clarifications || disabled || chatBusy) return;
    void action(async () => {
      const submitted = clarifications.questions
        .filter((question) => answers[question.id]?.trim())
        .map((question) => ({
          question_id: question.id,
          text: answers[question.id],
        }));
      const started = await request<Run>(`${base}/generate`, "POST", {
        review_token: clarifications.review_token,
        answers: submitted,
      });
      if (selectedRef.current === selectedId) {
        setRun(started);
        setShowChat(false);
      }
    });
  }
  async function saveReview(
    decision: "approve" | "reject" | "request_changes",
  ) {
    if (!version || !reviewer.trim()) {
      setError("Enter the reviewer name before recording a decision.");
      return;
    }
    await action(async () => {
      await request(`${base}/versions/${version.id}/reviews`, "POST", {
        decision,
        reviewer,
        comment,
        content_hash: version.content_hash,
      });
      setReviews(
        await request<Review[]>(`${base}/versions/${version.id}/reviews`),
      );
      setShowReview(false);
    });
  }
  async function sendChat(event: FormEvent) {
    event.preventDefault();
    if (!chatText.trim() || chatBusy || disabled) return;
    const projectId = selectedId;
    const text = chatText;
    setChatText("");
    setMessages((old) => [...old, { role: "you", text }]);
    setChatBusy(true);
    try {
      const response = await request<{ answer: string; sources: Json[] }>(
        "/chat",
        "POST",
        { message: text, project_id: projectId },
      );
      if (selectedRef.current !== projectId) return;
      setMessages((old) => [
        ...old,
        { role: "assistant", text: response.answer },
      ]);
    } catch (err) {
      if (selectedRef.current !== projectId) return;
      setMessages((old) => [
        ...old,
        {
          role: "assistant",
          text:
            err instanceof Error
              ? err.message
              : "Local answer failed. Please retry.",
        },
      ]);
    } finally {
      setChatBusy(false);
    }
  }

  const analysis: Analysis | null = project?.analysis ?? null;
  const currentAgent = run?.events.at(-1)?.agent;
  const generationSeconds =
    run?.status === "completed" &&
    run.kind === "generate" &&
    run.events.some((event) => event.version_id === version?.id)
      ? (Date.parse(run.updated_at ?? "") - Date.parse(run.created_at ?? "")) /
        1000
      : NaN;
  const shownContent: Json = !version
    ? null
    : section === "quality"
      ? (version.quality as unknown as Json)
      : section === "sources"
        ? version.content.sources
        : section === "evidence"
          ? version.content.evidence
          : section === "provenance"
            ? {
                requested_model: version.content.requested_model_name ?? "",
                actual_models_used: version.content.models_used ?? [],
                section_models: version.content.section_models ?? {},
                prompt_version: version.content.prompt_version ?? "",
              }
            : version.content[section];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button
          className="brand"
          onClick={() => select(null)}
          aria-label="CyberSRS home"
        >
          <span className="brand-mark">
            C<span>↗</span>
          </span>
          <span>
            CyberSRS<small>REQUIREMENTS STUDIO</small>
          </span>
        </button>
        <button className="new-project" onClick={() => select(null)}>
          ＋ New project
        </button>
        <div className="sidebar-label">
          YOUR WORKSPACE <span>{projects.length}</span>
        </div>
        <nav className="project-list" aria-label="Saved projects">
          {projects.map((item) => (
            <button
              key={item.id}
              className={`project-link ${selectedId === item.id ? "selected" : ""}`}
              onClick={() => select(item.id)}
            >
              <span className="project-icon">▤</span>
              <span>
                <strong>{item.name}</strong>
                <small>{new Date(item.updated_at).toLocaleDateString()}</small>
              </span>
            </button>
          ))}
          {!projects.length && (
            <p className="sidebar-empty">
              Your saved projects will appear here.
            </p>
          )}
        </nav>
        <div className="sidebar-bottom">
          <div className="local-notice">
            <span className="status-dot" /> Local workspace
            <small>Inputs and documents stay on this device.</small>
          </div>
        </div>
      </aside>
      <main className="main">
        <header className="topbar">
          <span>
            Workspace <span className="breadcrumb">/</span>{" "}
            {project?.name ?? "New project"}
          </span>
          <span className="runtime">
            <span className="status-dot" />
            {health}
          </span>
        </header>
        {error && (
          <div className="error-banner" role="alert">
            {error}
            <button onClick={() => setError("")} aria-label="Dismiss error">
              ×
            </button>
          </div>
        )}
        {!selectedId ? (
          <section className="welcome">
            <div className="eyebrow">FROM IDEA TO SPECIFICATION</div>
            <h1>
              Clear requirements.
              <br />
              <span>A better starting point.</span>
            </h1>
            <p className="welcome-copy">
              Describe your cybersecurity or networking project. Your local AI
              team will clarify the details, build each SRS section, and
              recommend a development lifecycle.
            </p>
            <form className="create-form" onSubmit={create}>
              <label>
                Project name <span className="muted">optional</span>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  maxLength={200}
                  placeholder="e.g. Campus network access control"
                />
              </label>
              <label>
                What are you building?
                <textarea
                  required
                  minLength={20}
                  maxLength={30000}
                  rows={7}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe the purpose, users, expected behavior, and any constraints you already know…"
                />
              </label>
              <div className="form-footer">
                <span>◇ Local Qwen · Evidence-led generation</span>
                <button
                  className="primary"
                  disabled={busy || description.trim().length < 20}
                >
                  {busy ? "Starting…" : "Analyze project"} <span>↗</span>
                </button>
              </div>
            </form>
          </section>
        ) : !project ? (
          <div className="loading-state">Loading your local project…</div>
        ) : (
          <>
            <div className="workspace-heading">
              <div>
                <div className="eyebrow">
                  {analysis?.domain ?? "PROJECT WORKSPACE"}
                </div>
                <h1>{analysis?.title ?? project.name}</h1>
              </div>
              <div className="workspace-actions">
                <button className="secondary" onClick={() => setTab("gather")}>
                  Project details
                </button>
                {version && (
                  <button
                    className="primary"
                    onClick={() => setTab("document")}
                  >
                    Open specification ↗
                  </button>
                )}
              </div>
            </div>
            <ol className="workflow-steps" aria-label="Workflow steps">
              <li
                aria-current={
                  tab === "gather" && !clarifications && !isActive(run)
                    ? "step"
                    : undefined
                }
              >
                1. Review analysis
              </li>
              <li
                aria-current={
                  tab === "gather" && clarifications && !isActive(run)
                    ? "step"
                    : undefined
                }
              >
                2. Clarify
              </li>
              <li
                aria-current={
                  isActive(run) && run?.kind !== "analyse" ? "step" : undefined
                }
              >
                3. Generate
              </li>
              <li
                aria-current={
                  tab === "document" && !isActive(run) ? "step" : undefined
                }
              >
                4. View and download
              </li>
            </ol>
            {run && (isActive(run) || run.status !== "completed") && (
              <section className="progress-panel" aria-live="polite">
                <div className="panel-heading">
                  <div>
                    <strong>
                      {isActive(run)
                        ? run.kind === "analyse"
                          ? "Analyzing your brief"
                          : "Generating IEEE SRS"
                        : run.status === "cancelled"
                          ? "Run canceled"
                          : "The run ended before completion"}
                    </strong>
                    <p>
                      {isActive(run)
                        ? currentAgent &&
                          `Current step · ${label(currentAgent)}`
                        : run.error === "generation_time_limit"
                          ? "The run reached its time limit. No new PDF was created."
                          : "Your project and completed work are saved."}
                    </p>
                  </div>
                  {isActive(run) && (
                    <button
                      className="secondary"
                      disabled={busy}
                      onClick={() =>
                        void action(async () => {
                          await request(`/runs/${run.id}/cancel`, "POST");
                        })
                      }
                    >
                      Cancel
                    </button>
                  )}
                </div>
                {run.kind !== "analyse" && (
                  <RunTiming
                    run={run}
                    agents={["analysis", ...sections].filter(
                      (agent) =>
                        agent !== "analysis" ||
                        run.events.some((event) => event.agent === agent),
                    )}
                  />
                )}
                {run.error && (
                  <details>
                    <summary>Run diagnostic</summary>
                    <code>{run.error}</code>
                  </details>
                )}
              </section>
            )}
            {tab === "gather"
              ? !isActive(run) && (
                  <div className="workflow-content">
                    <section className="gather-main">
                      <details className="panel">
                        <summary>Your project brief</summary>
                        <div className="panel-heading">
                          <h2>Original brief</h2>
                          <span className="pill">Original input</span>
                        </div>
                        <p className="original-brief">{project.description}</p>
                        <details>
                          <summary>Edit the project brief</summary>
                          <form
                            onSubmit={(e) => {
                              e.preventDefault();
                              const form = new FormData(e.currentTarget);
                              void action(async () => {
                                await request(base, "PATCH", {
                                  name: project.name,
                                  description: String(form.get("description")),
                                });
                                setClarifications(null);
                                setAnswers({});
                                await refresh(project.id);
                                setRun(
                                  await request<Run>(`${base}/analyse`, "POST"),
                                );
                              });
                            }}
                          >
                            <textarea
                              name="description"
                              rows={7}
                              defaultValue={project.description}
                              minLength={20}
                              required
                            />
                            <p className="muted">
                              Changing the brief requires a new analysis and
                              specification. Previous versions remain available.
                            </p>
                            <button className="secondary" disabled={disabled}>
                              Save revised brief
                            </button>
                          </form>
                        </details>
                      </details>
                      {analysis && !clarifications && (
                        <article className="panel">
                          <div className="panel-heading">
                            <h2>Project analysis</h2>
                            <span className="pill">
                              {analysis.supported
                                ? "In scope"
                                : "Unsupported domain"}
                            </span>
                          </div>
                          <p>{analysis.summary}</p>
                          <p>
                            <strong>Domain:</strong> {analysis.domain}
                          </p>
                          {!!analysis.stakeholders?.length && (
                            <p>
                              <strong>People and roles:</strong>{" "}
                              {analysis.stakeholders.join(", ")}
                            </p>
                          )}
                          {!!analysis.assessments?.length && (
                            <details>
                              <summary>What the analysis identified</summary>
                              <ul className="plain-list">
                                {analysis.assessments.map((item, i) => (
                                  <li key={i}>
                                    <strong>{label(item.kind)}:</strong>{" "}
                                    {item.explanation}
                                  </li>
                                ))}
                              </ul>
                            </details>
                          )}
                          {analysis.unresolved_decisions.length > 0 && (
                            <details open>
                              <summary>
                                {analysis.unresolved_decisions.length} decisions
                                to confirm
                              </summary>
                              <ul className="plain-list">
                                {analysis.unresolved_decisions.map(
                                  (item, i) => (
                                    <li key={i}>{item}</li>
                                  ),
                                )}
                              </ul>
                            </details>
                          )}
                          {analysis.supported ? (
                            <button
                              className="primary"
                              disabled={busy}
                              onClick={reviewAnalysis}
                            >
                              Confirm analysis & show questions
                            </button>
                          ) : (
                            <p className="muted">
                              Edit the brief to describe a defensive
                              cybersecurity or networking project.
                            </p>
                          )}
                        </article>
                      )}
                      {analysis && clarifications && (
                        <section
                          className="panel clarification-form"
                          aria-label="Clarifications"
                        >
                          <div className="panel-heading">
                            <h2>Clarify open decisions</h2>
                            <button
                              className="secondary"
                              disabled={disabled}
                              onClick={() => {
                                setClarifications(null);
                                setShowChat(false);
                              }}
                            >
                              Back to analysis
                            </button>
                          </div>
                          <p className="muted">
                            {clarifications.questions.length
                              ? "Answer what you know. Blank answers remain open in the specification."
                              : "The analysis found no further questions. You can generate the specification now."}
                          </p>
                          <button
                            className="secondary"
                            type="button"
                            onClick={() => setShowChat(true)}
                          >
                            Ask about this project
                          </button>
                          <form onSubmit={generate}>
                            {clarifications.questions.map((q, i) => (
                              <label className="question" key={q.id}>
                                <span className="question-title">
                                  <span>{String(i + 1).padStart(2, "0")}</span>
                                  {q.question}
                                </span>
                                <small>{q.why_needed}</small>
                                <textarea
                                  rows={3}
                                  maxLength={12000}
                                  value={answers[q.id] ?? ""}
                                  onChange={(e) =>
                                    setAnswers((old) => ({
                                      ...old,
                                      [q.id]: e.target.value,
                                    }))
                                  }
                                  placeholder="Leave blank to keep this decision open"
                                />
                              </label>
                            ))}
                            <div className="generation-actions">
                              <button
                                className="primary"
                                disabled={disabled || chatBusy}
                              >
                                Generate IEEE SRS
                              </button>
                              <p className="muted">
                                Generation budget · up to 8 minutes
                              </p>
                            </div>
                          </form>
                        </section>
                      )}
                      {!analysis && (
                        <button
                          className="primary"
                          disabled={disabled}
                          onClick={analyse}
                        >
                          Analyze project
                        </button>
                      )}
                    </section>
                    <details className="panel workflow-tools">
                      <summary>Project tools</summary>
                      <article>
                        <h3>Private references</h3>
                        <h3>Bring your evidence.</h3>
                        <p className="muted">
                          Add project policies, existing specifications, or
                          technical notes. These references stay private to this
                          project.
                        </p>
                        <label className="upload-control">
                          ＋ Add a reference
                          <input
                            type="file"
                            accept=".pdf,.txt,.md,.csv"
                            disabled={disabled}
                            onChange={(e) => {
                              const file = e.target.files?.[0];
                              if (file)
                                void action(async () => {
                                  const form = new FormData();
                                  form.append("file", file);
                                  await request(
                                    `${base}/documents`,
                                    "POST",
                                    form,
                                  );
                                  setClarifications(null);
                                  await refresh(project.id);
                                });
                              e.target.value = "";
                            }}
                          />
                        </label>
                        <small className="muted">
                          PDF, TXT, Markdown or CSV · up to 10 MB
                        </small>
                        <ul className="reference-list">
                          {references.map((ref) => (
                            <li key={ref.id}>
                              <span>{ref.name}</span>
                              <button
                                aria-label={`Remove ${ref.name}`}
                                disabled={disabled}
                                onClick={() =>
                                  void action(async () => {
                                    await request(
                                      `${base}/documents/${ref.id}`,
                                      "DELETE",
                                    );
                                    setClarifications(null);
                                    await refresh(project.id);
                                  })
                                }
                              >
                                ×
                              </button>
                            </li>
                          ))}
                        </ul>
                      </article>
                      <article className="assurance">
                        <span>◇</span>
                        <h3>Your decisions stay yours.</h3>
                        <p>
                          Agents draft and cross-check. You review the evidence,
                          resolve open decisions, and approve an exact version.
                        </p>
                        <a href={`/api/v1${base}/audit`} download>
                          Download private project history
                        </a>
                        <small>
                          Includes project inputs and AI drafting history.
                        </small>
                      </article>
                      <button
                        className="danger-text"
                        disabled={disabled}
                        onClick={() => {
                          if (
                            window.confirm(
                              "Delete this project, its references, document versions, and private history?",
                            )
                          )
                            void action(async () => {
                              await request(base, "DELETE");
                              select(null);
                              await listProjects();
                            });
                        }}
                      >
                        Delete project
                      </button>
                    </details>
                  </div>
                )
              : version && (
                  <section className="document-workspace">
                    <div className="document-toolbar">
                      <div>
                        <span
                          className={`pill ${version.quality.status === "invalid" ? "invalid" : approved(reviews, version) ? "approved" : ""}`}
                        >
                          {version.quality.status === "invalid"
                            ? "Invalid draft · validation failed"
                            : approved(reviews, version)
                              ? "Human-approved baseline"
                              : "Draft · human review required"}
                        </span>
                        {Number.isFinite(generationSeconds) && (
                          <span className="muted">
                            Generated in {formatElapsed(generationSeconds)}
                          </span>
                        )}
                        <select
                          aria-label="Document version"
                          value={version.id}
                          onChange={(e) => {
                            if (selectedId)
                              void action(() =>
                                loadVersion(selectedId, e.target.value),
                              );
                          }}
                        >
                          {versions.map((v) => (
                            <option value={v.id} key={v.id}>
                              Version {v.sequence} ·{" "}
                              {new Date(v.created_at).toLocaleString()}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <button
                          className="secondary"
                          onClick={() => setShowReview(!showReview)}
                        >
                          Record review
                        </button>
                        {version.quality.status !== "invalid" && (
                          <a
                            className="primary button-link"
                            href={`/api/v1${base}/versions/${version.id}/export/pdf`}
                            download
                          >
                            Download IEEE SRS PDF
                          </a>
                        )}
                      </div>
                    </div>
                    {showReview && (
                      <form
                        className="panel review-form"
                        onSubmit={(e) => {
                          e.preventDefault();
                          void saveReview("approve");
                        }}
                      >
                        <h3>
                          Record your decision on version {version.sequence}
                        </h3>
                        <p className="muted">
                          Approval records your review of this exact content. A
                          later edit creates a new, unapproved version.
                        </p>
                        <label>
                          Reviewer
                          <input
                            required
                            value={reviewer}
                            onChange={(e) => setReviewer(e.target.value)}
                            maxLength={200}
                          />
                        </label>
                        <label>
                          Review notes
                          <textarea
                            value={comment}
                            onChange={(e) => setComment(e.target.value)}
                            rows={3}
                          />
                        </label>
                        <div className="review-actions">
                          <button className="primary" disabled={disabled}>
                            Approve this version
                          </button>
                          <button
                            type="button"
                            className="secondary"
                            disabled={disabled}
                            onClick={() => void saveReview("request_changes")}
                          >
                            Request changes
                          </button>
                          <button
                            type="button"
                            className="secondary"
                            disabled={disabled}
                            onClick={() => void saveReview("reject")}
                          >
                            Reject
                          </button>
                        </div>
                      </form>
                    )}
                    {version.presentation && (
                      <SRSReport
                        key={version.id}
                        report={version.presentation}
                      />
                    )}
                    <details className="panel workflow-tools">
                      <summary>Review evidence or edit sections</summary>
                      <div className="document-columns">
                        <nav className="section-nav" aria-label="SRS sections">
                          <span className="sidebar-label">
                            DOCUMENT CONTENTS
                          </span>
                          {[
                            ...sections,
                            "evidence",
                            "sources",
                            "quality",
                            "provenance",
                          ].map((key, i) => (
                            <button
                              key={key}
                              className={section === key ? "active" : ""}
                              onClick={() => {
                                setSection(key);
                                setEditValue(undefined);
                              }}
                            >
                              <span>{String(i + 1).padStart(2, "0")}</span>
                              {key === "quality"
                                ? "Quality & traceability"
                                : key === "evidence"
                                  ? "Evidence register"
                                  : key === "sources"
                                    ? "Source references"
                                    : label(key)}
                            </button>
                          ))}
                        </nav>
                        <article className="document-content">
                          <div className="section-title">
                            <div>
                              <div className="eyebrow">
                                VERSION {version.sequence} · SPECIFICATION
                              </div>
                              <h2>
                                {section === "quality"
                                  ? "Quality & traceability"
                                  : label(section)}
                              </h2>
                            </div>
                            {sections.some((key) => key === section) && (
                              <div>
                                <button
                                  className="secondary"
                                  disabled={disabled}
                                  onClick={() => setEditValue(shownContent)}
                                >
                                  Edit section
                                </button>
                                <button
                                  className="text-button"
                                  disabled={disabled}
                                  onClick={() =>
                                    void action(async () => {
                                      setRun(
                                        await request<Run>(
                                          `${base}/versions/${version.id}/regenerate/${section}`,
                                          "POST",
                                        ),
                                      );
                                    })
                                  }
                                >
                                  Regenerate ↻
                                </button>
                              </div>
                            )}
                          </div>
                          {section === "sdlc" && (
                            <div className="sdlc-ranking">
                              <h3>Ranked lifecycle suitability</h3>
                              <p className="muted">
                                Versioned evidence rules produce suitability
                                points. These scores are not probabilities.
                                Missing factors remain open for human review.
                              </p>
                              <StructuredValue
                                value={version.content.sdlc_candidates}
                              />
                              <h3>Evidence behind the recommendation</h3>
                              <p className="muted">
                                Derived factors suggest a delivery approach.
                                They do not confirm release frequency, budget or
                                team capacity.
                              </p>
                              <StructuredValue
                                value={version.content.sdlc_factors}
                              />
                            </div>
                          )}
                          {editValue !== undefined ? (
                            <div className="section-editor">
                              <p className="edit-notice">
                                Your edit creates a successor and rebuilds
                                affected stories, tests, and workflow links.
                                Other requirement sections are preserved.
                              </p>
                              <label>
                                Edit author
                                <select
                                  value={editActor}
                                  onChange={(e) =>
                                    setEditActor(
                                      e.target.value === "assistant"
                                        ? "assistant"
                                        : "human",
                                    )
                                  }
                                >
                                  <option value="human">Human reviewer</option>
                                  <option value="assistant">
                                    Assistant correction
                                  </option>
                                </select>
                              </label>
                              <SectionEditor
                                value={editValue}
                                onChange={setEditValue}
                              />
                              <div className="sticky-actions">
                                <button
                                  className="secondary"
                                  onClick={() => setEditValue(undefined)}
                                >
                                  Discard edit
                                </button>
                                <button
                                  className="primary"
                                  disabled={disabled}
                                  onClick={() =>
                                    void action(async () => {
                                      setRun(
                                        await request<Run>(
                                          `${base}/versions/${version.id}/sections/${section}`,
                                          "PUT",
                                          {
                                            content: editValue,
                                            editor: editActor,
                                            expected_content_hash:
                                              version.content_hash,
                                          },
                                        ),
                                      );
                                      setEditValue(undefined);
                                    })
                                  }
                                >
                                  Save & revalidate
                                </button>
                              </div>
                            </div>
                          ) : (
                            <StructuredValue value={shownContent ?? null} />
                          )}
                        </article>
                      </div>
                    </details>
                    <footer className="document-footer">
                      AI-generated advisory document ·{" "}
                      {version.quality.checks_passed}/
                      {version.quality.checks_total} automated checks passed ·
                      Semantic correctness requires review.
                      <details>
                        <summary>Version fingerprint & review history</summary>
                        <code>{version.content_hash}</code>
                        {reviews.length ? (
                          reviews.map((review) => (
                            <p key={review.id}>
                              {review.reviewer} · {label(review.decision)} ·{" "}
                              {new Date(review.created_at).toLocaleString()}
                              <br />
                              {review.comment}
                            </p>
                          ))
                        ) : (
                          <p>No human decision recorded for this version.</p>
                        )}
                      </details>
                    </footer>
                  </section>
                )}
          </>
        )}
      </main>
      {showChat && (
        <aside
          className="chat-drawer"
          aria-label="Project clarification conversation"
        >
          <header>
            <div>
              <strong>Ask CyberSRS</strong>
              <small>Project clarification</small>
            </div>
            <button
              aria-label="Close conversation"
              onClick={() => setShowChat(false)}
            >
              ×
            </button>
          </header>
          <div className="chat-messages">
            {!messages.length && (
              <p className="muted">
                Ask what a clarification question means or what information you
                need to answer it.
              </p>
            )}
            {messages.map((message, i) => (
              <article className={`chat-message ${message.role}`} key={i}>
                <strong>{message.role === "you" ? "You" : "CyberSRS"}</strong>
                <p>{message.text}</p>
              </article>
            ))}
            {chatBusy && <p className="muted">Preparing a local answer…</p>}
          </div>
          <form onSubmit={(e) => void sendChat(e)}>
            <textarea
              aria-label="Your question"
              value={chatText}
              onChange={(e) => setChatText(e.target.value)}
              rows={3}
              placeholder="Ask about an open decision…"
            />
            <button
              className="primary"
              disabled={disabled || chatBusy || !chatText.trim()}
            >
              Send ↗
            </button>
          </form>
        </aside>
      )}
    </div>
  );
}
