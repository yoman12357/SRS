import { Json, label } from "./api";

const choices: Record<string, string[]> = {
  priority: ["must", "should", "could"],
  basis: ["explicit", "derived", "proposed"],
  status: ["confirmed", "proposed", "unresolved"],
  method: ["test", "inspection", "analysis", "demonstration"],
  likelihood: ["low", "medium", "high", "unknown"],
  impact: ["low", "medium", "high", "unknown"],
};

export function SectionEditor({
  value,
  onChange,
  field = "",
}: {
  value: Json;
  onChange: (value: Json) => void;
  field?: string;
}) {
  if (value === null) return <span className="muted">Not specified</span>;
  if (typeof value === "boolean")
    return (
      <input
        type="checkbox"
        checked={value}
        onChange={(e) => onChange(e.target.checked)}
        aria-label={label(field)}
      />
    );
  if (typeof value === "number")
    return (
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-label={label(field)}
      />
    );
  if (typeof value === "string") {
    if (field === "id") return <code>{value}</code>;
    if (choices[field]?.includes(value))
      return (
        <select
          aria-label={label(field)}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        >
          {choices[field].map((option) => (
            <option key={option}>{option}</option>
          ))}
        </select>
      );
    return (
      <textarea
        aria-label={label(field)}
        value={value}
        rows={value.length > 100 ? 3 : 2}
        onChange={(e) => onChange(e.target.value)}
      />
    );
  }
  if (Array.isArray(value))
    return (
      <div className="editor-array">
        {value.map((entry, index) => (
          <div className="editor-entry" key={index}>
            <SectionEditor
              value={entry}
              field={field}
              onChange={(next) =>
                onChange(value.map((old, i) => (i === index ? next : old)))
              }
            />
          </div>
        ))}
        {value.every((item) => typeof item === "string") && (
          <button
            type="button"
            className="text-button"
            onClick={() => onChange([...value, ""])}
          >
            + Add entry
          </button>
        )}
      </div>
    );
  return (
    <div className="editor-object">
      {Object.entries(value).map(([key, entry]) => (
        <label className="editor-field" key={key}>
          <span>{label(key)}</span>
          <SectionEditor
            field={key}
            value={entry}
            onChange={(next) => onChange({ ...value, [key]: next })}
          />
        </label>
      ))}
    </div>
  );
}
