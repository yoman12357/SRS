import { Json, label } from "./api";

export function StructuredValue({
  value,
  depth = 0,
}: {
  value: Json;
  depth?: number;
}) {
  if (value === null) return <span className="muted">Not specified</span>;
  if (typeof value === "boolean") return <span>{value ? "Yes" : "No"}</span>;
  if (typeof value !== "object")
    return <p className="text-value">{String(value)}</p>;
  if (Array.isArray(value)) {
    if (!value.length)
      return <span className="muted empty-value">None recorded</span>;
    if (value.every((v) => typeof v !== "object" || v === null))
      return (
        <ul className="plain-list">
          {value.map((item, i) => (
            <li key={i}>{String(item ?? "Not specified")}</li>
          ))}
        </ul>
      );
    return (
      <div className="object-list">
        {value.map((item, i) => (
          <div className={depth < 3 ? "artifact-card" : "nested-item"} key={i}>
            <StructuredValue value={item} depth={depth + 1} />
          </div>
        ))}
      </div>
    );
  }
  return (
    <dl className="structured-fields">
      {Object.entries(value)
        .filter(([key, item]) => !(key === "id" && item === ""))
        .map(([key, item]) => (
          <div className={`field field-${key}`} key={key}>
            <dt>{label(key)}</dt>
            <dd>
              <StructuredValue value={item} depth={depth + 1} />
            </dd>
          </div>
        ))}
    </dl>
  );
}
