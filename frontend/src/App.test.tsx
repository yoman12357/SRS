import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { approved, isActive, request, Review, Version } from "./api";
import { StructuredValue } from "./StructuredValue";

const project = {
  id: "p-1",
  name: "Campus access control",
  description:
    "Build a campus network that limits guest access to the internet.",
  answers: [],
  analysis: {
    title: "Campus access control",
    domain: "Network access control",
    summary: "Guests can access the internet with explicit network boundaries.",
    supported: true,
    questions: [
      {
        id: "q-1",
        question: "Which roles can modify access policies?",
        why_needed: "We need the exact role permission boundary.",
        critical: true,
      },
    ],
    unresolved_decisions: ["Administrator permissions"],
  },
};

function mockFetch(overrides: Record<string, unknown> = {}) {
  const fake = vi.fn(
    async (input: RequestInfo | URL, options?: RequestInit) => {
      const url = String(input);
      const method = options?.method ?? "GET";
      const routes: Record<string, unknown> = {
        "/api/v1/health": {
          status: "ready",
          model: { model: "local-qwen" },
          knowledge: { global: 111 },
        },
        "/api/v1/projects": [],
        "/api/v1/projects/p-1": project,
        "/api/v1/projects/p-1/versions": [],
        "/api/v1/projects/p-1/documents": [],
        "/api/v1/projects/p-1/runs": [],
        "POST /api/v1/projects": project,
        "POST /api/v1/projects/p-1/analyse": {
          id: "r-1",
          kind: "analyse",
          status: "queued",
          events: [],
          checkpoints: {},
          error: null,
        },
        ...overrides,
      };
      const value = routes[`${method} ${url}`] ?? routes[url];
      return {
        ok: value !== undefined,
        status: value === undefined ? 500 : 200,
        json: async () =>
          value ?? { detail: { message: "Local request failed" } },
      } as Response;
    },
  );
  vi.stubGlobal("fetch", fake);
  return fake;
}

beforeEach(() => {
  localStorage.clear();
  vi.unstubAllGlobals();
});

it.each([
  ["Generate IEEE SRS", "standard"],
  ["Generate Normal SRS", "full"],
])(
  "starts exactly one generation for %s after displaying analysis",
  async (button, preference) => {
    localStorage.setItem("cybersrs.selected", "p-1");
    const fetch = mockFetch({
      "POST /api/v1/projects/p-1/generate": {
        id: "r-generate",
        kind: "generate",
        status: "queued",
        events: [],
        checkpoints: {},
        error: null,
      },
    });
    render(<App />);
    expect(
      await screen.findByRole("heading", { name: "Project analysis" }),
    ).toBeInTheDocument();
    expect(screen.getByText(project.analysis.summary)).toBeInTheDocument();
    expect(screen.getAllByText(project.analysis.domain).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: button }));
    await waitFor(() =>
      expect(
        fetch.mock.calls.filter(
          ([url, options]) =>
            String(url).endsWith("/generate") && options?.method === "POST",
        ),
      ).toHaveLength(1),
    );
    expect(localStorage.getItem("cybersrs.report-format.p-1")).toBe(preference);
  },
);

it("disables both report choices for an unsupported analysis", async () => {
  localStorage.setItem("cybersrs.selected", "p-1");
  const fetch = mockFetch({
    "/api/v1/projects/p-1": {
      ...project,
      analysis: { ...project.analysis, supported: false },
    },
  });
  render(<App />);
  expect(
    await screen.findByRole("button", { name: "Generate IEEE SRS" }),
  ).toBeDisabled();
  expect(
    screen.getByRole("button", { name: "Generate Normal SRS" }),
  ).toBeDisabled();
  expect(
    fetch.mock.calls.some(([, options]) => options?.method === "POST"),
  ).toBe(false);
});

describe("local project workflow", () => {
  it("preserves the exact project input and explicitly starts analysis", async () => {
    const fetch = mockFetch();
    render(<App />);
    const description = screen.getByLabelText("What are you building?");
    fireEvent.change(description, { target: { value: project.description } });
    fireEvent.click(
      screen.getByRole("button", { name: /Understand my project/ }),
    );
    await waitFor(() =>
      expect(
        fetch.mock.calls.some(
          ([url, options]) =>
            String(url).endsWith("/analyse") && options?.method === "POST",
        ),
      ).toBe(true),
    );
    const creation = fetch.mock.calls.find(
      ([url, options]) =>
        String(url) === "/api/v1/projects" && options?.method === "POST",
    );
    expect(JSON.parse(String(creation?.[1]?.body)).description).toBe(
      project.description,
    );
    expect(localStorage.getItem("cybersrs.selected")).toBe("p-1");
  });

  it("shows unanswered decisions and never substitutes assumed answers", async () => {
    localStorage.setItem("cybersrs.selected", "p-1");
    const fetch = mockFetch();
    render(<App />);
    expect(
      await screen.findByText("Which roles can modify access policies?"),
    ).toBeInTheDocument();
    expect(screen.getByText("Administrator permissions")).toBeInTheDocument();
    expect(
      fetch.mock.calls.some(([, options]) => options?.method === "POST"),
    ).toBe(false);
  });

  it("keeps the description available after a failed create request", async () => {
    mockFetch({ "POST /api/v1/projects": undefined });
    render(<App />);
    fireEvent.change(screen.getByLabelText("What are you building?"), {
      target: { value: project.description },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /Understand my project/ }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Local request failed",
    );
    expect(screen.getByLabelText("What are you building?")).toHaveValue(
      project.description,
    );
  });

  it("renders failed runs as incomplete with an explicit retry", async () => {
    localStorage.setItem("cybersrs.selected", "p-1");
    mockFetch({
      "/api/v1/projects/p-1/runs": [
        { id: "r-failed", status: "failed", kind: "generate" },
      ],
      "/api/v1/runs/r-failed": {
        id: "r-failed",
        status: "failed",
        kind: "generate",
        events: [{ agent: "functional", state: "completed" }],
        checkpoints: {},
        error: "section_validation_failed",
      },
    });
    render(<App />);
    expect(
      await screen.findByText("This run needs attention"),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    expect(
      screen.getByText(/No incomplete report was marked successful/),
    ).toBeInTheDocument();
  });

  it("distinguishes finished analysis from a finished specification", async () => {
    localStorage.setItem("cybersrs.selected", "p-1");
    mockFetch({
      "/api/v1/projects/p-1/runs": [
        { id: "r-analysis", kind: "analyse", status: "completed" },
      ],
      "/api/v1/runs/r-analysis": {
        id: "r-analysis",
        kind: "analyse",
        status: "completed",
        error: null,
        events: [{ agent: "analysis", state: "completed" }],
        checkpoints: {},
      },
    });
    render(<App />);
    expect(
      await screen.findByText("Project analysis completed"),
    ).toBeInTheDocument();
    expect(screen.queryByText("Generation completed")).not.toBeInTheDocument();
    expect(
      screen.queryByText(/Your draft is ready for review/),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Generate IEEE SRS" }),
    ).toBeEnabled();
    expect(
      screen.getByRole("button", { name: "Generate Normal SRS" }),
    ).toBeEnabled();
  });
});

it("renders stakeholder and model text without executing HTML", () => {
  render(
    <StructuredValue
      value={{ statement: "<img src=x onerror=alert(1)>", sources: [] }}
    />,
  );
  expect(screen.getByText("<img src=x onerror=alert(1)>")).toBeInTheDocument();
  expect(document.querySelector("img")).toBeNull();
});

it("approval requires the latest explicit decision on the exact content hash", () => {
  const version = {
    content_hash: "hash-a",
    quality: { status: "needs_review" },
  } as Version;
  const review = { decision: "approve", content_hash: "hash-a" } as Review;
  expect(approved([], version)).toBe(false);
  expect(approved([review], version)).toBe(true);
  expect(approved([review], { ...version, content_hash: "hash-b" })).toBe(
    false,
  );
  expect(approved([review, { ...review, decision: "reject" }], version)).toBe(
    false,
  );
});

it("shows failed current validation even if an older review approved that content", async () => {
  localStorage.setItem("cybersrs.selected", "p-1");
  const version = {
    id: "v-1",
    sequence: 1,
    created_at: "2026-10-28T00:00:00Z",
    content_hash: "hash-a",
    content: {
      introduction: {
        summary: "Exact source-linked draft content.",
        items: [],
      },
    },
    quality: {
      status: "invalid",
      checks_passed: 25,
      checks_total: 26,
      findings: [
        {
          code: "risk_rating_without_source_basis",
          severity: "error",
          section: "risks",
          item_id: "RISK-001",
          message: "Risk rating lacks source evidence",
        },
      ],
      traceability: [],
    },
  };
  const fetch = mockFetch({
    "/api/v1/projects/p-1/versions": [version],
    "/api/v1/projects/p-1/versions/v-1": version,
    "/api/v1/projects/p-1/versions/v-1/reviews": [
      { decision: "approve", content_hash: "hash-a" },
    ],
  });
  render(<App />);
  const review = await screen.findByRole("button", {
    name: /Review specification/,
  });
  await waitFor(() => expect(review).toBeEnabled());
  fireEvent.click(review);
  expect(
    await screen.findByText("Invalid draft · validation failed"),
  ).toBeInTheDocument();
  expect(screen.queryByText("Human-approved baseline")).not.toBeInTheDocument();
  expect(
    fetch.mock.calls.some(([, options]) => options?.method === "POST"),
  ).toBe(false);
});

it("distinguishes terminal runs and surfaces safe server errors", async () => {
  expect(isActive({ status: "running" } as never)).toBe(true);
  expect(isActive({ status: "interrupted" } as never)).toBe(false);
  mockFetch();
  await expect(request("/missing")).rejects.toThrow("Local request failed");
});

it("opens the IEEE reader by default and retains the full section editor", async () => {
  localStorage.setItem("cybersrs.selected", "p-1");
  const makeSection = (number: string, title: string) => ({
    number,
    title,
    paragraphs: [],
    bullets: [],
    tables: [],
    requirements: [],
  });
  const version = {
    id: "v-ieee",
    sequence: 1,
    created_at: "2026-10-29T00:00:00Z",
    content_hash: "hash-ieee",
    content: {
      introduction: { summary: "Full canonical introduction.", items: [] },
    },
    presentation: {
      profile: "ieee-830-1998-1.0",
      title: "Campus access control",
      sections: [
        makeSection("1", "Introduction"),
        {
          ...makeSection("1.1", "Purpose"),
          paragraphs: ["Concise IEEE purpose."],
        },
        makeSection("2", "Overall description"),
        makeSection("3", "Specific requirements"),
      ],
    },
    quality: {
      status: "needs_review",
      checks_passed: 1,
      checks_total: 1,
      findings: [],
      traceability: [],
    },
  };
  mockFetch({
    "/api/v1/projects/p-1/versions": [version],
    "/api/v1/projects/p-1/versions/v-ieee": version,
    "/api/v1/projects/p-1/versions/v-ieee/reviews": [],
    "/api/v1/projects/p-1/runs": [
      { id: "r-ieee", kind: "generate", status: "completed" },
    ],
    "/api/v1/runs/r-ieee": {
      id: "r-ieee",
      kind: "generate",
      status: "completed",
      error: null,
      created_at: "2026-10-29T00:00:00Z",
      updated_at: "2026-10-29T00:01:00Z",
      events: [],
      checkpoints: {},
    },
  });
  render(<App />);
  const review = await screen.findByRole("button", {
    name: /Review specification/,
  });
  expect(await screen.findByText("Generation completed")).toBeInTheDocument();
  await waitFor(() => expect(review).toBeEnabled());
  fireEvent.click(review);
  expect(await screen.findByText("Concise IEEE purpose.")).toBeInTheDocument();
  expect(screen.queryByText("Generation completed")).not.toBeInTheDocument();
  expect(
    screen.queryByText("Full canonical introduction."),
  ).not.toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Normal SRS PDF" })).toHaveAttribute(
    "href",
    "/api/v1/projects/p-1/versions/v-ieee/export/pdf?detail=full",
  );
  fireEvent.click(screen.getByRole("button", { name: "Normal SRS & editing" }));
  expect(screen.getByText("Full canonical introduction.")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Edit section" })).toBeEnabled();
  expect(localStorage.getItem("cybersrs.report-format.p-1")).toBe("full");
  expect(screen.getByRole("link", { name: /Export PDF/ })).toHaveAttribute(
    "href",
    "/api/v1/projects/p-1/versions/v-ieee/export/pdf?detail=full",
  );
  expect(screen.getByRole("link", { name: "MARKDOWN" })).toHaveAttribute(
    "href",
    "/api/v1/projects/p-1/versions/v-ieee/export/markdown?detail=full",
  );
  expect(screen.getByRole("link", { name: "JSON" })).toHaveAttribute(
    "href",
    "/api/v1/projects/p-1/versions/v-ieee/export/json",
  );
  fireEvent.click(screen.getByRole("button", { name: "IEEE SRS" }));
  expect(screen.getByRole("link", { name: /Export PDF/ })).toHaveAttribute(
    "href",
    "/api/v1/projects/p-1/versions/v-ieee/export/pdf",
  );
});
