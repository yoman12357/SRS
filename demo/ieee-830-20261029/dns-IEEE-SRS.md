# Secure DNS and Web Access Filtering System

Software Requirements Specification

IEEE 830-1998 outline

DRAFT — human review required

Version 1 | 2026-10-29T10:23:17.128847+00:00

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

Design a secure DNS and web-access filtering system for a university that protects students, faculty, staff, and administrative users from malicious or unauthorized internet destinations. The system should inspect DNS requests, block access to known malicious domains, apply different browsing policies based on user roles, and provide administrators with a dashboard for reviewing blocked requests and security events. Administrators should be able to create and update filtering policies, allow approved exceptions, investigate repeated attempts to access blocked resources, and temporarily restrict users when suspicious behavior is detected. The platform should maintain audit logs of policy changes and filtering decisions, integrate with centralized authentication, and support deployment across academic buildings, hostels, laboratories, and administrative offices. The solution should be secure, scalable, reliable, and manageable.


### 1.3 Definitions, acronyms and abbreviations


| Term | Meaning |
| --- | --- |
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

Design a secure DNS and web-access filtering system for a university that protects students, faculty, staff, and administrative users from malicious or unauthorized internet destinations.


### 2.2 Product functions

Functional topics are summarized below; section 3 retains the full requirements.

- Access permissions — FR-001, FR-002, FR-003
- DNS and web filtering — FR-001, FR-002, FR-003
- Policy controls — FR-002, FR-003
- Dashboard — FR-002
- Event investigation — FR-003

### 2.3 User characteristics and stakeholders

Labels group stakeholders for readability. They do not combine permissions.

Education, training and experience requirements remain unspecified.


| Role | Source user groups | Responsibility |
| --- | --- | --- |
| User | students, faculty, staff | Uses permitted functions; each source class keeps its specified permissions. |
| Admin | administrative users, administrators | Performs only the role's source-defined operations in section 3. |
| Project Analyst | Document review role | Reviews requirements and tracks open decisions; this role grants no product access. |

### 2.4 Constraints

No additional implementation constraints were confirmed. Source-defined restrictions remain in the requirements in section 3.


### 2.5 Assumptions and dependencies

Open decisions requiring confirmation:

- how user roles are defined and mapped to browsing policies
- what constitutes suspicious behavior and how it is detected
- how audit logs are stored and accessed by authorized personnel
- whether the system will support real-time threat intelligence feeds
- Definition of 'malicious domain'
- Threshold for repeated access attempts
- Definition of 'known malicious domain'
- Definition of 'suspicious behavior'
- Duration of temporary restriction
- Workflow for investigation review
- Definition of 'manageable' in terms of administrative interface usability thresholds
- Thresholds for scalability under peak load conditions
- Recovery time objectives for component failure scenarios
- Whether audit logs shall include metadata about the source IP address of policy change initiators
- The exact scope of role-based policies across different building types
- How policy synchronization is handled during cross-location deployments

## 3 Specific requirements

Each requirement is stated once with its original identifier and wording. Cross-references identify requirements covering more than one concern.


### 3.1 External interface requirements


#### 3.1.1 User interfaces

Related requirements: FR-001, FR-002, FR-003. Interface details beyond those requirements remain unspecified.


#### 3.1.2 Hardware interfaces

No specific interface requirement was supplied; confirmation is required.


#### 3.1.3 Software interfaces

Related requirements: DR-001. Interface details beyond those requirements remain unspecified.


#### 3.1.4 Communications interfaces

Related requirements: FR-001, FR-002. Interface details beyond those requirements remain unspecified.


### 3.2 Functional requirements


**FR-001** · Must · explicit

The system shall implement a secure DNS and web-access filtering mechanism to protect all university users from malicious or unauthorized internet destinations.

Traceability: E-001, TEST-001

**FR-002** · Should · explicit

The system shall inspect DNS requests, block access to known malicious domains, apply role-based browsing policies, and provide administrators with a dashboard for reviewing blocked requests and security events.

Traceability: E-002, TEST-002, TEST-003

**FR-003** · Should · explicit

Administrators shall be able to create, update filtering policies, allow approved exceptions, investigate repeated access attempts to blocked resources, and temporarily restrict users when suspicious behavior is detected.

Traceability: E-003, TEST-004, TEST-005, TEST-006

### 3.3 Performance requirements


**NFR-001** · Should · explicit

The solution shall be secure, scalable, reliable, and manageable.

Traceability: E-005, TEST-007, TEST-008, TEST-009, TEST-010

### 3.4 Logical database requirements


**DR-001** · Should · explicit

The platform shall maintain audit logs of policy changes and filtering decisions, integrate with centralized authentication, and support deployment across academic buildings, hostels, laboratories, and administrative offices.

Traceability: E-004, TEST-011, TEST-012, TEST-013, TEST-014

### 3.5 Design constraints

No separate requirement was specified in the supplied brief.


### 3.6 Software system attributes


#### 3.6.1 Reliability

Also covered by: NFR-001.


#### 3.6.2 Availability

No separate requirement was specified in the supplied brief.


#### 3.6.3 Security

Also covered by: FR-001, FR-002, FR-003, NFR-001, DR-001.


#### 3.6.4 Maintainability

Also covered by: NFR-001.


#### 3.6.5 Portability

No separate requirement was specified in the supplied brief.


### 3.7 Other requirements

No separate requirement was specified in the supplied brief.


---

Canonical content SHA-256: bad6625ad3214c7431f456a00a11950c8c3cc765d7a5a6c79f6c6e95ae9ab581

Detailed acceptance criteria, evidence, architecture and the SDLC plan are retained in the supporting report and canonical JSON.
