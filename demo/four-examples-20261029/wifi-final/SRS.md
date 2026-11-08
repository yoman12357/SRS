# Secure Campus Wi-Fi Management System

Software Requirements Specification

IEEE 830-1998 outline

DRAFT — human review required

Version 1 | 2026-10-29T13:36:54.004529+00:00

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

Design a secure campus Wi-Fi management system for a university that provides wireless access to students, faculty, staff, and guests across academic buildings, hostels, laboratories, and administrative offices. The system should use centralized authentication, role-based access control, separate guest access from internal university resources, monitor active wireless sessions, detect repeated authentication failures and unauthorized access attempts, and generate security alerts. Network administrators should be able to configure wireless access policies, review connected devices, revoke access, and inspect audit logs. The solution should support university-managed and approved personal devices and remain secure, scalable, reliable, and manageable across multiple campus locations.


### 1.3 Definitions, acronyms and abbreviations


| Term | Meaning |
| --- | --- |
| Access control | Rules and enforcement governing which principals may perform actions on resources. |
| Policy | A rule or decision governing permitted actions; its project-specific meaning remains defined by the source requirements. |
| Audit record | A stored record of an event. Required event scope and retention are determined by the linked source, not this definition. |
| Log | A collection of event records. This term does not itself require additional logging fields, events or access permissions. |

### 1.4 References


| Reference | Source |
| --- | --- |
| Format | IEEE Std 830-1998, clauses 5 and Annex A (document organization). |

### 1.5 Overview

Section 2 summarizes the product, stakeholders and open decisions. Section 3 contains the uniquely identified requirements. Detailed evidence, acceptance procedures and the SDLC plan are available in the supporting report.


## 2 Overall description


### 2.1 Product perspective

Design a secure campus Wi-Fi management system for a university that provides wireless access to students, faculty, staff, and guests across academic buildings, hostels, laboratories, and administrative offices.


### 2.2 Product functions

Functional topics are summarized below; section 3 retains the full requirements.

- Access permissions — FR-001, FR-002, FR-003
- Authentication — FR-002
- Policy controls — FR-003
- Monitoring and alerts — FR-002
- Audit logging — FR-003
- Device support — FR-003

### 2.3 User characteristics and stakeholders

Labels group stakeholders for readability. They do not combine permissions.

Education, training and experience requirements remain unspecified.


| Role | Source user groups | Responsibility |
| --- | --- | --- |
| User | students, faculty, staff, guests | Uses permitted functions; each source class keeps its specified permissions. |
| Admin | Network administrators | Performs only the role's source-defined operations in section 3. |
| Project Analyst | Document review role | Reviews requirements and tracks open decisions; this role grants no product access. |

### 2.4 Constraints

No additional implementation constraints were confirmed. Source-defined restrictions remain in the requirements in section 3.


### 2.5 Assumptions and dependencies

Open decisions requiring confirmation:

- How will device-level policies be enforced on personal devices?
- What specific authentication protocols (e.g., 802.1X) are required for internal access?
- How will repeated authentication failures trigger alerts or automated actions?
- What is the retention period and access control for audit logs?
- Definition of 'approved personal devices' including hardware, OS versions, and security posture thresholds
- Thresholds for scalability under concurrent device load across campus locations
- Mechanism for real-time monitoring of device health and compliance status during operation

## 3 Specific requirements

Each requirement is stated once with its original identifier and wording. Cross-references identify requirements covering more than one concern.


### 3.1 External interface requirements


#### 3.1.1 User interfaces

No specific interface requirement was supplied; confirmation is required.


#### 3.1.2 Hardware interfaces

Related requirements: FR-003, NFR-001. Interface details beyond those requirements remain unspecified.


#### 3.1.3 Software interfaces

Related requirements: FR-002. Interface details beyond those requirements remain unspecified.


#### 3.1.4 Communications interfaces

Related requirements: FR-001, FR-002, FR-003. Interface details beyond those requirements remain unspecified.


### 3.2 Functional requirements


**FR-001** · Must · explicit

The system shall provide wireless access to students, faculty, staff, and guests across academic buildings, hostels, laboratories, and administrative offices.

Traceability: E-001, TEST-001

**FR-002** · Should · explicit

The system shall use centralized authentication, role-based access control, separate guest access from internal university resources, monitor active wireless sessions, detect repeated authentication failures and unauthorized access attempts, and generate security alerts.

Traceability: E-002, TEST-002, TEST-003

**FR-003** · Should · explicit

Network administrators should be able to configure wireless access policies, review connected devices, revoke access, and inspect audit logs.

Traceability: E-003, TEST-004, TEST-005, TEST-006

### 3.3 Performance requirements


**NFR-001** · Should · explicit

The solution shall support university-managed and approved personal devices and remain secure, scalable, reliable, and manageable across multiple campus locations.

Traceability: E-004, TEST-007, TEST-008

### 3.4 Logical database requirements

No separate requirement was specified in the supplied brief.


### 3.5 Design constraints

No separate requirement was specified in the supplied brief.


### 3.6 Software system attributes


#### 3.6.1 Reliability

Also covered by: NFR-001.


#### 3.6.2 Availability

No separate requirement was specified in the supplied brief.


#### 3.6.3 Security

Also covered by: FR-002, FR-003, NFR-001.


#### 3.6.4 Maintainability

Also covered by: NFR-001.


#### 3.6.5 Portability

No separate requirement was specified in the supplied brief.


### 3.7 Other requirements

No separate requirement was specified in the supplied brief.


---

Canonical content SHA-256: 9c1bde3733f6e04eaacaee1c9fadb487db780fb35bd80c7e01dbe14f31e6fb42

Detailed acceptance criteria, evidence, architecture and the SDLC plan are retained in the supporting report and canonical JSON.
