# MedVision AI Frontend — Complete Design and Feasibility Description

## 1. Executive summary

This frontend is a **high-fidelity internal clinical-workspace prototype** for a bone-fracture-detection assistant. It is intentionally designed as a **review-first evidence system**, not a public marketing site and not a standalone diagnostic product. Its visual model is called **Clinical Instrument**: a graphite operational rail, a warm paper-like work surface, compact metadata, numbered workflow stations, and dark evidence frames that distinguish the AI signal from the clinician’s decision.

The current project is **feasible as the frontend foundation for the intended workflow**, provided that it is connected to a secure backend, storage layer, authentication service, inference job system, and organization-specific policy controls. It is **not yet suitable for real clinical deployment by itself**, because it currently uses mock data and simulated state transitions.

| Area | Current feasibility | What it means |
| --- | --- | --- |
| Product workflow | High | The core user journey, screen hierarchy, states, and information design are present and reviewable. |
| Visual/UX direction | High | The interface is coherent across desktop and mobile and has a distinct clinical-product identity. |
| Frontend demo | High | Navigation, filters, upload validation, local review actions, modals, tabs, and empty states can be demonstrated. |
| API integration | Partial | A narrow Axios boundary exists, but no real endpoint contracts or query cache are connected. |
| Authentication and authorization | Not production-ready | Forms are visual/demo flows; protected-route enforcement and server sessions are not implemented. |
| Medical-image handling | Not production-ready | JPG/PNG UX validation exists; secure upload, object storage, server validation, and inference are absent. |
| Clinical/regulatory deployment | Not production-ready | The UI deliberately avoids compliance claims while the applicable framework and organization policies remain unconfirmed. |

> **Primary product principle:** AI output is rendered as evidence to inspect and document, rather than as a decision to accept automatically.

## 2. Product and design intent

MedVision AI is aimed at internal healthcare staff, principally **technicians, clinicians, and administrators**. The primary task is to move from an anonymized X-ray image to a documented, clinician-reviewed outcome with a traceable history of actions.

The design intentionally avoids cheerful consumer-health styling and generic admin-dashboard patterns. Each major UI surface identifies the kind of work being performed: a **queue** is a queue, an **intake station** is an intake station, an **evidence review desk** is a dedicated imaging surface, and a **decision panel** records the accountable human action.

### Visual system

| Design element | Implementation | Product reason |
| --- | --- | --- |
| Dark graphite navigation rail | Persistent desktop rail with numbered routes and system-status footer | Keeps the application operational rather than marketing-like. |
| Warm paper canvas | Off-white content surface with rule-based panels | Reduces clinical coldness while preserving contrast and readability. |
| Signal Teal accent | Used for active navigation, focus contours, secure-state indicators, and primary actions | Makes status and action visible without making the interface visually noisy. |
| Editorial serif + compact utility type | DM Serif Display for rare editorial headings; Manrope and DM Mono for controls and metadata | Adds product character while keeping dense clinical information functional. |
| Authored brand mark | A line-based bone cross-section and scan-aperture symbol | Avoids a generic app tile and ties the brand to the imaging workflow. |
| Radiographic evidence treatment | Grids, measurement coordinates, bone-density forms, scan apertures, focus rings, and annotation labels | Grounds the design in an X-ray review context rather than a generic monitoring UI. |

The interface is desktop-first for hospital workstations, while responsive layouts have been checked at a narrow mobile viewport. The expected practical target is **desktop and tablet workstation use**, not mobile image diagnosis.

## 3. End-to-end user workflow

The frontend supports the following intended sequence.

| Step | User role | Current screen behavior | Required production service |
| --- | --- | --- | --- |
| 1. Access workspace | Staff user | Login, open self-registration, forgot password, and reset-password screens | Identity provider, session service, password reset email, optional MFA policy |
| 2. View workload | Technician / clinician | Dashboard displays case queue, queue signal counts, review states, and model metadata reference | Analysis list endpoint, user-specific queue rules, model-registry metadata |
| 3. Upload image | Technician / clinician | Drag/drop or browse for one JPG/PNG; client checks MIME type and 10 MB limit | Authenticated upload endpoint, image validation, malware scanning, storage, case creation |
| 4. Run inference | System | UI simulates queued/processing state | Async inference job service, status polling or server-sent events, timeout/error states |
| 5. Inspect result | Clinician | Evidence desk displays original/overlay concept, confidence, severity, finding details, and disclaimer | Original and overlay image URLs, prediction result, model version, report generator |
| 6. Record review | Clinician | Approve, flag for second opinion, and add-note controls update locally | Signed review/approval endpoint, optimistic-state rules, immutable audit event |
| 7. Find historical case | Staff user | Search and status filtering over mock history; links lead to results desk | Paginated analysis search/filter endpoint and server-enforced access scope |
| 8. Govern organization | Admin | User-management table, invite modal, session/security settings, and audit log | Role management, invitations, device sessions, MFA enrollment, audit-retention policy |

## 4. Implemented screens and interaction design

### 4.1 Authentication and account access

The login route includes work-email and password fields, password visibility control, a “remember this workstation” control, disabled pending submission, and a generic visual sign-in flow. It links to the password reset and account creation routes.

The account model reflects your confirmation that **self-registration should be open**. The sign-up screen asks for full name, work email, and role, plus an acknowledgement that the user is authorized to use the workspace. The content does not claim regulatory compliance.

Password recovery has separate forgot-password and reset-password screens. The reset form requires a password with at least 12 characters, a number, and a symbol in its user-facing guidance.

**Current limitation:** these forms do not send credentials to a server, perform real inline server-error handling, or implement MFA. The MFA UI exists in Security settings, but MFA feature-flag behavior must be added when the identity solution is selected.

### 4.2 Dashboard: queue, signal, and handoff

The dashboard is a staff-workstation overview rather than a greeting card. It contains a live service indicator, a clinically worded primary action—“Create documented analysis”—and a signal board with open cases, fracture review count, inference exception count, and a small queue-velocity trace.

The central **Open reviews** queue displays case ID, anatomy, uploader context, finding, confidence, and review status. It has a dedicated empty state so a new account or cleared queue has an understandable next action. A handoff panel uses a radiographic evidence surface and directs the clinician to an active review desk.

The lower metadata strip surfaces total analyses, fracture count, model accuracy with a visible metadata reference, median review time, and the permanent clinician-review disclaimer.

### 4.3 Upload / intake station

The upload screen is intentionally titled and laid out as an **intake station**. It includes a large drop zone, browse action, format/size rule, and a side protocol panel that communicates validation, queueing, and clinician review as three distinct steps.

Client-side validation accepts **JPG and PNG only**, confirms MIME type, and rejects files above **10 MB**. It contains display states for invalid input, progress, queued inference, and a link into the result workspace after the simulated queue step.

The screen contains explicit framework-neutral privacy language instructing staff to remove identifiers under their organization’s process. It clearly states that client-side validation is for user experience only and that server-side validation remains mandatory.

### 4.4 Evidence review desk / results

The results screen is designed as a dedicated review station. It separates the interface into two different products surfaces.

| Surface | Content | Purpose |
| --- | --- | --- |
| Evidence viewer | Original/overlay control, measurement coordinate, focus ring, bone-density silhouette, grid, model metadata, and image-quality metadata | Makes the AI signal inspectable and spatially grounded. |
| Interpretation panel | Fracture status, confidence, severity, region, finding type, recommendation, and review controls | Converts evidence into a clinician’s accountable next action. |

The result state includes the permanent disclaimer: **“AI-assisted result — requires clinician review before clinical use.”** The visible result data is sample data: “Fracture detected,” 94% confidence, possible cortical break in the distal radius, and moderate severity.

The clinician can approve the result, flag it for a second opinion, or reveal a text area to add a clinical note. The interaction updates state in the browser and visually confirms the action. A real implementation must replace this with authenticated server actions and immutable audit records.

### 4.5 History / case archive

The history page is a filterable case archive. It includes search by case, anatomy, or uploader; status selection; date-range affordance; an export-view affordance; case rows with confidence and status; and a distinct “no cases match these filters” state.

The interface visually supports pagination, but it does not currently request pages from an API. In production, filters, counts, result scope, pagination cursor, and export permissions must be server-driven.

### 4.6 Profile, security, administration, and audit

The Profile and Settings page separates **My Account** from **Security** as requested. My Account includes editable personal data, notification switches, password-change affordance, and sign-out. Security includes MFA enrollment affordance and a device-session list with revoke actions.

The Admin User Management page is visible in the current demo because the mock user has the Admin role. It includes active-user counts, a role/status table, an invite modal, and distinct user states such as Active and Invited.

The Audit Log is a read-only list with filtering UI and entry metadata showing actor, action, target, timestamp, and descriptive detail. It is designed to be useful for both global admin views and, once the server filters the data, non-admin users’ scoped activity.

### 4.7 Error and restricted states

The project includes a 403-style role-restricted page and a 404 page. The Axios boundary dispatches a session-expired browser event after a 401 response, which establishes an integration hook for a future session-expired route.

**Current limitation:** a full session-expired screen and an actual auth guard that redirects unauthenticated users while preserving the intended route are not yet wired to real authentication state.

## 5. Frontend architecture that exists today

The frontend is a Vite-based static application located in `client/`. It is a single-page routed application with reusable layout primitives and mock data.

| Folder / file | Current responsibility |
| --- | --- |
| `client/src/App.tsx` | All current route definitions, reusable layout components, page-level workflows, and local UI state. |
| `client/src/index.css` | Clinical Instrument design system, responsive behavior, motion preferences, and visual evidence treatment. |
| `client/src/types/index.ts` | TypeScript domain types for User, Analysis, AnalysisStatus, and AuditLogEntry. |
| `client/src/lib/mockApi.ts` | Deterministic sample user, analyses, and audit entries used by the visual prototype. |
| `client/src/api/http.ts` | Central Axios instance with `VITE_API_BASE_URL` fallback, cookie credentials enabled, timeout, and 401/session-expiry hook. |
| `ideas.md` | Design rationale and explicit visual decisions for the Quiet Clinical / Clinical Instrument system. |
| `README.md` | Setup, security considerations, known limitations, Docker instructions, and backend follow-up checklist. |

### Important stack deviation to consider

The original requested stack named React 18, React Router v6, Tailwind/shadcn, TanStack Query, React Hook Form + Zod, Axios, Zustand, MSW, Vitest/RTL, and Playwright. The managed static project template available for this build uses **React 19 and Wouter**. The current frontend uses custom CSS for the bespoke visual system and does not yet integrate TanStack Query, React Hook Form, Zod, Zustand, MSW, Vitest/RTL, or Playwright.

This does **not** make the project infeasible. However, if your engineering organization requires the originally specified stack as a non-negotiable technical standard, the next implementation phase should include a deliberate migration/refactor before backend integration rather than treating this prototype as the final application architecture.

| Requested capability | Current state | Recommended next action |
| --- | --- | --- |
| React Router v6 | Not used; the template uses Wouter | Migrate route definitions and add explicit route guards if React Router v6 is mandatory. |
| TanStack Query | Not implemented | Introduce typed query/mutation hooks before connecting the real API. |
| React Hook Form + Zod | Not implemented | Move auth, upload metadata, invite, profile, and review note forms to schemas. |
| Zustand | Not implemented | Use for session UI, active organization, theme, and transient review workspace state if required. |
| MSW | Not implemented | Add mock handlers mirroring the backend OpenAPI/contract so frontend development remains independent. |
| Vitest / RTL / Playwright | Not implemented | Add unit, interaction, accessibility, and end-to-end coverage before production. |
| Axios | Partially implemented | Keep `client/src/api/http.ts` as the sole API transport boundary and add typed endpoint modules. |

## 6. Data model and API contract needed for production

The existing types establish the beginning of a shared vocabulary. A production backend should provide at least the following resource families.

| Resource | Essential fields | Required operations |
| --- | --- | --- |
| User | ID, name, email, role, organization, account status, MFA state | Login, registration, refresh, logout, profile update, password reset, session list/revoke |
| Analysis | ID, case reference, anatomy, uploader, timestamps, status, inference job ID, storage pointers | Create, list/search/filter, retrieve by ID, retry/timeout state, access-scope enforcement |
| PredictionResult | Fracture status, confidence, severity, region, finding type, recommendation, model version, overlay reference | Retrieve result, model metadata, report export |
| ClinicalReview | Reviewer ID, action, note, reviewed timestamp, second-opinion route | Approve, flag, add/edit allowed note, retrieve review history |
| AuditLogEntry | Actor, action, target, time, tenant/organization scope, request context | Append server-side event, list/filter/export by authorized scope |
| User invitation | Email, role, token, status, expiry | Create, resend, accept, revoke |

The current Axios module uses `withCredentials: true`, allowing a backend to prefer **httpOnly cookie sessions**. If the organization instead chooses access tokens, token storage and silent refresh should remain isolated in a dedicated auth module—not scattered through page components—and should not default to localStorage.

## 7. Security and privacy boundary

The frontend includes sensible **frontend-side guardrails**, but it cannot create a secure clinical deployment on its own.

### Present in the project

| Control | Present implementation |
| --- | --- |
| No frontend secrets | No API key, PHI, or secret is embedded in the component code. |
| CSP documentation | `client/index.html` contains a Content-Security-Policy meta tag, while `nginx.conf` adds a deployable header baseline. |
| Cookie-oriented API boundary | Axios is configured with `withCredentials`. |
| Upload UX validation | MIME type, extension acceptance, and 10 MB limit are checked before simulated queueing. |
| Framework-neutral content | The UI makes no assertion of HIPAA, DPDP, or other compliance until you confirm the applicable framework. |
| Persistent review disclaimer | Results always state that clinician review is required before clinical use. |
| Responsive keyboard-friendly controls | Native buttons/inputs, focus outlines, semantic labels, and icon labels are used throughout. |

### Must be implemented on the server or hosting layer

| Requirement | Why it cannot be satisfied by the current frontend alone |
| --- | --- |
| Real authentication and RBAC | Client-side display rules can be bypassed; the server must enforce user and organization scope. |
| CSRF strategy | Cookie sessions require server-side CSRF protection and documented same-site/origin rules. |
| Image validation | Extension and MIME checks can be falsified; the server must inspect file signatures, decodeability, size, authorization, and malicious content. |
| PHI controls | De-identification, access logging, storage encryption, retention, deletion, and breach controls require backend/infrastructure policy. |
| Inference safety | Timeout, retries, status integrity, model provenance, monitoring, and clinical review rules require a job service and database. |
| Audit integrity | Audit events must be created server-side and be protected from ordinary client mutation. |
| PDF reports | Report contents, sign-off state, download authorization, and storage must be server-generated or securely rendered. |

> **Do not treat the client-side image checks as a security boundary.** They are useful for immediate staff feedback only.

## 8. Deployment and operations

The repository includes a multi-stage Dockerfile that builds the Vite client and serves `dist/public` through Nginx. It also includes an Nginx configuration with client-routing fallback and a security-header baseline, plus a `docker-compose.yml` stub for local web-service use.

There is a GitHub Actions workflow that runs `pnpm check` and `pnpm build` on push and pull request. The project was manually verified by building the production bundle and inspecting representative desktop and mobile screens.

| Deployment item | Status | Notes |
| --- | --- | --- |
| Vite production build | Verified | `pnpm build` completes successfully. |
| TypeScript check | Verified | `pnpm check` completes successfully. |
| Docker/Nginx serving | Scaffolded | Suitable for a static deployment model; add backend services separately. |
| CI | Scaffolded | Currently typecheck and build only. |
| Unit/e2e tests | Not yet added | Required before production. |
| Environment example | Documented in README | The project documents `VITE_API_BASE_URL`; add the controlled environment configuration through your deployment settings. |
| Bundle optimization | Follow-up | The production bundle produces a size warning; route-level code splitting should be added if load performance is a priority. |

## 9. Feasibility assessment by project scenario

### Feasible now

The current frontend is appropriate for stakeholder review, workflow design validation, usability review, visual acceptance, and backend-contract planning. It can also be used as the basis of a real frontend if the implementation gaps are resolved in an organized next phase.

### Feasible with normal product engineering work

The project is feasible for an internal clinical workflow that uses JPG/PNG uploads, one analysis per image, AI inference, clinician review, role-based organization access, and audit history. The next phase needs a backend plus the planned frontend integration work listed below.

### Not feasible without additional decisions

The following areas should not be assumed until the organization makes a decision:

| Decision needed | Why it matters |
| --- | --- |
| Applicable regulatory and policy framework | Determines consent copy, retention, access review, export controls, breach workflow, and terminology. |
| Identity system | Determines self-registration rules, organization verification, password requirements, SSO, MFA, and session model. |
| Inference architecture | Determines job polling, latency expectations, failure recovery, report lifecycle, and monitoring. |
| Storage and image lifecycle | Determines image encryption, signed URL rules, deletion, backup, and locality. |
| DICOM requirement | The current frontend intentionally supports JPG/PNG only; DICOM needs a dedicated viewer and metadata-handling design. |
| Clinical governance process | Determines who may approve, flag, override, view reports, and access organization-wide audit logs. |

## 10. Recommended implementation path

The most practical way to turn this into a deployment candidate is to preserve the current product design while adding capabilities in a controlled order.

| Priority | Implementation work | Outcome |
| --- | --- | --- |
| 1 | Confirm identity provider, organization model, roles, regulatory framework, storage policy, and inference contract | Prevents the UX and security model from being built on untested assumptions. |
| 2 | Add real auth/session handling, route guards, RBAC, and session-expired behavior | Makes the app safe to expose to controlled internal users. |
| 3 | Introduce typed API modules, TanStack Query, React Hook Form, Zod, and MSW contract handlers if the requested stack remains mandatory | Turns the static demo into a maintainable application integration layer. |
| 4 | Implement secure upload, server-side image validation, job polling, result retrieval, and failure/timeout recovery | Enables the core analysis workflow. |
| 5 | Implement server-side clinical review actions, PDF report generation, immutable audit events, and scoped history | Creates a credible review and governance workflow. |
| 6 | Add unit, integration, accessibility, and Playwright end-to-end coverage | Makes changes safer and supports production release validation. |
| 7 | Perform a formal security/privacy assessment against the confirmed framework and organization controls | Establishes whether the deployment environment is appropriate for sensitive medical images. |

## 11. Bottom line

The frontend is a **strong product and design starting point** for your stated internal fracture-analysis assistant. It communicates a clear and differentiated clinical workflow: image intake, AI-assisted evidence review, clinician decision, and traceability. It is particularly well suited for a team that wants the interface to feel like a focused review instrument rather than a generic dashboard.

Its production feasibility depends less on visual work and more on the next technical decisions: identity, secure storage, inference integration, server-side auditability, role enforcement, and the applicable privacy/regulatory policy. If those pieces are within your project scope—as they normally would be for an internal healthcare workflow—the frontend can be evolved into a production application. If you need a lightweight image-analysis demo without authentication, audit, or clinical governance, this implementation is more structured than necessary but can still be simplified.

