# Secure Access Control and Network Monitoring for University Research Laboratories

Software Requirements Specification

IEEE 830-1998 outline

DRAFT — human review required

Version 1 | 2026-10-29T10:08:40.747439+00:00

## Contents

- 1 Introduction
- 1.1 Purpose
- 1.2 Scope
- 1.3 Definitions, acronyms and abbreviations
- 1.4 References
- 1.5 Overview
- 2 Overall description
- 2.1 Product perspective
- 2.2 Product functions
- 2.3 User characteristics and stakeholders
- 2.4 Constraints
- 2.5 Assumptions and dependencies
- 3 Specific requirements
- 3.1 External interface requirements
- 3.1.1 User interfaces
- 3.1.2 Hardware interfaces
- 3.1.3 Software interfaces
- 3.1.4 Communications interfaces
- 3.2 Functional requirements
- 3.3 Performance requirements
- 3.4 Logical database requirements
- 3.5 Design constraints
- 3.6 Software system attributes
- 3.6.1 Reliability
- 3.6.2 Availability
- 3.6.3 Security
- 3.6.4 Maintainability
- 3.6.5 Portability
- 3.7 Other requirements

## 1 Introduction


### 1.1 Purpose

This specification records the project purpose, stakeholder constraints and unresolved decisions stated in the source evidence below.

This SRS describes the software's required behavior for users, administrators and the Project Analyst reviewing the specification.


### 1.2 Scope

Design a secure access-control and network-monitoring system for university research laboratories containing sensitive equipment and research data. The system should allow only authorized students, faculty, researchers, and lab administrators to access designated lab networks and systems based on role and approved permissions. Administrative users should be able to grant or revoke access, review active sessions, monitor unusual login activity, and receive alerts for repeated failed authentication, unauthorized access attempts, and access outside approved lab hours. The system should maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices. The solution should be secure, reliable, and manageable across multiple research buildings.


### 1.3 Definitions, acronyms and abbreviations


| Term | Meaning |
| --- | --- |
| Access control | Rules and enforcement governing which principals may perform actions on resources. |
| Audit record | A stored record of an event. Required event scope and retention are determined by the linked source, not this definition. |
| Log | A collection of event records. This term does not itself require additional logging fields, events or access permissions. |
| Device isolation | Restriction of a device's network access; the source determines whether and by whom this action is permitted. |

### 1.4 References


| Reference | Source |
| --- | --- |
| Format | IEEE Std 830-1998, clauses 5 and Annex A (document organization). |

### 1.5 Overview

Section 2 summarizes the product, stakeholders and open decisions. Section 3 contains the uniquely identified requirements. Detailed evidence, acceptance procedures and the SDLC plan are available in the supporting report.


## 2 Overall description


### 2.1 Product perspective

Design a secure access-control and network-monitoring system for university research laboratories containing sensitive equipment and research data.


### 2.2 Product functions

Functional topics are summarized below; section 3 retains the full requirements.

- Access permissions — FR-001, FR-002, FR-003
- Authentication — FR-003
- Monitoring and alerts — FR-001, FR-003
- The solution should be secure, reliable, and manageable across multiple research buildings. — FR-004

### 2.3 User characteristics and stakeholders

Labels group stakeholders for readability. They do not combine permissions.

Education, training and experience requirements remain unspecified.


| Role | Source user groups | Responsibility |
| --- | --- | --- |
| User | students, faculty, researchers, guest | Uses permitted functions; each source class keeps its specified permissions. |
| Admin | lab administrators, Administrative users, administrator | Performs only the role's source-defined operations in section 3. |
| Project Analyst | Document review role | Reviews requirements and tracks open decisions; this role grants no product access. |

### 2.4 Constraints

No additional implementation constraints were confirmed. Source-defined restrictions remain in the requirements in section 3.


### 2.5 Assumptions and dependencies

Open decisions requiring confirmation:

- Thresholds for what constitutes unusual login activity
- Definition of 'approved research device' and how it is validated

## 3 Specific requirements

Each requirement is stated once with its original identifier and wording. Cross-references identify requirements covering more than one concern.


### 3.1 External interface requirements


#### 3.1.1 User interfaces

Related requirements: FR-003. Interface details beyond those requirements remain unspecified.


#### 3.1.2 Hardware interfaces

Related requirements: FR-001, SEC-001. Interface details beyond those requirements remain unspecified.


#### 3.1.3 Software interfaces

Related requirements: FR-003. Interface details beyond those requirements remain unspecified.


#### 3.1.4 Communications interfaces

Related requirements: FR-001, FR-002, SEC-001. Interface details beyond those requirements remain unspecified.


### 3.2 Functional requirements


**FR-001** · Must · explicit

The system shall provide secure access-control and network-monitoring capabilities for university research laboratories containing sensitive equipment and research data.

Traceability: E-001, TEST-001

**FR-002** · Should · explicit

The system shall allow only authorized students, faculty, researchers, and lab administrators to access designated lab networks and systems based on role and approved permissions.

Traceability: E-002, TEST-002

**FR-003** · Should · explicit

Administrative users should be able to grant or revoke access, review active sessions, monitor unusual login activity, and receive alerts for repeated failed authentication, unauthorized access attempts, and access outside approved lab hours.

Traceability: E-003, TEST-003, TEST-004, TEST-005

**FR-004** · Should · explicit

The solution should be secure, reliable, and manageable across multiple research buildings.

Traceability: E-005, TEST-006

### 3.3 Performance requirements

No separate requirement was specified in the supplied brief.


### 3.4 Logical database requirements

No separate requirement was specified in the supplied brief.


### 3.5 Design constraints

No separate requirement was specified in the supplied brief.


### 3.6 Software system attributes


#### 3.6.1 Reliability

Also covered by: FR-004.


#### 3.6.2 Availability

No separate requirement was specified in the supplied brief.


#### 3.6.3 Security

Also covered by: FR-001, FR-002, FR-003, FR-004.


**SEC-001** · Should · explicit

The system shall maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices.

Traceability: E-004, TEST-007, TEST-008, TEST-009

#### 3.6.4 Maintainability

Also covered by: FR-004.


#### 3.6.5 Portability

No separate requirement was specified in the supplied brief.


### 3.7 Other requirements

No separate requirement was specified in the supplied brief.


---

Canonical content SHA-256: 30c2cc09749b96ef07e0e33926dc7c54c11d1dd194cde7de426cc89848bc2e1c

Detailed acceptance criteria, evidence, architecture and the SDLC plan are retained in the supporting report and canonical JSON.
