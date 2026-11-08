import { useEffect, useState } from "react";
import { isActive, label, Run } from "./api";

export function formatElapsed(seconds: number): string {
  const value = Math.max(0, Math.floor(seconds));
  return `${Math.floor(value / 60)}:${String(value % 60).padStart(2, "0")}`;
}

export function sectionSeconds(
  run: Run,
  agent: string,
  now: number,
): number | null {
  const events = run.events.filter((event) => event.agent === agent);
  const completed = [...events]
    .reverse()
    .find((event) => event.state === "completed");
  if (completed?.reused) return 0;
  const started = [...events]
    .reverse()
    .find((event) => event.state === "running");
  if (!started?.at) return completed?.elapsed_seconds ?? null;
  const end = completed?.at ?? (!isActive(run) ? run.updated_at : undefined);
  const duration =
    ((end ? Date.parse(end) : now) - Date.parse(started.at)) / 1000;
  return Number.isFinite(duration) ? Math.max(0, duration) : null;
}

export function RunTiming({
  run,
  agents,
}: {
  run: Run;
  agents: readonly string[];
}) {
  const [now, setNow] = useState(Date.now);
  useEffect(() => {
    if (!isActive(run)) return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [run.id, run.status]);
  const end = isActive(run) ? now : Date.parse(run.updated_at ?? "");
  const total = (end - Date.parse(run.created_at ?? "")) / 1000;
  return (
    <div className="run-timing" aria-label="Generation timing">
      <strong>
        Total elapsed: {Number.isFinite(total) ? formatElapsed(total) : "—"}
      </strong>
      {run.budget_seconds != null && (
        <span> · Total limit: {formatElapsed(run.budget_seconds)}</span>
      )}
      <div className="section-timings">
        {agents.map((agent) => {
          const seconds = sectionSeconds(run, agent, now);
          const reused = run.events.some(
            (e) => e.agent === agent && e.state === "completed" && e.reused,
          );
          return (
            <span key={agent}>
              {label(agent)}:{" "}
              {reused
                ? "reused"
                : seconds === null
                  ? "waiting"
                  : formatElapsed(seconds)}
            </span>
          );
        })}
      </div>
    </div>
  );
}
