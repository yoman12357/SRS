import { useState } from "react";
import { SRSPresentation } from "./api";

export function SRSReport({ report }: { report: SRSPresentation }) {
  const [part, setPart] = useState("1");
  const groups = report.sections.filter(
    (section) => !section.number.includes("."),
  );
  const visible = report.sections.filter(
    (section) => section.number.split(".")[0] === part,
  );
  return (
    <div className="ieee-report">
      <nav aria-label="IEEE SRS sections" className="ieee-navigation">
        <span className="sidebar-label">IEEE 830-1998</span>
        {groups.map((section) => (
          <button
            key={section.number}
            className={part === section.number ? "active" : ""}
            aria-current={part === section.number ? "page" : undefined}
            onClick={() => setPart(section.number)}
          >
            {section.number}. {section.title}
          </button>
        ))}
      </nav>
      <article className="ieee-body" aria-label="Readable SRS">
        {visible.map((section) => (
          <section className="ieee-section" key={section.number}>
            {section.number === part ? (
              <h2>
                {section.number}. {section.title}
              </h2>
            ) : (
              <h3>
                {section.number} {section.title}
              </h3>
            )}
            {section.paragraphs.map((text, index) => (
              <p key={index}>{text}</p>
            ))}
            {!!section.bullets.length && (
              <ul>
                {section.bullets.map((text, index) => (
                  <li key={index}>{text}</li>
                ))}
              </ul>
            )}
            {section.tables.map((table, index) => (
              <div className="ieee-table-wrap" key={index}>
                <table>
                  <thead>
                    <tr>
                      {table.columns.map((column, index) => (
                        <th scope="col" key={index}>
                          {column}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {table.rows.map((row, index) => (
                      <tr key={index}>
                        {row.map((cell, index) => (
                          <td key={index}>{cell}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
            {section.requirements.map((row, index) => (
              <div className="ieee-requirement" key={`${row.id}-${index}`}>
                <div>
                  <strong>{row.id}</strong>
                  <span>
                    {row.priority} · {row.basis}
                  </span>
                </div>
                <p>{row.statement}</p>
                <p className="ieee-citation">
                  Traceability:{" "}
                  {[...row.evidence_ids, ...row.test_ids].join(", ")}
                </p>
                {row.sources.map((source, index) => (
                  <p className="ieee-citation" key={index}>
                    Source {source.chunk_id}: {source.quote}
                  </p>
                ))}
              </div>
            ))}
          </section>
        ))}
      </article>
    </div>
  );
}
