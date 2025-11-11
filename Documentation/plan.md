# 🧭 **RICHWELL SCHOOL PORTAL – FULL SYSTEM PLAN (v2.0)**

---

## 🎯 **Goal**

Build a unified, rule-based academic management system that:

1. Prevents invalid enrollments through prerequisite and load validation.
2. Automates academic rules like unit caps, INC deadlines, and grade logic.
3. Simplifies workflows for professors, registrars, and students.
4. Supports curriculum versioning, CHED updates, and long-term data archiving.
5. Provides flexible control through a dynamic **Settings** module.

---

## 🧩 **System Modules**

### 1. **User & Role Management**

* All system accounts are stored in `Users`.
* Each user has a defined `role` determining access and privileges.
* Passwords stored securely as hashes.
* Admins can create, deactivate, or reset user accounts.
* Students automatically receive linked accounts upon admission approval.

---

### 2. **Admissions & Student Onboarding**

**Handled by:** *Admission* and *Registrar*

**Controlled by:**
`Settings.key_name = 'admission_link_enabled'` → toggled *true/false* by Registrar or Admin.

**Flow:**

1. Admission enables the **online admission link**.
2. New student fills out the admission form and selects **Freshman** or **Transferee**.
3. System creates a record in `Students` and `Users`.
4. Freshmen:

   * Auto-assigned default subjects based on `recommended_year` and `recommended_sem`.
   * Can add or remove subjects up to the **freshman unit cap (30 units)**.
5. Transferees:

   * Forwarded to the Registrar for TOR validation.
   * Registrar assigns appropriate `curriculum_id` and manually credits subjects.

---

### 3. **Curriculum Management**

**Handled by:** *Registrar* or *Admin*

* Each program (`Programs`) may have multiple `Curricula` versions (CHED/DepEd revisions).
* Each version links subjects through `CurriculumSubjects`.
* `Subjects` table defines `type` (major/minor), `recommended_year`, and `recommended_sem`.
* When a new CHED curriculum is implemented:

  * Create a new entry in `Curricula`.
  * Map its subjects in `CurriculumSubjects`.
  * New students are automatically linked to the active version.

**Result:** No mismatch between old and new curricula.

---

### 4. **Term Management**

**Handled by:** *Registrar*

* Terms are defined in `Terms` (start date, end date, deadlines, and active flag).
* Only one term can be active at a time.
* When a term closes:

  * All grades are finalized.
  * Data snapshots are stored in `Archive`.
  * `is_active` is set to `false`.
  * Registrar opens the next term for section creation.

---

### 5. **Section Management**

**Handled by:** *Registrar* or *Dean*

**Flow:**

1. Registrar creates `Sections` for each subject and assigns professors.
2. Each section includes:

   * `subject_id`
   * `term_id`
   * `professor_id`
   * `section_code`
   * `capacity`
3. Status options: `open`, `full`, or `closed`.
4. Only Registrar/Dean/Admin can modify professor assignments.
5. Professors automatically gain access to grade encoding and class lists for their assigned sections.

---

### 6. **Enrollment**

**Handled by:** *Students*

**Controlled by:**
`Settings.key_name = 'enrollment_open'`

**Flow:**

1. Student logs in → system detects current term and their `curriculum_id`.
2. Displays:

   * Recommended subjects (`recommended_year` and `recommended_sem` match current year level).
   * Eligible subjects (passed prerequisites).
   * Section availability (capacity and status).
3. Student adds or drops subjects → system validates:

   * **Prerequisites** passed (`Prereqs`).
   * **No duplicate enrollment** in the same term.
   * **Section capacity** not exceeded.
   * **Unit limit** ≤ `Settings.freshman_unit_cap` (30 if freshman).
4. Upon successful validation → record added to `StudentSubjects`.
5. Enrollment is final (no approval queue).
6. COR (Certificate of Registration) auto-generated.

---

### 7. **Grades & INC Management**

**Handled by:** *Professors* and *Registrar*

* Professors can view and manage only their assigned `Sections`.
* Grade entries are stored in `Grades`.
* For each student:

  * Grade posted → updates `StudentSubjects.status` (completed, failed, or inc).
  * INC grades tracked by subject type:

    * **Major:** expires in 6 months
    * **Minor:** expires in 1 year
* After expiration → status auto-changes to `repeat_required`.
* Registrar must confirm physical completion forms before grade resolution.
* All grade changes are logged in `AuditTrail`.

---

### 8. **Audit Trail**

**Automatic logging for critical updates.**

Every key event creates an entry in `AuditTrail`:

* Enrollment changes
* Grade edits
* Setting toggles
* Section assignments
* Archiving actions

**Example:**

```json
{
  "actor_id": 4,
  "action": "update_setting",
  "entity": "Settings",
  "entity_id": 1,
  "old_value_json": {"value_text": "true"},
  "new_value_json": {"value_text": "false"},
  "created_at": "2025-11-07T14:30:00"
}
```

Purpose: maintain accountability and traceability.

---

### 9. **Archiving System**

**Unified and simplified archive (`Archive`).**

When a term closes or a student graduates:

* System saves a JSON snapshot of their data in `Archive`.
* Example entry:

  ```json
  {
    "entity": "Grades",
    "entity_id": 451,
    "data_snapshot": {"student_id": 22, "subject_id": 101, "grade": "1.75"},
    "reason": "Term Closed"
  }
  ```
* Archived data becomes read-only in the live database.
* Only Admin and Registrar can perform archiving and restoration.

---

### 10. **Settings Management**

**Handled by:** *Registrar* or *Admin*

Dynamic system-wide configuration stored in `Settings`.

**Examples:**

| Key Name               | Description                             | Example Value |
| ---------------------- | --------------------------------------- | ------------- |
| admission_link_enabled | Toggles online admission link           | `true/false`  |
| enrollment_open        | Enables/disables active term enrollment | `true/false`  |
| freshman_unit_cap      | Freshman total unit limit               | `30`          |
| passing_grade          | Minimum passing grade                   | `3.00`        |
| timezone               | Server timezone                         | `Asia/Manila` |

Changes are logged in `AuditTrail`.

---

### 11. **Reporting & Analytics**

**Used by:** *Dean*, *Registrar*, *Admin*

Reports include:

* Enrollment per section, term, or program
* Grade distribution and average per subject
* INC tracking and repeat rates
* Student load summary (total units per term)
* Section utilization (open vs full)
* Archival and audit summaries for oversight

---

## 👥 **Roles & Permissions**

| Role                   | Responsibilities                                             | System Access                      |
| ---------------------- | ------------------------------------------------------------ | ---------------------------------- |
| **Admin**              | Full control of all modules, system configuration, and users | All modules                        |
| **Registrar**          | Manages programs, curricula, terms, sections, archiving      | Admin tools, reports               |
| **Dean**               | Monitors department performance, assigns professors          | Reports, section management        |
| **Professor**          | Encodes grades and resolves INCs                             | Assigned sections and grade sheets |
| **Admission**          | Handles new student onboarding, document review              | Admission portal                   |
| **Student (Freshman)** | Enrolls freely (≤30 units), views COR, grades                | Enrollment module                  |
| **Student (Regular)**  | Enrolls in eligible subjects, views INCs and grades          | Enrollment module                  |

---

## 🧮 **Key System Rules**

| Rule                         | Description                                                      |
| ---------------------------- | ---------------------------------------------------------------- |
| **Freshman Unit Cap**        | Max total 30 units per first term (from `Settings`).             |
| **Prerequisite Validation**  | Must pass/credit all prerequisite subjects before enrolling.     |
| **Recommended Subject Flow** | Based on `recommended_year` and `recommended_sem` in `Subjects`. |
| **INC Deadline**             | 6 months for major subjects, 1 year for minor.                   |
| **Automatic Repeat**         | INCs become `repeat_required` after expiration.                  |
| **Section Access**           | Professors can only view their assigned sections.                |
| **Audit Enforcement**        | All changes logged in `AuditTrail`.                              |
| **Archiving Rule**           | Data is archived after term close or student graduation.         |
| **Settings Control**         | Registrar/Admin dynamically manage system toggles.               |

---

## ⚙️ **Technical Notes**

* **Database:** SQLite (for testing and local development) — can later migrate to PostgreSQL or MySQL.
* **Backend:** **Django Framework** — handles routing, ORM, authentication, and admin panel.
* **Frontend:** **Django Templates + HTMX + Alpine.js** for dynamic interactivity without a heavy frontend framework.
* **Styling:** Tailwind CSS and/or Bootstrap via CDN imports (no build tools required).
* **Authentication:** Django’s built-in session-based authentication (secure, fast, and integrated).
* **Timezone:** `Asia/Manila`.
* **Audit & Archive:** Managed via Django service layer (model-level logic), **not** database triggers.
* **Deployment:** Works seamlessly on localhost or LAN setup; optional upgrade to WSGI/ASGI server for production.
* **Performance Note:** Lightweight — all page updates handled via HTMX partial requests, minimizing full reloads.
---

## 🧠 **Data Flow Summary**

```
Admission → creates Student + Curriculum assignment
Registrar → defines Term + creates Sections + assigns Professors
Students → enroll (validated by prereqs, sections, unit cap)
Professors → encode Grades + manage INCs
System → logs all actions + enforces deadlines
Registrar/Admin → archive old data
Dean/Admin → analyze reports + audits
```

---

