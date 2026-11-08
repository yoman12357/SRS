import { act, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { Run } from "./api";
import { formatElapsed, RunTiming, sectionSeconds } from "./RunTiming";

const run: Run = {
  id: "timed", kind: "generate", status: "running", error: null, checkpoints: {},
  created_at: "2026-10-29T00:00:00Z", updated_at: "2026-10-29T00:00:30Z",
  events: [
    {agent: "introduction", state: "completed", reused: true, at: "2026-10-29T00:00:01Z"},
    {agent: "functional", state: "running", at: "2026-10-29T00:00:02Z"},
  ],
};
afterEach(() => vi.useRealTimers());

it("ticks from persisted section timestamps and labels reused checkpoints", () => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2026-10-29T00:00:30Z"));
  render(<RunTiming run={run} agents={["introduction", "functional", "security"]} />);
  expect(screen.getByText("Total elapsed: 0:30")).toBeInTheDocument();
  expect(screen.getByText("Functional requirements: 0:28")).toBeInTheDocument();
  expect(screen.getByText("Introduction: reused")).toBeInTheDocument();
  act(() => vi.advanceTimersByTime(2000));
  expect(screen.getByText("Functional requirements: 0:30")).toBeInTheDocument();
});

it("freezes failed/cancelled times and uses actual completion timestamps", () => {
  expect(sectionSeconds({...run, status: "failed"}, "functional", Date.now())).toBe(28);
  const completed = {...run, status: "completed", events: [...run.events,
    {agent: "functional", state: "completed", at: "2026-10-29T00:00:22Z"}]};
  expect(sectionSeconds(completed, "functional", Date.now())).toBe(20);
  expect(sectionSeconds(run, "security", Date.now())).toBeNull();
  expect(formatElapsed(65)).toBe("1:05");
});
