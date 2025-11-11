# 🧭 **RICHWELL SCHOOL PORTAL – REGISTRAR MODULE STRUCTURE**

---

## 🧱 **1. Programs, Curricula, and Subjects**

### 🔹 **Main Page: `/registrar/academics/`**

## **Purpose:** Central hub for academic structure.

### ### **A. Programs Tab**

**URL:** `/registrar/academics/programs/`
**UI Layout:**

- Table: `Program Name | Level | Passing Grade | Actions (Edit, Deactivate)`
- Button: `+ Add Program`

**Actions:**

1. **Add Program**

   - Opens modal: `Name`, `Level`, `Passing Grade`.
   - Backend: `POST /programs/create/`
   - Creates record in `Programs`.

2. **Edit Program**

   - Inline edit in table (HTMX partial).
   - Updates `Programs`.

3. **Deactivate**

   - Sets status inactive (soft delete).

---

### ### **B. Curricula Tab**

**URL:** `/registrar/academics/curricula/`
**UI Layout:**

- Table: `Program | Version | Effective SY | Active | Actions (Edit, Duplicate)`
- Buttons: `+ New Curriculum`, `Duplicate Existing`

---

**Actions:**

1. **Add New Curriculum**

   - Modal Fields:

     - `Program` – select from existing programs
     - `Version` – string or numeric (e.g. `2025 Rev A`)
     - `Effective SY` – text or date range (e.g. `2025–2026`)

   - Backend: `POST /curricula/create/`

   - Creates a record in `Curricula` table linked to the chosen program.

   - Automatically sets `active=False` (until manually activated).

---

2. **Duplicate Curriculum**

   - Action Button: “Duplicate” on any curriculum row.

   - Opens modal:

     - Field: `New Curriculum Name` (must be unique).
     - Field: optional `Effective SY` (auto-filled with next school year).
     - Confirm button: “Duplicate Curriculum”.

   - Backend:

     - Copies selected curriculum data and its associated `CurriculumSubjects` records.
     - Saves as a new curriculum with the provided name.
     - Logs duplication event in `AuditTrail` for traceability.

   - **Success Feedback:**

     - After duplication, a transient **toast notification** appears at the top-right corner:

       ```
       ✅ “<Curriculum Name> created successfully.”
       [View Curriculum]
       ```

     - The toast lasts for **5 seconds** and disappears automatically.
     - “View Curriculum” button redirects to the new curriculum’s detail page (`/registrar/academics/curricula/{id}/`).

---

3. **Activate / Deactivate Curriculum**

   - Toggle switch in table under “Active” column.
   - Backend ensures only **one active curriculum per program**.
   - When toggled ON, all other curricula under the same program are automatically deactivated.
   - Changes are logged to `AuditTrail`.

---

4. **Open Curriculum Detail View**

   - URL: `/registrar/academics/curricula/{id}/`
   - Displays:

     - **Header:** Curriculum name, version, program, and status.
     - **Tabs:**

       - `Subjects` – lists all mapped subjects (via `CurriculumSubjects`).
       - `Prerequisites` – shows subject dependency map for quick validation.

---

**Content Summary:**

- Create, duplicate, and manage curriculum versions linked to academic programs.
- Duplication includes subject mappings for faster setup of new revisions.
- Unique curriculum name enforcement prevents version conflicts.
- 5-second success notification with “View Curriculum” shortcut enhances UX feedback.
- Activation system enforces single active version per program.

---

### ### **C. Subjects Tab**

**URL:** `/registrar/academics/subjects/`
**UI Layout:**

- Table: `Code | Title | Units | Type | Year | Sem | Program | Actions`
- Buttons: `+ Add Subject`, `Bulk Import CSV` (optional)

---

**Actions:**

1. **Add Subject**

   - Modal fields:

     - `Code` – unique subject code (e.g. CS101)
     - `Title` – full subject name
     - `Units` – numeric value (e.g. 3)
     - `Type` – dropdown (`Major`, `Minor`, `Elective`, `PE`, etc.)
     - `Recommended Year` – dropdown (1–4)
     - `Recommended Semester` – dropdown (`1st`, `2nd`, `Summer`)
     - `Program` – select from existing programs
     - `Has Prerequisite?` – checkbox toggle (default: unchecked)

   - When “Has Prerequisite?” is **unchecked**:
     The form remains simple — subject can be saved directly.

   - When “Has Prerequisite?” is **checked**:
     A new field appears **below** the checkbox labeled `Select Prerequisites`.

     - Includes a **live search input** where the registrar can type to find existing subjects.
     - Displays search results (subject code + title).
     - Selected subjects appear as **tags** (removable).
     - On save, each selected subject is linked as a prerequisite.

   - Backend: `POST /subjects/create/`

     - Creates record in `Subjects`.
     - If prerequisites are provided, creates multiple entries in `Prereqs` table.

---

2. **Edit Subject**

   - Action button on the table row opens modal pre-filled with subject data.
   - “Has Prerequisite?” checkbox automatically checked if prerequisites exist.
   - Selected prerequisites are displayed as tags (removable).
   - Backend: `PUT /subjects/{id}/update/`
   - If prerequisites are modified, existing ones are replaced with the updated list.

---

3. **Map to Curriculum**

   - Action button “Add to Curriculum” opens modal:

     - `Curriculum` – select from existing curricula
     - `Year` – select level
     - `Semester` – select term
     - `Recommended` – toggle on/off

   - Backend: creates entry in `CurriculumSubjects`.

   - Purpose:
     Links the subject to a curriculum with its recommended placement in the year/term sequence.

---

4. **Assign Prerequisites**

   - Available in subject details page.
   - Section shows:

     - Existing prerequisites (displayed as tags with remove option).
     - Search bar to add new prerequisite subjects (with live search dropdown).

   - Backend endpoints:

     - `GET /subjects/search/?q=term` – live search suggestions
     - `POST /prereqs/add/` – add prerequisite
     - `DELETE /prereqs/{id}/remove/` – remove prerequisite

---

**Content Summary:**

- CRUD for Subjects (add, edit, deactivate).
- Integrated prerequisite management via checkbox and live search.
- Mapping subjects to specific curricula and academic terms.
- Consistent UX for managing dependencies directly from the subject modal.
- Backend handles multi-prerequisite creation atomically for consistency.

---

## 🧮 **2. Term Management**

### 🔹 **Main Page: `/registrar/terms/`**

**Purpose:** Manage semesters/trimesters and control academic timeline.

**UI Layout:**

- Header: `Active Term: 1st Semester AY 2025-2026`
- Buttons: `+ New Term`, `Activate`, `Close Term`
- Table: `Name | Start Date | End Date | Active | Created At | Actions`

**Actions:**

1. **Add New Term**

   - Modal Fields:
     `Name`, `Start Date`, `End Date`, `Add/Drop Deadline`, `Grade Deadline`.
   - Backend: `POST /terms/create/`.

2. **Activate Term**

   - Action: only one term active.
   - Backend logic:

     - Deactivate existing term.
     - Set `is_active=True` for selected term.

   - Updates all session-level data for enrollment.

3. **Close Term**

   - Confirms → marks `is_active=False`.
   - Triggers archive (future module).
   - Backend: `POST /terms/{id}/close/`.

**Content Summary:**

- Term lifecycle management.
- One-active-term rule enforced at model/service layer.
- Hooks for auto-archive and reports later.

---

## 🧩 **3. Section Management**

### 🔹 **Main Page:** `/registrar/sections/`

**Purpose:** Manage subject offerings per term, assign professors, and control section capacity.

---

**UI Layout:**

- Dropdown: Select **Active Term**
- Table: `Section Code | Subject | Professor(s) | Capacity | Status | Actions`
- Buttons: `+ Add Section`, `Bulk Create Sections`

---

**Actions:**

### 1. **Add Section**

- Modal Fields:

  - **Subject** – search field with live results (`Search Subject…`)
  - **Section Code** – auto-generated (e.g. `CS101-A`), editable
  - **Capacity** – numeric input (default: 40)
  - **Assigned Professors** – searchable multi-add field

---

#### **Professor Management (inside Add/Edit Modal)**

**UI Behavior:**

- Section at the bottom labeled **“Assigned Professors”**
- Default view:

  ```
  [ 🔍 Search Professor... ]   [ + Add Professor ]
  ```

- Typing triggers **live search** (HTMX GET `/users/search/?role=professor&q=…`)
  Results show as:

  ```
  • Prof. John Dela Cruz (CS Department)
  • Prof. Maria Reyes (Math Department)
  ```

- Clicking a result adds it as a **tag**:

  ```
  Selected Professors:
  [Prof. John Dela Cruz ✕] [Prof. Maria Reyes ✕]
  ```

- Clicking ✕ removes that professor immediately (no reload).
- “+ Add Professor” re-opens the search input to append more names.
- Works the same way during edit.

**Backend:**

- Endpoint: `POST /sections/create/`
- Payload example:

  ```json
  {
    "subject_id": 12,
    "section_code": "CS101-A",
    "capacity": 40,
    "professors": [5, 7]
  }
  ```

- Backend creates one `Section` record tied to the active term and inserts multiple professor links (either a join table or a JSON array).
- Each add/remove triggers `AuditTrail` entries:

  ```
  Action: "update_professor_assignment"
  Entity: "Sections"
  Entity ID: 23
  Old Value: {"professors": [5]}
  New Value: {"professors": [5,7]}
  ```

---

### 2. **Edit Section**

- Opens pre-filled modal showing existing subject and professors.
- “Assigned Professors” area uses the same search-based selector.
- Removing all professors and saving leaves section unassigned.
- Backend: `PUT /sections/{id}/update/`

---

### 3. **Bulk Create**

- Modal Fields:

  - `Subject` – searchable input
  - `Number of Sections` – numeric
  - `Capacity` – optional override

- Backend auto-generates codes:

  ```
  CS101-A
  CS101-B
  CS101-C
  ```

- Endpoint: `POST /sections/bulk_create/`

---

### 4. **Assign Professor (Quick Edit)**

- Inline action in main table.
- Opens small popover with **search field**:

  ```
  🔍 Search Professor...
  ```

- Selecting a name instantly updates backend (`PATCH /sections/{id}/assign_professor/`).

---

### 5. **Change Section Status**

- Inline toggle in table row: `open → full → closed`
- Backend: `PATCH /sections/{id}/status/`
- Closed sections are hidden from student enrollment lists.

---

**Content Summary:**

- Manual and bulk section creation.
- **Search-based professor assignment** with live suggestions.
- Multi-professor support using tag-style selection.
- Full CRUD for capacity and status.
- Every update logged in `AuditTrail`.
- Term-aware filtering ensures clean semester management.
- Designed for future link to professors’ grading dashboards.

---

## 🧍‍♂️ **4. Student Admissions (Registrar Access, lets not think about this now, lets just add a template with no functions)**

### 🔹 **Main Page: `/registrar/admissions/`**

**Purpose:** Handle transferee applications and validate academic records.

**UI Layout:**

- Tabs: `Pending | Approved | Rejected`
- Table: `Student Name | Program | Type | TOR | Status | Actions`

**Actions:**

1. **View Applicant**

   - Opens details modal or page.
   - Displays:

     - Personal info
     - Uploaded TOR
     - Preferred Program

2. **Validate & Approve**

   - Registrar selects:

     - `Program`
     - `Curriculum`
     - Credited Subjects (multiselect)

   - Backend:

     - Creates `Users` + `Students`
     - Inserts credited entries into `StudentSubjects` with `status='completed'`.

3. **Reject Application**

   - Marks as `rejected`.
   - Optional notes field.

**Content Summary:**

- Only Registrar has access.
- Converts applicant data into valid student record.
- Auto-links to chosen curriculum.

---

## ⚙️ **5. Settings Management (Enrollment Toggle Only as of now)**

### 🔹 **Main Page: `/registrar/settings/`**

**Purpose:** Manage system-wide configurations.

**UI Layout:**

- Simple table:
  `Key Name | Value | Description | Last Updated | Actions`
- Only one key for now: `enrollment_open`

**Actions:**

1. **Toggle Enrollment**

   - Switch button `ON/OFF`
   - Backend: `PATCH /settings/enrollment_open/`
   - Logs change in `AuditTrail`.

**Content Summary:**

- Minimal config page.
- Direct backend binding to global toggle state.

---

# 🧩 **Page Flow Overview**

```
Registrar Dashboard
 ├─ Academics
 │   ├─ Programs
 │   ├─ Curricula (with duplicate & map subjects)
 │   └─ Subjects (with prerequisites)
 ├─ Terms (Create / Activate / Close)
 ├─ Sections (manual or bulk creation)
 ├─ Admissions (validate transferees)
 └─ Settings (toggle enrollment)
```

---

# 🧠 **Development Notes**

- **Backend:** Django views per module (CBV or HTMX endpoints).
- **Frontend:** HTMX for modal forms, Alpine.js for interactivity.
- **Data Validation:** handled in `services.py` for clean separation.
- **AuditTrail:** decorator-based logger for each CRUD action.

---
