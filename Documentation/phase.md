# 🧭 **RICHWELL SCHOOL PORTAL – DEVELOPMENT PLAN (v3.0)**

---

## 🧱 **Phase 1: Environment & Core Models Setup**

### 🎯 **Goal**

Establish the Django environment, repository standards, and implement all base models according to the schema.

### ✅ **Tasks**

**Environment Setup**

1. Initialize project repo and `.env`.
2. Create Django project `richwell_portal`.
3. Create core apps:

   * `users` – custom `AbstractUser` model.
   * `academics` – programs, curricula, subjects, prerequisites.
   * `enrollment` – terms, sections, student subjects.
   * `grades` – grading and INC logic.
   * `audit` – audit trail and archive system.
   * `settingsapp` – dynamic system configuration.

**Dependencies**

* `django`, `django-htmx`, `python-dotenv`
* TailwindCSS (CDN)
* Alpine.js (CDN)
* SQLite (dev), PostgreSQL (prod)

**Database Models**

* Implement all tables from `Documentation/schema.md`
* Add field-level constraints and foreign keys.
* Use Django `choices` for enums (roles, statuses, etc.).
* Include automatic timestamps and related names.
* Register all models in Django Admin.

**Frontend**

* `base.html` layout with Tailwind + HTMX structure.
* Simple dashboard placeholders for each role.
* Navbar with dynamic role-based visibility (stubbed).

---

## 🔐 **Phase 2: RBAC, Authentication, and Dashboards**

### 🎯 **Goal**

Implement full authentication system and dynamic dashboards per user role.

### ✅ **Tasks**

**RBAC Backend**

1. Extend Django’s `AbstractUser` → custom `Users` model.
2. Define role choices: `student`, `professor`, `registrar`, `dean`, `admission`, `admin`.
3. Implement middleware/decorator for route-based access.
4. Integrate permissions layer (`role_required` decorator).

**Authentication**

* Create login/logout/password reset using Django’s auth views.
* Add session-based access with role filtering.
* Redirect users to respective dashboards after login.

**Dashboards**

* `Admin`: System overview (links to all modules).
* `Registrar`: Terms, sections, curriculum control.
* `Professor`: Assigned sections, grading access.
* `Student`: Enrollment + grade viewer.
* `Admission`: New applicant management.
* `Dean`: Academic analytics.

**Frontend**

* HTMX fragments for dashboard loading (no full page reload).
* Alpine.js for navbar role toggling and dropdowns.
* Tailwind theming for a consistent academic UI look.

---

## 🎓 **Phase 3: Admissions & Student Onboarding**

### 🎯 **Goal**

Enable online admission flow and student creation with curriculum linkage.

### ✅ **Tasks**

1. Toggle admission link via `Settings.admission_link_enabled`.
2. Build public admission form with Freshman/Transferee options.
3. On submit:

   * Auto-create `Users` + `Students` entries.
   * Assign `Curriculum` and default program.
   * Auto-enroll recommended freshman subjects ≤ `30 units`.
4. Registrar crediting page for transferees (manual TOR validation).
5. Log admission actions in `AuditTrail`.

**Frontend**

* Public admission page with step-by-step progress.
* Confirmation screen with generated student credentials.

---

## 📘 **Phase 4: Enrollment Module**

### 🎯 **Goal**

Implement validated enrollment based on prerequisites, sections, and settings.

### ✅ **Tasks**

1. Enrollment open/close toggled via `Settings.enrollment_open`.
2. Show eligible subjects filtered by:

   * `recommended_year`, `recommended_sem`
   * Completed prerequisites
3. Validate:

   * No duplicate enrollment
   * Section capacity
   * Unit limit (`Settings.freshman_unit_cap`)
4. Create record in `StudentSubjects` upon validation success.
5. Generate downloadable **COR (Certificate of Registration)** PDF.

**Frontend**

* HTMX-driven table for adding/dropping subjects.
* Live total unit counter.
* COR preview modal.

---

## 🧑‍🏫 **Phase 5: Professor Grading System**

### 🎯 **Goal**

Enable grade encoding, INC management, and automatic audit logging.

### ✅ **Tasks**

1. Professors see only their assigned `Sections`.
2. Grade input per student per subject.
3. Update `StudentSubjects.status` automatically:

   * `completed`, `failed`, or `inc`
4. INC lifecycle logic:

   * Major = 6 months, Minor = 1 year
   * Auto change → `repeat_required` after expiry
5. Every grade update logged to `AuditTrail`.

**Frontend**

* HTMX editable table for grades.
* Color-coded statuses.
* Summary widget for grade stats (passed/failed/INC).

---

## 🗃️ **Phase 6: Archiving, AuditTrail & Settings Management**

### 🎯 **Goal**

Ensure accountability and control through centralized settings and historical data retention.

### ✅ **Tasks**

1. Settings editor UI for toggles and values.
2. Audit decorator/service for CRUD events.
3. Archiving service for:

   * Term closure
   * Student graduation
4. Store archived data as JSON in `Archive.data_snapshot`.
5. Make archived records read-only.

**Frontend**

* Settings page with HTMX toggle saves.
* Audit log viewer with date/entity filters.
* Archive browser with JSON preview.

---

## 📊 **Phase 7: Reporting & Analytics**

### 🎯 **Goal**

Provide performance visibility for admins, registrars, and deans.

### ✅ **Tasks**

* Enrollment reports (per term, section, program)
* Grade distribution & failure rate
* INC tracking & resolution report
* Student unit load report
* Section utilization (open/full ratio)
* Export (CSV/PDF)

**Frontend**

* HTMX charts via Chart.js
* Filters for term and program
* Printable templates with official headers

---

## 🚀 **Phase 8: QA, Optimization & Deployment**

### 🎯 **Goal**

Deliver stable production build with optimized performance.

### ✅ **Tasks**

* Conduct end-to-end tests across all roles.
* Optimize ORM queries (`select_related`, `prefetch_related`).
* Enable caching for static and report-heavy views.
* Add pagination for large lists.
* Apply Tailwind responsive refinements.
* Prepare `.env.prod` and PostgreSQL config.
* Deploy via Gunicorn + Nginx (Ubuntu server).
* Write final `DEPLOYMENT.md` and admin guide.

**Frontend**

* Finalized layout and responsive tweaks.
* Unified branding (Richwell color scheme).
* Test latency of all HTMX interactions.

---

## 🔧 **Post-MVP Extensions**

* REST API (DRF) for mobile apps.
* Notification system (email/SMS).
* Payment tracking integration.
* SSO / OAuth2 for institutional login.
* Curriculum flowchart visualizer.

---

