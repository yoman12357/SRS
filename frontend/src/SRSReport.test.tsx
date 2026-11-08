import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SRSPresentation, ReportSection } from "./api";
import { SRSReport } from "./SRSReport";

function section(number: string, title: string): ReportSection {
  return {
    number,
    title,
    paragraphs: [],
    bullets: [],
    tables: [],
    requirements: [],
  };
}
function fixture(): SRSPresentation {
  const roles = section("2.3", "User characteristics and stakeholders");
  roles.tables = [
    {
      columns: ["Role", "Source groups", "Responsibility"],
      rows: [
        [
          "User",
          "students, faculty",
          "Each group retains its own permissions.",
        ],
        [
          "Admin",
          "network administrators",
          "Source-defined policy operations.",
        ],
        [
          "Project Analyst",
          "Document review role",
          "No product access granted.",
        ],
      ],
    },
  ];
  const requirements = section("3.2", "Functional requirements");
  requirements.requirements = [
    {
      id: "FR-001",
      statement: "The system shall enforce the stated access permissions.",
      priority: "must",
      basis: "explicit",
      sources: [],
      evidence_ids: ["E-001"],
      test_ids: ["TEST-001"],
    },
  ];
  return {
    profile: "ieee-830-1998-1.0",
    title: "University access",
    sections: [
      section("1", "Introduction"),
      section("2", "Overall description"),
      roles,
      section("3", "Specific requirements"),
      requirements,
    ],
  };
}

describe("IEEE SRS reader", () => {
  it("shows simple stakeholders in the numbered overall description", () => {
    render(<SRSReport report={fixture()} />);
    fireEvent.click(
      screen.getByRole("button", { name: "2. Overall description" }),
    );
    expect(
      screen.getByRole("heading", {
        name: "2.3 User characteristics and stakeholders",
      }),
    ).toBeInTheDocument();
    for (const role of ["User", "Admin", "Project Analyst"])
      expect(screen.getByRole("cell", { name: role })).toBeInTheDocument();
    expect(screen.getByText("No product access granted.")).toBeInTheDocument();
  });
  it("renders exact requirements with source/test links and no internal field dump", () => {
    render(<SRSReport report={fixture()} />);
    fireEvent.click(
      screen.getByRole("button", { name: "3. Specific requirements" }),
    );
    expect(
      screen.getByText(
        "The system shall enforce the stated access permissions.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Traceability: E-001, TEST-001"),
    ).toBeInTheDocument();
    expect(screen.queryByText("Acceptance criteria")).not.toBeInTheDocument();
  });
  it("escapes source-looking HTML without mutating its report", () => {
    const report = fixture();
    report.sections[0].paragraphs = ["<img src=x onerror=alert(1)>"];
    const before = JSON.stringify(report);
    render(<SRSReport report={report} />);
    expect(
      screen.getByText("<img src=x onerror=alert(1)>"),
    ).toBeInTheDocument();
    expect(document.querySelector("img")).toBeNull();
    expect(JSON.stringify(report)).toBe(before);
  });
});
