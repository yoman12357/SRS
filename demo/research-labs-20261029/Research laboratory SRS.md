# Secure Access Control and Network Monitoring for University Research Laboratories

DRAFT — human review required

Version 1 | 2026-10-29T10:08:40.747439+00:00

Content SHA-256: 30c2cc09749b96ef07e0e33926dc7c54c11d1dd194cde7de426cc89848bc2e1c

AI-generated advisory document. A qualified person must review its correctness.
Automated checks are heuristic; SDLC scores are suitability points, not probabilities.

## Original project description

Design a secure access-control and network-monitoring system for university research laboratories containing sensitive equipment and research data. The system should allow only authorized students, faculty, researchers, and lab administrators to access designated lab networks and systems based on role and approved permissions. Administrative users should be able to grant or revoke access, review active sessions, monitor unusual login activity, and receive alerts for repeated failed authentication, unauthorized access attempts, and access outside approved lab hours. The system should maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices. The solution should be secure, reliable, and manageable across multiple research buildings.

## 1. Introduction

### Summary

This specification records the project purpose, stakeholder constraints and unresolved decisions stated in the source evidence below.

### Items


#### Title

Stakeholder source statement E-001

#### Detail

Design a secure access-control and network-monitoring system for university research laboratories containing sensitive equipment and research data.

#### Status

confirmed

#### Evidence ids

- E-001

#### Sources

None recorded.

#### Requirement ids

None recorded.

---


#### Title

Stakeholder source statement E-002

#### Detail

The system should allow only authorized students, faculty, researchers, and lab administrators to access designated lab networks and systems based on role and approved permissions.

#### Status

confirmed

#### Evidence ids

- E-002

#### Sources

None recorded.

#### Requirement ids

None recorded.

---


#### Title

Stakeholder source statement E-003

#### Detail

Administrative users should be able to grant or revoke access, review active sessions, monitor unusual login activity, and receive alerts for repeated failed authentication, unauthorized access attempts, and access outside approved lab hours.

#### Status

confirmed

#### Evidence ids

- E-003

#### Sources

None recorded.

#### Requirement ids

None recorded.

---


#### Title

Stakeholder source statement E-004

#### Detail

The system should maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices.

#### Status

confirmed

#### Evidence ids

- E-004

#### Sources

None recorded.

#### Requirement ids

None recorded.

---


#### Title

Stakeholder source statement E-005

#### Detail

The solution should be secure, reliable, and manageable across multiple research buildings.

#### Status

confirmed

#### Evidence ids

- E-005

#### Sources

None recorded.

#### Requirement ids

None recorded.

---


### Open issues

None recorded.

## 2. Functional requirements

### Applicability reason

Source-backed obligations; unspecified decisions remain open.

### Requirements


#### Id

FR-001

#### Title

provide secure access-control and network-monitoring capabilities for university research laboratories containing sensitive equipment and research data.

#### Statement

The system shall provide secure access-control and network-monitoring capabilities for university research laboratories containing sensitive equipment and research data.

#### Rationale

Implements stakeholder source E-001.

#### Priority

must

#### Dimensions

- business

#### Basis

explicit

#### Evidence ids

- E-001

#### Sources

None recorded.

#### Dependencies

None recorded.

#### Acceptance criteria


##### Given

A research laboratory with sensitive equipment and data

##### When

The system is deployed to monitor and control access

##### Then

Access to the lab systems is restricted to authorized users only, and network traffic is monitored for anomalies

##### Method

test

##### Observable evidence

Test capture of the resulting state

---


#### Unresolved decisions

None recorded.

---


#### Id

FR-002

#### Title

allow only authorized students, faculty, researchers, and lab administrators to access designated lab networks and systems based on role and approved permissions.

#### Statement

The system shall allow only authorized students, faculty, researchers, and lab administrators to access designated lab networks and systems based on role and approved permissions.

#### Rationale

Implements stakeholder source E-002.

#### Priority

should

#### Dimensions

- business

#### Basis

explicit

#### Evidence ids

- E-002

#### Sources

None recorded.

#### Dependencies

None recorded.

#### Acceptance criteria


##### Given

A user with defined roles: student, faculty, researcher, administrator

##### When

The user attempts to access a lab network system

##### Then

Access is granted only if the user's role and permissions are authorized by the system

##### Method

inspection

##### Observable evidence

Test capture of permission evaluation response showing role-based access decisions

---


#### Unresolved decisions

None recorded.

---


#### Id

FR-003

#### Title

Administrative users should be able to grant or revoke access, review active sessions, monitor unusual login activity, and receive alerts for repeated failed authentication, unauthorized access attempts, and access outside approved lab hours.

#### Statement

Administrative users should be able to grant or revoke access, review active sessions, monitor unusual login activity, and receive alerts for repeated failed authentication, unauthorized access attempts, and access outside approved lab hours.

#### Rationale

Implements stakeholder source E-003.

#### Priority

should

#### Dimensions

- business

#### Basis

explicit

#### Evidence ids

- E-003

#### Sources

None recorded.

#### Dependencies

None recorded.

#### Acceptance criteria


##### Given

An administrative user with valid credentials and access rights

##### When

The administrator initiates a request to grant or revoke access to a system

##### Then

The administrator observes access permissions are updated

##### Method

demonstration

##### Observable evidence

Test capture of the resulting response

---


##### Given

An administrative user with valid credentials and access rights

##### When

The administrator reviews active sessions and monitors login activity

##### Then

The administrator sees a list of active sessions and login activity records

##### Method

analysis

##### Observable evidence

Test capture of the resulting state

---


##### Given

An administrative user with valid credentials and access rights

##### When

The system detects repeated failed authentication attempts or unauthorized access outside approved hours

##### Then

The system detects repeated failed authentication attempts or unauthorized access outside approved hours

##### Method

test

##### Observable evidence

Test capture of the observed result

---


#### Unresolved decisions

None recorded.

---


#### Id

FR-004

#### Title

The solution should be secure, reliable, and manageable across multiple research buildings.

#### Statement

The solution should be secure, reliable, and manageable across multiple research buildings.

#### Rationale

Implements stakeholder source E-005.

#### Priority

should

#### Dimensions

- business

#### Basis

explicit

#### Evidence ids

- E-005

#### Sources

None recorded.

#### Dependencies

None recorded.

#### Acceptance criteria


##### Given

A multi-building university environment with distributed lab networks

##### When

The system is configured to manage access and monitoring across all buildings

##### Then

Access policies are consistently enforced, and network monitoring remains functional without degradation in performance or reliability

##### Method

test

##### Observable evidence

Test capture of cross-building policy enforcement and monitoring continuity

---


#### Unresolved decisions

None recorded.

---


### Related requirement ids

None recorded.

### Related acceptance criteria

None recorded.

## 3. Non-functional requirements

### Applicability reason

Existing canonical requirements, where applicable, are linked below; this section adds no separate obligation. Unresolved stakeholder decisions remain open.

### Requirements

None recorded.

### Related requirement ids

- FR-004

### Related acceptance criteria

None recorded.

## 4. Security, privacy and compliance

### Applicability reason

Source-backed obligations; unspecified decisions remain open.

### Requirements


#### Id

SEC-001

#### Title

maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices.

#### Statement

The system shall maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices.

#### Rationale

Implements stakeholder source E-004.

#### Priority

should

#### Dimensions

- security

#### Basis

explicit

#### Evidence ids

- E-004

#### Sources

None recorded.

#### Dependencies

None recorded.

#### Acceptance criteria


##### Given

An administrator performs an access decision or action

##### When

The system records the event in an audit log

##### Then

The log entry includes timestamp, user identity, action type, target resource, and outcome

##### Method

test

##### Observable evidence

Test capture of audit log entries for access decisions and administrative actions

---


##### Given

A research device connects to a lab network via approved configuration

##### When

The system validates the device's identity and permissions

##### Then

The connection is allowed only if the device is university-managed or has an approved research device certificate

##### Method

demonstration

##### Observable evidence

Test capture of device onboarding and permission validation

---


##### Given

A student attempts to access a lab network from outside campus hours

##### When

The system enforces access restrictions based on time and location rules

##### Then

Access is denied with a message indicating the restriction, and an alert is generated for administrator review

##### Method

inspection

##### Observable evidence

Test capture of access denial events and corresponding alerts

---


#### Unresolved decisions

- Thresholds for what constitutes unusual login activity
- Definition of 'approved research device' and how it is validated

---


### Related requirement ids

- FR-001
- FR-002
- FR-003

### Related acceptance criteria

None recorded.

## 5. Data requirements

### Applicability reason

Existing canonical requirements, where applicable, are linked below; this section adds no separate obligation. Unresolved stakeholder decisions remain open.

### Requirements

None recorded.

### Related requirement ids

- SEC-001

### Related acceptance criteria

None recorded.

## 6. Network and interfaces

### Applicability reason

Existing canonical requirements, where applicable, are linked below; this section adds no separate obligation. Unresolved stakeholder decisions remain open.

### Requirements

None recorded.

### Related requirement ids

- FR-001
- FR-002
- SEC-001

### Related acceptance criteria

None recorded.

## 7. Compliance and policy applicability matrix

### Mappings

None recorded.

### Open decisions

- Thresholds for what constitutes unusual login activity
- Definition of 'approved research device' and how it is validated

## 8. Architecture

### Summary

Proposed logical components and interactions mapped to canonical source obligations.

### Items


#### Title

Access Control Engine

#### Detail

Proposed logical owner for FR-002, SEC-001, FR-004.

#### Status

proposed

#### Evidence ids

- E-002
- E-004
- E-005

#### Sources

None recorded.

#### Requirement ids

- FR-002
- SEC-001
- FR-004

#### Component name

Access Control Engine

#### Responsibility

The system shall allow only authorized students, faculty, researchers, and lab administrators to access designated lab networks and systems based on role and approved permissions. The system shall maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices. The solution should be secure, reliable, and manageable across multiple research buildings.

---


#### Title

Network Monitoring Module

#### Detail

Proposed logical owner for FR-001, SEC-001, FR-004.

#### Status

proposed

#### Evidence ids

- E-001
- E-004
- E-005

#### Sources

None recorded.

#### Requirement ids

- FR-001
- SEC-001
- FR-004

#### Component name

Network Monitoring Module

#### Responsibility

The system shall provide secure access-control and network-monitoring capabilities for university research laboratories containing sensitive equipment and research data. The system shall maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices. The solution should be secure, reliable, and manageable across multiple research buildings.

---


#### Title

Audit and Alert Service

#### Detail

Proposed logical owner for FR-003, SEC-001, FR-004.

#### Status

proposed

#### Evidence ids

- E-003
- E-004
- E-005

#### Sources

None recorded.

#### Requirement ids

- FR-003
- SEC-001
- FR-004

#### Component name

Audit and Alert Service

#### Responsibility

Administrative users should be able to grant or revoke access, review active sessions, monitor unusual login activity, and receive alerts for repeated failed authentication, unauthorized access attempts, and access outside approved lab hours. The system shall maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices. The solution should be secure, reliable, and manageable across multiple research buildings.

---


### Open issues

None recorded.

### Data flows


#### Title

Proposed source-defined interaction

#### Detail

Proposed directed path for FR-004, SEC-001.

#### Status

proposed

#### Evidence ids

- E-004
- E-005

#### Sources

None recorded.

#### Requirement ids

- FR-004
- SEC-001

#### From component

Access Control Engine

#### To component

Network Monitoring Module

#### Data or action

The solution should be secure, reliable, and manageable across multiple research buildings. The system shall maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices.

---


#### Title

Proposed source-defined interaction

#### Detail

Proposed directed path for FR-004, SEC-001.

#### Status

proposed

#### Evidence ids

- E-004
- E-005

#### Sources

None recorded.

#### Requirement ids

- FR-004
- SEC-001

#### From component

Access Control Engine

#### To component

Audit and Alert Service

#### Data or action

The solution should be secure, reliable, and manageable across multiple research buildings. The system shall maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices.

---


#### Title

Proposed source-defined interaction

#### Detail

Proposed directed path for FR-004, SEC-001.

#### Status

proposed

#### Evidence ids

- E-004
- E-005

#### Sources

None recorded.

#### Requirement ids

- FR-004
- SEC-001

#### From component

Network Monitoring Module

#### To component

Access Control Engine

#### Data or action

The solution should be secure, reliable, and manageable across multiple research buildings. The system shall maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices.

---


#### Title

Proposed source-defined interaction

#### Detail

Proposed directed path for FR-004, SEC-001.

#### Status

proposed

#### Evidence ids

- E-004
- E-005

#### Sources

None recorded.

#### Requirement ids

- FR-004
- SEC-001

#### From component

Network Monitoring Module

#### To component

Audit and Alert Service

#### Data or action

The solution should be secure, reliable, and manageable across multiple research buildings. The system shall maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices.

---


#### Title

Proposed source-defined interaction

#### Detail

Proposed directed path for FR-004, SEC-001.

#### Status

proposed

#### Evidence ids

- E-004
- E-005

#### Sources

None recorded.

#### Requirement ids

- FR-004
- SEC-001

#### From component

Audit and Alert Service

#### To component

Access Control Engine

#### Data or action

The solution should be secure, reliable, and manageable across multiple research buildings. The system shall maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices.

---


#### Title

Proposed source-defined interaction

#### Detail

Proposed directed path for FR-004, SEC-001.

#### Status

proposed

#### Evidence ids

- E-004
- E-005

#### Sources

None recorded.

#### Requirement ids

- FR-004
- SEC-001

#### From component

Audit and Alert Service

#### To component

Network Monitoring Module

#### Data or action

The solution should be secure, reliable, and manageable across multiple research buildings. The system shall maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices.

---


### Trust boundaries


#### Title

Proposed source-defined trust boundary

#### Detail

Proposed logical trust-domain crossing for FR-004, SEC-001.

#### Status

proposed

#### Evidence ids

- E-004
- E-005

#### Sources

None recorded.

#### Requirement ids

- FR-004
- SEC-001

#### Untrusted component

Access Control Engine

#### Trusted component

Network Monitoring Module

#### Enforcement

The solution should be secure, reliable, and manageable across multiple research buildings. The system shall maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices.

---


#### Title

Proposed source-defined trust boundary

#### Detail

Proposed logical trust-domain crossing for FR-004, SEC-001.

#### Status

proposed

#### Evidence ids

- E-004
- E-005

#### Sources

None recorded.

#### Requirement ids

- FR-004
- SEC-001

#### Untrusted component

Access Control Engine

#### Trusted component

Audit and Alert Service

#### Enforcement

The solution should be secure, reliable, and manageable across multiple research buildings. The system shall maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices.

---


#### Title

Proposed source-defined trust boundary

#### Detail

Proposed logical trust-domain crossing for FR-004, SEC-001.

#### Status

proposed

#### Evidence ids

- E-004
- E-005

#### Sources

None recorded.

#### Requirement ids

- FR-004
- SEC-001

#### Untrusted component

Network Monitoring Module

#### Trusted component

Access Control Engine

#### Enforcement

The solution should be secure, reliable, and manageable across multiple research buildings. The system shall maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices.

---


#### Title

Proposed source-defined trust boundary

#### Detail

Proposed logical trust-domain crossing for FR-004, SEC-001.

#### Status

proposed

#### Evidence ids

- E-004
- E-005

#### Sources

None recorded.

#### Requirement ids

- FR-004
- SEC-001

#### Untrusted component

Network Monitoring Module

#### Trusted component

Audit and Alert Service

#### Enforcement

The solution should be secure, reliable, and manageable across multiple research buildings. The system shall maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices.

---


#### Title

Proposed source-defined trust boundary

#### Detail

Proposed logical trust-domain crossing for FR-004, SEC-001.

#### Status

proposed

#### Evidence ids

- E-004
- E-005

#### Sources

None recorded.

#### Requirement ids

- FR-004
- SEC-001

#### Untrusted component

Audit and Alert Service

#### Trusted component

Access Control Engine

#### Enforcement

The solution should be secure, reliable, and manageable across multiple research buildings. The system shall maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices.

---


#### Title

Proposed source-defined trust boundary

#### Detail

Proposed logical trust-domain crossing for FR-004, SEC-001.

#### Status

proposed

#### Evidence ids

- E-004
- E-005

#### Sources

None recorded.

#### Requirement ids

- FR-004
- SEC-001

#### Untrusted component

Audit and Alert Service

#### Trusted component

Network Monitoring Module

#### Enforcement

The solution should be secure, reliable, and manageable across multiple research buildings. The system shall maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices.

---


## 9. Threats

### Threats

None recorded.

### Assumptions

- These are defensive planning hypotheses, not observed incidents or approved extra controls. Unrecognized threats and actual implementation effectiveness require human review.

## 10. Risks

### Risks

None recorded.

### Open issues

None recorded.

## 11. User stories and use cases

### User stories and use cases


#### Id

UC-001

#### Actor

students

#### Goal

The system shall allow only authorized students, faculty, researchers, and lab administrators to access designated lab networks and systems based on role and approved permissions.

#### Story

As students, I need the following behavior: The system shall allow only authorized students, faculty, researchers, and lab administrators to access designated lab networks and systems based on role and approved permissions.

#### Preconditions

- A user with defined roles: student, faculty, researcher, administrator

#### Steps

- The user attempts to access a lab network system

#### Success outcome

Access is granted only if the user's role and permissions are authorized by the system

#### Alternate flows

None recorded.

#### Requirement ids

- FR-002

#### Evidence ids

- E-002

#### Unresolved decisions

None recorded.

---


### Open issues

None recorded.

## 12. Verification and acceptance

### Tests


#### Id

TEST-001

#### Requirement ids

- FR-001

#### Procedure

- Given: A research laboratory with sensitive equipment and data
- When: The system is deployed to monitor and control access

#### Expected result

Expected: Access to the lab systems is restricted to authorized users only, and network traffic is monitored for anomalies

#### Evidence to record

Evidence: Test capture of the resulting state

#### Test type

positive

---


#### Id

TEST-002

#### Requirement ids

- FR-002

#### Procedure

- Given: A user with defined roles: student, faculty, researcher, administrator
- When: The user attempts to access a lab network system

#### Expected result

Expected: Access is granted only if the user's role and permissions are authorized by the system

#### Evidence to record

Evidence: Test capture of permission evaluation response showing role-based access decisions

#### Test type

inspection

---


#### Id

TEST-003

#### Requirement ids

- FR-003

#### Procedure

- Given: An administrative user with valid credentials and access rights
- When: The administrator initiates a request to grant or revoke access to a system

#### Expected result

Expected: The administrator observes access permissions are updated

#### Evidence to record

Evidence: Test capture of the resulting response

#### Test type

positive

---


#### Id

TEST-004

#### Requirement ids

- FR-003

#### Procedure

- Given: An administrative user with valid credentials and access rights
- When: The administrator reviews active sessions and monitors login activity

#### Expected result

Expected: The administrator sees a list of active sessions and login activity records

#### Evidence to record

Evidence: Test capture of the resulting state

#### Test type

analysis

---


#### Id

TEST-005

#### Requirement ids

- FR-003

#### Procedure

- Given: An administrative user with valid credentials and access rights
- When: The system detects repeated failed authentication attempts or unauthorized access outside approved hours

#### Expected result

Expected: The system detects repeated failed authentication attempts or unauthorized access outside approved hours

#### Evidence to record

Evidence: Test capture of the observed result

#### Test type

negative

---


#### Id

TEST-006

#### Requirement ids

- FR-004

#### Procedure

- Given: A multi-building university environment with distributed lab networks
- When: The system is configured to manage access and monitoring across all buildings

#### Expected result

Expected: Access policies are consistently enforced, and network monitoring remains functional without degradation in performance or reliability

#### Evidence to record

Evidence: Test capture of cross-building policy enforcement and monitoring continuity

#### Test type

positive

---


#### Id

TEST-007

#### Requirement ids

- SEC-001

#### Procedure

- Given: An administrator performs an access decision or action
- When: The system records the event in an audit log

#### Expected result

Expected: The log entry includes timestamp, user identity, action type, target resource, and outcome

#### Evidence to record

Evidence: Test capture of audit log entries for access decisions and administrative actions

#### Test type

positive

---


#### Id

TEST-008

#### Requirement ids

- SEC-001

#### Procedure

- Given: A research device connects to a lab network via approved configuration
- When: The system validates the device's identity and permissions

#### Expected result

Expected: The connection is allowed only if the device is university-managed or has an approved research device certificate

#### Evidence to record

Evidence: Test capture of device onboarding and permission validation

#### Test type

positive

---


#### Id

TEST-009

#### Requirement ids

- SEC-001

#### Procedure

- Given: A student attempts to access a lab network from outside campus hours
- When: The system enforces access restrictions based on time and location rules

#### Expected result

Expected: Access is denied with a message indicating the restriction, and an alert is generated for administrator review

#### Evidence to record

Evidence: Test capture of access denial events and corresponding alerts

#### Test type

inspection

---


### Limitations

- These verification plans have not been executed; their acceptance outcomes require testing.

## 13. Glossary

### Summary

Source-present terminology; definitions introduce no additional product obligation.

### Items


#### Title

Access control

#### Detail

Rules and enforcement governing which principals may perform actions on resources.

#### Status

proposed

#### Evidence ids

- E-001

#### Sources

None recorded.

#### Requirement ids

None recorded.

---


#### Title

Audit record

#### Detail

A stored record of an event. Required event scope and retention are determined by the linked source, not this definition.

#### Status

proposed

#### Evidence ids

- E-004

#### Sources

None recorded.

#### Requirement ids

None recorded.

---


#### Title

Log

#### Detail

A collection of event records. This term does not itself require additional logging fields, events or access permissions.

#### Status

proposed

#### Evidence ids

- E-004

#### Sources

None recorded.

#### Requirement ids

None recorded.

---


#### Title

Device isolation

#### Detail

Restriction of a device's network access; the source determines whether and by whom this action is permitted.

#### Status

proposed

#### Evidence ids

- E-004

#### Sources

None recorded.

#### Requirement ids

None recorded.

---


### Open issues

None recorded.

## 14. SDLC recommendation and workflow

### Selected model

Agile

### Justification

The selection of Agile as the required model is based on a uniform score of 40 across all candidates, with no differentiating input evidence provided to favor one methodology over another. Given the absence of explicit factors such as budget, delivery timelines, failure consequences, feedback mechanisms, legacy systems, regulation, schedule constraints, stability needs, uncertainty levels, or verification requirements, no candidate model can be objectively ranked for suitability. The provisional nature of this decision reflects an incomplete evidence base. All models receive equal score meaning—suitability points out of 100—not probabilities. Without evidence to differentiate between Agile and other methodologies (e.g., DevSecOps, Spiral, V-Model, Waterfall, Hybrid, Incremental), the choice remains arbitrary and unsupported by input data. The requirement for secure access control, role-based permissions, real-time monitoring, audit logging, and cross-building manageability aligns with iterative development principles but does not inherently mandate Agile over other models. Unknown factors such as regulation or legacy systems could influence model selection if addressed; however, these are currently unaccounted for in the input evidence. Therefore, this decision is grounded only in equal suitability scores and lacks evidentiary differentiation.

### Tradeoffs

- Recurring delivery requires stakeholder review and backlog refinement; a cycle does not guarantee completeness or remove unresolved decisions.

### Phases


#### Name

Requirements and verification planning

#### Phase type

planning

#### Activities

- Review and baseline the source-defined work group: FR-001: The system shall provide secure access-control and network-monitoring capabilities for university research laboratories containing sensitive equipment and research data.; FR-002: The system shall allow only authorized students, faculty, researchers, and lab administrators to access designated lab networks and systems based on role and approved permissions.; FR-003: Administrative users should be able to grant or revoke access, review active sessions, monitor unusual login activity, and receive alerts for repeated failed authentication, unauthorized access attempts, and access outside approved lab hours.; FR-004: The solution should be secure, reliable, and manageable across multiple research buildings.; SEC-001: The system shall maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices.
- Create the unit, integration, system and acceptance test plan before implementation; retain each authored acceptance criterion.

#### Roles

- Proposed project owner
- Proposed development lead
- Proposed verification reviewer

#### Deliverables

- Versioned requirements baseline
- Unit, integration, system and acceptance test plan
- Unresolved-decision record

#### Entry criteria

- Authoritative inputs and canonical requirements are available for review.

#### Exit criteria

- A human reviewer has recorded the baseline decision and disposition of unresolved scope.

#### Security checks

- Review implementation and acceptance evidence against SEC-001: The system shall maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices.

#### Human approval

Pending human decision by Proposed project owner on this phase's deliverables and unresolved decisions; no approval is recorded by generation.

#### Requirement ids

- FR-001
- FR-002
- FR-003
- FR-004
- SEC-001

---


#### Name

Agile delivery cycle

#### Phase type

iteration

#### Activities

- Review and prioritize the backlog for the next iteration without changing source-defined scope.
- Implement the source-defined work group: FR-001: The system shall provide secure access-control and network-monitoring capabilities for university research laboratories containing sensitive equipment and research data.; FR-002: The system shall allow only authorized students, faculty, researchers, and lab administrators to access designated lab networks and systems based on role and approved permissions.; FR-003: Administrative users should be able to grant or revoke access, review active sessions, monitor unusual login activity, and receive alerts for repeated failed authentication, unauthorized access attempts, and access outside approved lab hours.; FR-004: The solution should be secure, reliable, and manageable across multiple research buildings.; SEC-001: The system shall maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices.
- In an authorized isolated test environment, execute TEST-001: Given: A research laboratory with sensitive equipment and data When: The system is deployed to monitor and control access Expected: Access to the lab systems is restricted to authorized users only, and network traffic is monitored for anomalies
- In an authorized isolated test environment, execute TEST-002: Given: A user with defined roles: student, faculty, researcher, administrator When: The user attempts to access a lab network system Expected: Access is granted only if the user's role and permissions are authorized by the system
- In an authorized isolated test environment, execute TEST-003: Given: An administrative user with valid credentials and access rights When: The administrator initiates a request to grant or revoke access to a system Expected: The administrator observes access permissions are updated
- In an authorized isolated test environment, execute TEST-004: Given: An administrative user with valid credentials and access rights When: The administrator reviews active sessions and monitors login activity Expected: The administrator sees a list of active sessions and login activity records
- In an authorized isolated test environment, execute TEST-005: Given: An administrative user with valid credentials and access rights When: The system detects repeated failed authentication attempts or unauthorized access outside approved hours Expected: The system detects repeated failed authentication attempts or unauthorized access outside approved hours
- In an authorized isolated test environment, execute TEST-006: Given: A multi-building university environment with distributed lab networks When: The system is configured to manage access and monitoring across all buildings Expected: Access policies are consistently enforced, and network monitoring remains functional without degradation in performance or reliability
- In an authorized isolated test environment, execute TEST-007: Given: An administrator performs an access decision or action When: The system records the event in an audit log Expected: The log entry includes timestamp, user identity, action type, target resource, and outcome
- In an authorized isolated test environment, execute TEST-008: Given: A research device connects to a lab network via approved configuration When: The system validates the device's identity and permissions Expected: The connection is allowed only if the device is university-managed or has an approved research device certificate
- In an authorized isolated test environment, execute TEST-009: Given: A student attempts to access a lab network from outside campus hours When: The system enforces access restrictions based on time and location rules Expected: Access is denied with a message indicating the restriction, and an alert is generated for administrator review
- Collect stakeholder feedback; agree its cadence with a human reviewer before scheduling cycles.
- Return accepted stakeholder feedback and observed defects to the backlog and plan the next iteration.

#### Roles

- Proposed project owner
- Proposed development lead
- Proposed verification reviewer

#### Deliverables

- Requirement-linked implementation increment
- Recorded test evidence
- Reviewed feedback and next-iteration backlog

#### Entry criteria

- Prior work, source scope and the reviewed test plan are available for iteration planning.

#### Exit criteria

- A human reviewer has assessed the increment, test evidence and feedback; unresolved changes return to the next iteration.

#### Security checks

- Review implementation and acceptance evidence against SEC-001: The system shall maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices.

#### Human approval

Pending human decision by Proposed project owner on this phase's deliverables and unresolved decisions; no approval is recorded by generation.

#### Requirement ids

- FR-001
- FR-002
- FR-003
- FR-004
- SEC-001

---


#### Name

Release and handoff

#### Phase type

release

#### Activities

- Review the exact requirements baseline, implementation links and verification evidence before a release decision.
- Carry unresolved source decisions into handoff; generated text is not human approval.

#### Roles

- Proposed project owner
- Proposed development lead
- Proposed verification reviewer

#### Deliverables

- Requirements and verification evidence package
- Pending human release decision
- Outstanding-decision record

#### Entry criteria

- Verification evidence and unresolved decisions are available for human review.

#### Exit criteria

- A human has recorded the release/handoff decision for the reviewed content.

#### Security checks

- Review implementation and acceptance evidence against SEC-001: The system shall maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices.

#### Human approval

Pending human decision by Proposed project owner on this phase's deliverables and unresolved decisions; no approval is recorded by generation.

#### Requirement ids

- FR-001
- FR-002
- FR-003
- FR-004
- SEC-001

---


### Unknown factors

- budget
- delivery
- failure\_consequences
- feedback
- legacy
- regulation
- schedule
- stability
- uncertainty
- verification

### V-Model development and verification pairing

None recorded.

## SDLC decision evidence

### Policy

sequential-sdlc-1.1

### Generation profile

sequential-sdlc-generation-2.0

### Factors

None recorded.

### Ranked candidates


#### Model

Agile

#### Score

40

#### Reasons

- No differentiating input evidence

---


#### Model

DevSecOps

#### Score

40

#### Reasons

- No differentiating input evidence

---


#### Model

Spiral

#### Score

40

#### Reasons

- No differentiating input evidence

---


#### Model

V-Model

#### Score

40

#### Reasons

- No differentiating input evidence

---


#### Model

Waterfall

#### Score

40

#### Reasons

- No differentiating input evidence

---


#### Model

Hybrid

#### Score

40

#### Reasons

- No differentiating input evidence

---


#### Model

Incremental

#### Score

40

#### Reasons

- No differentiating input evidence

---


## Original evidence

### Id

E-001

### Source

description

### Quote

Design a secure access-control and network-monitoring system for university research laboratories containing sensitive equipment and research data.

### Context



---


### Id

E-002

### Source

description

### Quote

The system should allow only authorized students, faculty, researchers, and lab administrators to access designated lab networks and systems based on role and approved permissions.

### Context



---


### Id

E-003

### Source

description

### Quote

Administrative users should be able to grant or revoke access, review active sessions, monitor unusual login activity, and receive alerts for repeated failed authentication, unauthorized access attempts, and access outside approved lab hours.

### Context



---


### Id

E-004

### Source

description

### Quote

The system should maintain audit logs of access decisions and administrator actions, isolate research lab networks from general student and guest networks, and support both university-managed and approved research devices.

### Context



---


### Id

E-005

### Source

description

### Quote

The solution should be secure, reliable, and manageable across multiple research buildings.

### Context



---


## Source references

### Id

kb-c1e0239af9dd46bd:1

### Source document id

kb-c1e0239af9dd46bd

### Chunk index

1

### Page or section

text chunk 2

### Relevance score

\0.7412

### Text

thing. Each time someone tries to access a resource, evaluate whether they should be allowed. \[Sessions\](https://cheatsheetseries.owasp.org/cheatsheets/Session\_Management\_Cheat\_Sheet.html) should be short-lived and require re-authentication when they expire. No "set it and forget it" access.

\### 4. Access is Determined by Dynamic Policy

Access decisions consider multiple factors: who's asking, what device they're using, where they're connecting from, what time it is, and how they normally behave. These policies change based on risk. Someone accessing payroll during work hours from their work laptop is low risk. The same person downloading lots of data at 2 AM from a coffee shop is high risk.

\### 5. Monitor and Measure the Security Posture of All Assets

Continuously check the health and security of all devices and systems. If you can't see it, you can't protect it. This includes monitoring for patches, antivirus status, configuration changes, and suspicious behavior. Assets that fall out of compliance lose access.

\### 6. All Authentication and Authorization is Dynamic and Strictly Enforced

Security decisions happen in real-time for every access request. Don't rely on static rules or permanent permissions. The system should automatically adjust access based on current risk levels, revoke access for compromised accounts, and isolate suspicious devices.

\### 7. Collect Information to Improve Security Posture

Gather as much security data as possible about users, devices, network traffic, and system behavior. Use this information to detect threats, improve policies, and make better security decisions. This data is essential for compliance and incident investigation.

\## Core Zero Trust Architecture Components

Zero Trust uses three main parts that work together:

\*\*Pol

### Title

03\_OWASP\_CheatSheets/107\_OWASP\_Zero\_Trust\_Architecture\_Cheat\_Sheet.md

### Sha256

f5fe6d1e1cfefc05da1b1b9773acee6b7e9d156f4aa69ab0a14a7a1adfd2a8ef

---


### Id

kb-c1e0239af9dd46bd:8

### Source document id

kb-c1e0239af9dd46bd

### Chunk index

8

### Page or section

text chunk 9

### Relevance score

\0.7242

### Text

monitoring of antivirus status, OS patches, security configurations, and device security posture
\- \*\*Certificate-based device identity\*\*: Use PKI certificates to uniquely identify and authenticate each device
\- \*\*Vulnerability scanning\*\*: Regular assessment of device security posture and patch levels
\- \*\*Revoke trust when compromised\*\*: Automatically remove access if device security is compromised

\### Protecting Endpoints

Every device needs these protections:

\- \*\*Anti-malware software\*\*: Real-time protection against viruses and malware
\- \*\*Behavior monitoring\*\*: Watch for suspicious device activity
\- \*\*Full disk encryption\*\*: Encrypt all data on the device
\- \*\*Remote wipe\*\*: Ability to erase lost or stolen devices

\## Network Architecture

\### Micro-Segmentation

Instead of one big network, create small isolated segments:

\- \*\*Separate by application\*\*: Each app gets its own network segment
\- \*\*Block by default\*\*: Don't allow traffic unless specifically permitted
\- \*\*Monitor internal traffic\*\*: Watch data moving between systems
\- \*\*Use encrypted communications\*\*: All communication between systems must be encrypted

\### Network Controls

Implement these network protections:

\- \*\*DNS filtering\*\*: Block access to malicious websites
\- \*\*Web filtering\*\*: Control what websites users can visit
\- \*\*Replace VPNs\*\*: Use Zero Trust Network Access (ZTNA) instead
\- \*\*Monitor traffic\*\*: Analyze all network connections

\## Application and Data Protection

\### Securing Applications

Protect your applications with these controls:

\- \*\*Identity-aware proxy\*\*: Check user identity before allowing app access
\- \*\*Web Application Firewalls (WAFs)\*\*: Block OWASP Top 10 attacks at the application layer. Deploy at network edge, internal segments, or as part of API gateways
\- \*\*API security g

### Title

03\_OWASP\_CheatSheets/107\_OWASP\_Zero\_Trust\_Architecture\_Cheat\_Sheet.md

### Sha256

f5fe6d1e1cfefc05da1b1b9773acee6b7e9d156f4aa69ab0a14a7a1adfd2a8ef

---


### Id

kb-ecd06e0e85ebe229:2

### Source document id

kb-ecd06e0e85ebe229

### Chunk index

2

### Page or section

text chunk 3

### Relevance score

\0.7057

### Text

ake advantage of. Faults related to authorization control can allow malicious insiders and outsiders alike to view, modify, or delete sensitive resources of all forms (databases records, static files, personally identifiable information (PII), etc.) or perform actions, such as creating a new account or initiating a costly order, that they should not be privileged to do. Furthermore, if logging related to access control is not properly set-up, such authorization violations may go undetected or at least remain unattributable to a particular individual or group.

\## Recommendations

\### Enforce Least Privileges

As a security concept, Least Privileges refers to the principle of assigning users only the minimum privileges necessary to complete their job. Although perhaps most commonly applied in system administration, this principle has relevance to the software developer as well. Least Privileges must be applied both horizontally and vertically. For example, even though both an accountant and sales representative may occupy the same level in an organization's hierarchy, both require access to different resources to perform their jobs. The accountant should likely not be granted access to a customer database and the sales representative should not be able to access payroll data. Similarly, the head of the sales department is likely to need more privileged access than their subordinates.

Failure to enforce least privileges in an application can jeopardize the confidentiality of sensitive resources. Mitigation strategies are applied primarily during the Architecture and Design phase (see \[CWE-272\](https://cwe.mitre.org/data/definitions/272.html)); however, the principle must be addressed throughout the SDLC.

Consider the following points and best practices:

\- During the de

### Title

03\_OWASP\_CheatSheets/038\_OWASP\_Authorization\_Cheat\_Sheet.md

### Sha256

e78a10eb9759a1fc7593ba1fc89a05b017e7e795ac16ad5496bdba86138d891f

---


### Id

kb-c1e0239af9dd46bd:2

### Source document id

kb-c1e0239af9dd46bd

### Chunk index

2

### Page or section

text chunk 3

### Relevance score

\0.6897

### Text

ke better security decisions. This data is essential for compliance and incident investigation.

\## Core Zero Trust Architecture Components

Zero Trust uses three main parts that work together:

\*\*Policy Engine\*\* - This makes decisions about whether to allow or block access. It looks at user identity, device health, location, behavior, and risk scores. The tricky part is making policies that are secure but don't make work impossible.

\*\*Policy Administrator\*\* - This takes the decision from the Policy Engine and tells the enforcement systems what to do. When the Policy Engine says "allow access but require extra verification," the Policy Administrator figures out the details and sends commands to the right systems.

\*\*Policy Enforcement Point\*\* - These actually block or allow access attempts. This includes firewalls, proxy servers, application gateways, and API gateways. The important thing is that enforcement happens everywhere, not just at your network edge.

These three parts work together on every access request in real time, creating security that adapts to changing situations.

\## How Zero Trust Addresses Modern Security Challenges

Zero Trust tackles security problems that traditional approaches can't handle effectively. Here's how it works in practice:

\### Traditional vs. Zero Trust Responses

| Attack Scenario | Traditional Security Response | Zero Trust Response |
|----------------|------------------------------|-------------------|
| \*\*Stolen credentials\*\* | Reset password, add basic MFA | Continuous risk assessment, device verification, behavioral analysis - access denied even with valid credentials if risk is high |
| \*\*Insider threat\*\* | Trust employees inside network perimeter | Verify every action regardless of user location, role, or tenure - no implici

### Title

03\_OWASP\_CheatSheets/107\_OWASP\_Zero\_Trust\_Architecture\_Cheat\_Sheet.md

### Sha256

f5fe6d1e1cfefc05da1b1b9773acee6b7e9d156f4aa69ab0a14a7a1adfd2a8ef

---


### Id

kb-ecd06e0e85ebe229:16

### Source document id

kb-ecd06e0e85ebe229

### Chunk index

16

### Page or section

text chunk 17

### Relevance score

\0.7083

### Text

ation being left in an unpredictable state (\[CWE-280: Improper Handling of Insufficient Permissions or Privileges\](https://cwe.mitre.org/data/definitions/280.html)). Specific recommendations include the following:

\- Ensure all exception and failed access control checks are handled no matter how unlikely they seem (\[OWASP Top Ten Proactive Controls C10: Handle all errors and exceptions\](https://owasp.org/www-project-proactive-controls/v3/en/c10-errors-exceptions)). This does not mean that an application should always try to "correct" for a failed check; oftentimes a simple message or HTTP status code is all that is required.
\- Centralize the logic for handling failed access control checks.
\- Verify the handling of exception and authorization failures. Ensure that such failures, no matter how unlikely, do not put the software into an unstable state that could lead to authorization bypass.
\- Ensure sensitive information, such as system logs or debugging output, is not exposed in error messages. Misconfigured error messages can increase the attack surface of your application. (\[CWE-209: Generation of Error Message Containing Sensitive Information\](https://cwe.mitre.org/data/definitions/209.html))

\### Implement Appropriate Logging

Logging is one of the most important detective controls in application security; insufficient logging and monitoring is recognized as among  the most critical security risks in \[OWASP's Top Ten 2021\](https://owasp.org/Top10/A09\_2021-Security\_Logging\_and\_Monitoring\_Failures/). Appropriate logs can not only detect malicious activity, but are also invaluable resources in post-incident investigations, can be used to troubleshoot access control and other security related problems, and are useful in security auditing. Though easy to overlook during th

### Title

03\_OWASP\_CheatSheets/038\_OWASP\_Authorization\_Cheat\_Sheet.md

### Sha256

e78a10eb9759a1fc7593ba1fc89a05b017e7e795ac16ad5496bdba86138d891f

---


## Quality and traceability

### Validation policy version

source-grounding-1.14

### Status

needs\_review

### Checks passed

22

### Checks total

22

### Findings


#### Code

human\_semantic\_review\_required

#### Severity

warning

#### Section

document

#### Item id



#### Message

Review completeness, actor permissions, contradictions and citation applicability; schema and link checks do not prove semantic correctness.

---


### Evidence coverage


#### E-001

- FR-001

#### E-002

- FR-002

#### E-003

- FR-003

#### E-004

- SEC-001

#### E-005

- FR-004

### Traceability


#### Requirement id

FR-001

#### Evidence ids

- E-001

#### Source chunks

None recorded.

#### Scenario ids

None recorded.

#### Test ids

- TEST-001

#### Sdlc phases

- Requirements and verification planning
- Agile delivery cycle
- Release and handoff

---


#### Requirement id

FR-002

#### Evidence ids

- E-002

#### Source chunks

None recorded.

#### Scenario ids

- UC-001

#### Test ids

- TEST-002

#### Sdlc phases

- Requirements and verification planning
- Agile delivery cycle
- Release and handoff

---


#### Requirement id

FR-003

#### Evidence ids

- E-003

#### Source chunks

None recorded.

#### Scenario ids

None recorded.

#### Test ids

- TEST-003
- TEST-004
- TEST-005

#### Sdlc phases

- Requirements and verification planning
- Agile delivery cycle
- Release and handoff

---


#### Requirement id

FR-004

#### Evidence ids

- E-005

#### Source chunks

None recorded.

#### Scenario ids

None recorded.

#### Test ids

- TEST-006

#### Sdlc phases

- Requirements and verification planning
- Agile delivery cycle
- Release and handoff

---


#### Requirement id

SEC-001

#### Evidence ids

- E-004

#### Source chunks

None recorded.

#### Scenario ids

None recorded.

#### Test ids

- TEST-007
- TEST-008
- TEST-009

#### Sdlc phases

- Requirements and verification planning
- Agile delivery cycle
- Release and handoff

---


## Human review history
None recorded.

## Generation provenance

### Requested model

cybersrs-qwen3-4b-ft:latest

### Actual models used

- cybersrs-qwen3-4b-ft:latest
- qwen3:4b-instruct-2507-q4\_K\_M

### Section models


#### Introduction

- cybersrs-qwen3-4b-ft:latest

#### Functional requirements

- qwen3:4b-instruct-2507-q4\_K\_M

#### Non-functional requirements

None recorded.

#### Security, privacy and compliance

- cybersrs-qwen3-4b-ft:latest

#### Data requirements

None recorded.

#### Network and interfaces

None recorded.

#### Compliance and policy applicability matrix

- cybersrs-qwen3-4b-ft:latest

#### Architecture

- cybersrs-qwen3-4b-ft:latest

#### Threats

- cybersrs-qwen3-4b-ft:latest

#### Risks

- cybersrs-qwen3-4b-ft:latest

#### User stories and use cases

- cybersrs-qwen3-4b-ft:latest

#### Verification and acceptance

- cybersrs-qwen3-4b-ft:latest

#### Glossary

- cybersrs-qwen3-4b-ft:latest

#### SDLC recommendation and workflow

- qwen3:4b-instruct-2507-q4\_K\_M

### Prompt version

sequential-1.28
