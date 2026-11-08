import { useState } from "react";
import { Json, label, Run, sections } from "./api";
import { SectionEditor } from "./SectionEditor";

export function CheckpointReview({
  run,
  disabled,
  onRetry,
}: {
  run: Run;
  disabled: boolean;
  onRetry: (edits: Record<string, Json>) => void;
}) {
  const saved = sections.filter((name) => run.checkpoints[name]);
  const [selected, setSelected] = useState<string>(saved[0] ?? "");
  const [edits, setEdits] = useState<Record<string, Json>>({});
  if (!saved.length || !run.input_hash) return null;
  return (
    <details>
      <summary>Review saved sections before retry</summary>
      <p>
        Correct a saved section against your original brief. Later sections will
        be rebuilt using your edits. This does not approve the document.
      </p>
      <label>
        Saved section
        <select value={selected} onChange={(e) => setSelected(e.target.value)}>
          {saved.map((name) => (
            <option key={name} value={name}>
              {label(name)}
            </option>
          ))}
        </select>
      </label>
      <SectionEditor
        value={edits[selected] ?? run.checkpoints[selected]}
        onChange={(value) => setEdits((old) => ({ ...old, [selected]: value }))}
      />
      <p>{Object.keys(edits).length} sections changed</p>
      <button
        className="secondary"
        disabled={disabled || !Object.keys(edits).length}
        onClick={() => onRetry(edits)}
      >
        Retry with reviewed edits
      </button>
    </details>
  );
}
