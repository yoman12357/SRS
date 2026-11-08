import { FormEvent, useEffect, useRef, useState } from "react";
import {
  Analysis,
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
import { CheckpointReview } from "./CheckpointReview";
import { StructuredValue } from "./StructuredValue";
import { RunTiming } from "./RunTiming";
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
  const [reportView, setReportView] = useState<"standard" | "full">("standard");
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

  function chooseReport(view: "standard" | "full") {
    setReportView(view);
    if (selectedId)
      localStorage.setItem(`cybersrs.report-format.${selectedId}`, view);
  }

  function generateReport(view: "standard" | "full") {
    chooseReport(view);
    begin("generate");
  }

  async function listProjects() {
    setProjects(await request<Summary[]>("/projects"));
  }
  function select(id: string | null) {
    selectedRef.current = id;
    setSelectedId(id);
    setError("");
    setEditValue(undefined);
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
  async function refresh(id: string) {
    const [data, history, docs, runs] = await Promise.all([
      request<Project>(`/projects/${id}`),
      request<VersionSummary[]>(`/projects/${id}/versions`),
      request<Reference[]>(`/projects/${id}/documents`),
      request<Run[]>(`/projects/${id}/runs`),
    ]);
    if (selectedRef.current !== id) return;
    setProject(data);
    setVersions(history);
    setReferences(docs);
    if (history[0]) await loadVersion(id, history[0].id);
    if (runs[0]) {
      const active = await request<Run>(`/runs/${runs[0].id}`);
      if (selectedRef.current === id) setRun(active);
    }
    await listProjects();
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
    setProject(null);
    setVersion(null);
    setReviews([]);
    setVersions([]);
    setRun(null);
    setReferences([]);
    setAnswers({});
    setTab("gather");
    setReportView(
      selectedId &&
        localStorage.getItem(`cybersrs.report-format.${selectedId}`) === "full"
        ? "full"
        : "standard",
    );
    if (selectedId)
      void refresh(selectedId).catch((err) => setError(err.message));
  }, [selectedId]);
  useEffect(() => {
    if (!run || !isActive(run)) return;
    const runId = run.id;
    const id = selectedId;
    let stopped = false;
    const timer = window.setInterval(() => {
      void request<Run>(`/runs/${runId}`)
        .then(async (latest) => {
          if (stopped || selectedRef.current !== id) return;
          setRun(latest);
          if (!isActive(latest) && id) {
            await refresh(id);
            if (latest.status === "completed" && latest.kind !== "analyse")
              setTab("document");
          }
        })
        .catch(() => {
          if (!stopped)
            setError(
              "Progress connection interrupted. Refresh to resume; your project is stored locally.",
            );
        });
    }, 1800);
    return () => {
      stopped = true;
      window.clearInterval(timer);
    };
  }, [run?.id, run?.status, selectedId]);

  function create(event: FormEvent) {
    event.preventDefault();
    void action(async () => {
      const created = await request<Project>("/projects", "POST", {
        name: name.trim() || "Untitled security project",
        description,
      });
      const started = await request<Run>(
        `/projects/${created.id}/analyse`,
        "POST",
      );
      select(created.id);
      setProject(created);
      setRun(started);
      setName("");
      setDescription("");
    });
  }
  function begin(kind: "analyse" | "generate") {
    void action(async () => {
      setRun(await request<Run>(`${base}/${kind}`, "POST"));
    });
  }
  function submitAnswers(event: FormEvent) {
    event.preventDefault();
    void action(async () => {
      const submitted =
        project?.analysis?.questions.map((q) => ({
          question_id: q.id,
          text: answers[q.id] ?? "",
          skipped: !(answers[q.id] ?? "").trim(),
        })) ?? [];
      setRun(
        await request<Run>(`${base}/answers`, "POST", { answers: submitted }),
      );
      setAnswers({});
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
    if (!chatText.trim() || chatBusy) return;
    const text = chatText;
    setChatText("");
    setMessages((old) => [...old, { role: "you", text }]);
    setChatBusy(true);
    try {
      const response = await request<{ answer: string; sources: Json[] }>(
        "/chat",
        "POST",
        { message: text, project_id: selectedId },
      );
      setMessages((old) => [
        ...old,
        { role: "assistant", text: response.answer },
      ]);
    } catch (err) {
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
  const progress = Object.fromEntries(
    (run?.events ?? []).map((event) => [event.agent, event.state]),
  );
  const currentAgent = run?.events.at(-1)?.agent;
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
          <button
            className="chat-toggle"
            onClick={() => setShowChat(!showChat)}
          >
            ◇ Ask a cybersecurity question
          </button>
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
                  {busy ? "Starting…" : "Understand my project"} <span>↗</span>
                </button>
              </div>
            </form>
            <div className="feature-row">
              <div>
                <span>01</span>
                <strong>Clarify the essentials</strong>
                <p>Questions that respond to your project.</p>
              </div>
              <div>
                <span>02</span>
                <strong>Build section by section</strong>
                <p>Specialists work in a shared sequence.</p>
              </div>
              <div>
                <span>03</span>
                <strong>Review and export</strong>
                <p>Traceable SRS, SDLC workflow, and PDF.</p>
              </div>
            </div>
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
            <div className="workflow-tabs">
              <button
                className={tab === "gather" ? "active" : ""}
                onClick={() => setTab("gather")}
              >
                01 <span>Gather & clarify</span>
              </button>
              <span className="tab-line" />
              <button
                className={tab === "document" ? "active" : ""}
                disabled={!version}
                onClick={() => setTab("document")}
              >
                02 <span>Review specification</span>
              </button>
              <span className="tab-line" />
              <span className="tab-final">
                03 <span>Approve & export</span>
              </span>
            </div>
            {run &&
              !(
                tab === "document" &&
                version?.presentation &&
                run.status === "completed"
              ) &&
              (isActive(run) ||
                run.status === "failed" ||
                run.status === "cancelled" ||
                run.status === "interrupted" ||
                run.status === "completed") && (
                <section className="progress-panel" aria-live="polite">
                  <div className="panel-heading">
                    <div>
                      <span
                        className={
                          isActive(run)
                            ? "pulse status-dot"
                            : "status-dot warning"
                        }
                      />
                      <strong>
                        {isActive(run)
                          ? `Working on ${label(currentAgent ?? "analysis").toLowerCase()}`
                          : run.status === "failed"
                            ? "This run needs attention"
                            : run.status === "completed"
                              ? run.kind === "analyse"
                                ? "Project analysis completed"
                                : "Generation completed"
                              : `Run ${run.status}`}
                      </strong>
                      <p>
                        {isActive(run)
                          ? "Each specialist uses validated context from the previous steps."
                          : run.status === "completed"
                            ? run.kind === "analyse"
                              ? "Analysis finished. Review the project understanding below."
                              : "Finished section times are shown below. Your draft is ready for review."
                            : "Completed sections are stored. No incomplete report was marked successful."}
                      </p>
                    </div>
                    {isActive(run) ? (
                      <button
                        className="secondary"
                        onClick={() =>
                          void action(async () => {
                            setRun(
                              await request<Run>(
                                `/runs/${run.id}/cancel`,
                                "POST",
                              ),
                            );
                          })
                        }
                      >
                        Cancel generation
                      </button>
                    ) : run.status !== "completed" ? (
                      <button
                        className="secondary"
                        disabled={busy}
                        onClick={() =>
                          void action(async () => {
                            setRun(
                              await request<Run>(
                                `/runs/${run.id}/retry`,
                                "POST",
                              ),
                            );
                          })
                        }
                      >
                        Retry
                      </button>
                    ) : null}
                  </div>
                  <RunTiming
                    run={run}
                    agents={run.kind === "analyse" ? ["analysis"] : sections}
                  />
                  <div className="agent-grid">
                    {(run.kind === "analyse" ? ["analysis"] : sections).map(
                      (agent, i) => (
                        <div
                          className={`agent-step ${progress[agent] ?? "pending"}`}
                          key={agent}
                        >
                          <span>
                            {progress[agent] === "completed"
                              ? "✓"
                              : String(i + 1).padStart(2, "0")}
                          </span>
                          {label(agent)}
                        </div>
                      ),
                    )}
                  </div>
                  {run.error && (
                    <details>
                      <summary>Run diagnostic</summary>
                      <code>{run.error}</code>
                    </details>
                  )}
                  {!isActive(run) &&
                    run.status !== "completed" &&
                    run.kind === "generate" && (
                      <CheckpointReview
                        key={run.id}
                        run={run}
                        disabled={busy}
                        onRetry={(edits) =>
                          void action(async () => {
                            setRun(
                              await request<Run>(
                                `/runs/${run.id}/retry`,
                                "POST",
                                {
                                  section_edits: edits,
                                  expected_input_hash: run.input_hash,
                                  editor: "human",
                                },
                              ),
                            );
                          })
                        }
                      />
                    )}
                </section>
              )}
            {tab === "gather" ? (
              <div className="gather-layout">
                <section className="gather-main">
                  <article className="panel">
                    <div className="panel-heading">
                      <h2>Your project brief</h2>
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
                            await refresh(project.id);
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
                  </article>
                  {analysis && (
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
                            {analysis.unresolved_decisions.length} decisions to
                            confirm
                          </summary>
                          <ul className="plain-list">
                            {analysis.unresolved_decisions.map((item, i) => (
                              <li key={i}>{item}</li>
                            ))}
                          </ul>
                        </details>
                      )}
                    </article>
                  )}
                  {analysis && analysis.questions.length > 0 && (
                    <form
                      className="panel clarification-form"
                      onSubmit={submitAnswers}
                    >
                      <div className="eyebrow">LET'S FILL THE GAPS</div>
                      <h2>A few details will make this stronger.</h2>
                      <p className="muted">
                        Answer what you know. Empty responses stay unresolved
                        and will not become assumptions.
                      </p>
                      {analysis.questions.map((q, i) => (
                        <label className="question" key={q.id}>
                          <span className="question-title">
                            <span>{String(i + 1).padStart(2, "0")}</span>
                            {q.question}
                            {q.critical && <small>Key decision</small>}
                          </span>
                          <small>{q.why_needed}</small>
                          <textarea
                            rows={3}
                            value={answers[q.id] ?? ""}
                            onChange={(e) =>
                              setAnswers((old) => ({
                                ...old,
                                [q.id]: e.target.value,
                              }))
                            }
                            placeholder="Your answer, or leave open for review…"
                          />
                        </label>
                      ))}
                      <button className="primary" disabled={disabled}>
                        Save answers & reassess ↗
                      </button>
                    </form>
                  )}
                  <div className="generation-actions">
                    {!analysis ? (
                      <button
                        className="primary"
                        disabled={disabled}
                        onClick={() => begin("analyse")}
                      >
                        Analyse project ↗
                      </button>
                    ) : (
                      <>
                        <button
                          className="secondary"
                          disabled={disabled}
                          onClick={() => begin("analyse")}
                        >
                          Reanalyse
                        </button>
                        <button
                          className="primary"
                          disabled={disabled || !analysis.supported}
                          onClick={() => generateReport("standard")}
                        >
                          Generate IEEE SRS
                        </button>
                        <button
                          className="primary"
                          disabled={disabled || !analysis.supported}
                          onClick={() => generateReport("full")}
                        >
                          Generate Normal SRS
                        </button>
                        <p className="muted">
                          Both include threats, risks and SDLC. IEEE uses a
                          numbered specification with appendices; Normal shows
                          all sections in sequence.
                        </p>
                      </>
                    )}
                  </div>
                </section>
                <aside className="gather-aside">
                  <article className="panel">
                    <div className="eyebrow">REFERENCE MATERIAL</div>
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
                              await request(`${base}/documents`, "POST", form);
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
                </aside>
              </div>
            ) : (
              version && (
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
                      {["json", "markdown", "pdf"].map((format) => (
                        <a
                          className={
                            format === "pdf"
                              ? "primary button-link"
                              : "secondary button-link"
                          }
                          key={format}
                          href={`/api/v1${base}/versions/${version.id}/export/${format}${
                            reportView === "full" && format !== "json"
                              ? "?detail=full"
                              : ""
                          }`}
                          download
                        >
                          {format === "pdf"
                            ? "↓ Export PDF"
                            : format.toUpperCase()}
                        </a>
                      ))}
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
                    <div className="report-switcher">
                      <div role="group" aria-label="Report view">
                        <button
                          className={reportView === "standard" ? "active" : ""}
                          onClick={() => chooseReport("standard")}
                        >
                          IEEE SRS
                        </button>
                        <button
                          className={reportView === "full" ? "active" : ""}
                          onClick={() => chooseReport("full")}
                        >
                          Normal SRS & editing
                        </button>
                      </div>
                      <a
                        href={`/api/v1${base}/versions/${version.id}/export/pdf?detail=full`}
                        download
                      >
                        Normal SRS PDF
                      </a>
                    </div>
                  )}
                  {version.presentation && reportView === "standard" ? (
                    <SRSReport report={version.presentation} />
                  ) : (
                    <div className="document-columns">
                      <nav className="section-nav" aria-label="SRS sections">
                        <span className="sidebar-label">DOCUMENT CONTENTS</span>
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
                              Derived factors suggest a delivery approach. They
                              do not confirm release frequency, budget or team
                              capacity.
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
                              affected stories, tests, and workflow links. Other
                              requirement sections are preserved.
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
                  )}
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
              )
            )}
          </>
        )}
      </main>
      {showChat && (
        <aside className="chat-drawer" aria-label="Cybersecurity conversation">
          <header>
            <div>
              <strong>Ask CyberSRS</strong>
              <small>Local cybersecurity assistant</small>
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
                Ask about a security concept or your project references. This
                conversation will not start a specification.
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
              aria-label="Cybersecurity question"
              value={chatText}
              onChange={(e) => setChatText(e.target.value)}
              rows={3}
              placeholder="Ask a cybersecurity question…"
            />
            <button className="primary" disabled={chatBusy || !chatText.trim()}>
              Send ↗
            </button>
          </form>
        </aside>
      )}
    </div>
  );
}
