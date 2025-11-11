# 🧭 **RICHWELL SCHOOL PORTAL – ROLE-BASED USE CASES**

---

## 👑 **Administrator**

**Overview:**
Full control over users, configuration, auditing, and system-level operations.
Responsible for access control, environment settings, backups, and system health.

**Use Cases:**

1. **User Account Management**

   * Create, edit, deactivate users.
   * Reset passwords or assign roles.
     *(UC-002, UC-019, UC-020)*

2. **Settings & Configuration**

   * Update dynamic system settings (enrollment toggle, unit cap, passing grade).
   * Changes automatically logged to `AuditTrail`.
     *(UC-017)*

3. **Audit Monitoring**

   * View `AuditTrail` entries for accountability (who changed what and when).
     *(UC-016)*

4. **Archive & Backup Management**

   * Export or backup entire system data for offsite storage.
     *(UC-014, UC-024)*

5. **Curriculum Oversight**

   * Approve or review new CHED curriculum migrations.
     *(UC-023)*

6. **Dashboard Access**

   * Global system overview: counts of users, active terms, logs, reports.
     *(UC-001, UC-022)*

---

## 🧾 **Registrar**

**Overview:**
Central authority for academic data, terms, curricula, and records.
Coordinates between Admission, Dean, and Professors.

**Use Cases:**

1. **Program, Curriculum, and Subject Management**

   * Create and update `Programs`, `Curricula`, and link `Subjects` with prerequisites.
     *(UC-005, UC-006, UC-023)*

2. **Term Management**

   * Create, activate, or close terms.
   * Ensure only one term is active at a time.
     *(UC-007)*

3. **Section Management**

   * Create sections per term and assign professors.
   * Modify assignments or capacities.
     *(UC-008, UC-009)*

4. **Student Admissions (with Admission role)**

   * Validate transferee records, assign curricula, and credit subjects.
     *(UC-004)*

5. **Enrollment Control**

   * Toggle `enrollment_open` setting.
   * Approve, review, or modify student enrollments manually if needed.
     *(UC-010)*

6. **Grade Finalization & INC Oversight**

   * Monitor grading completion.
   * Handle INC resolution and approvals.
     *(UC-012, UC-013)*

7. **Term Archiving**

   * Trigger archive process at term close.
     *(UC-014, UC-015)*

8. **Reporting**

   * Generate reports: enrollment summaries, grade distribution, INC tracking, utilization metrics.
     *(UC-018)*

9. **Dashboard**

   * Overview of active term, pending enrollments, grading progress, and analytics.
     *(UC-001, UC-022)*

---

## 🎓 **Dean**

**Overview:**
Departmental oversight role focusing on faculty, section utilization, and performance analytics.

**Use Cases:**

1. **Section & Faculty Monitoring**

   * View and approve section assignments.
   * Reassign professors if necessary.
     *(UC-008, UC-009)*

2. **Reporting & Analytics**

   * Access grade distribution, load balance, and performance charts.
     *(UC-018)*

3. **Curriculum Review**

   * Review new or revised curriculum versions before activation.
     *(UC-005, UC-023)*

4. **Dashboard**

   * Department-level overview: sections, active professors, and student performance metrics.
     *(UC-001, UC-022)*

---

## 🧑‍🏫 **Professor**

**Overview:**
Responsible for managing assigned sections, encoding grades, and handling INC resolutions.

**Use Cases:**

1. **Access Assigned Sections**

   * View only sections where they are assigned as instructor.
     *(UC-008)*

2. **Grade Entry**

   * Input grades per student in assigned sections.
   * Automatically updates `StudentSubjects.status`.
     *(UC-012)*

3. **INC Completion**

   * Mark resolved INCs before expiry.
     *(UC-013)*

4. **Dashboard**

   * View section summaries, class lists, and grading progress indicators.
     *(UC-001, UC-022)*

---

## 🧑‍💼 **Admission Officer**

**Overview:**
Responsible for monitoring and managing the admission data flow. The Admission Officer now focuses on **analytics, applicant monitoring, and system link control**, since enrollment and student account creation are automated.

---

**Use Cases:**

1. **Admissions Dashboard (Analytics & Monitoring)**

   * Views real-time statistics of incoming applicants (Freshman and Transferee).
   * Monitors applicant trends (daily, weekly, semester-based).
   * Displays key metrics such as:

     * Number of new applicants
     * Admission conversion rates
     * Source analytics (online vs walk-in)
       *(UC-001, UC-022)*

2. **Applicant Viewer**

   * Views all applicant details and statuses (Pending, Verified, Enrolled).
   * Filters applicants by program, date submitted, or status.
   * No longer edits or processes applications manually—used purely for review and reporting.
     *(UC-003, UC-004)*

3. **System Link Toggle**

   * Controls availability of the **Online Admission Form link**.
   * Can enable or disable admissions link visibility similar to the Admin/Registrar interface.
   * Ensures admission portal access aligns with academic calendar and system maintenance periods.
     *(UC-023)*

---

**Notes:**

* Enrollment, student creation, and curriculum assignment are handled automatically by the backend workflow.
* Admission Officer’s role is now **observational and analytical**, focusing on data accuracy, reporting, and operational readiness.

---

## 🧑‍🎓 **Student**

**Overview:**
End-user consuming the academic workflow — from admission to enrollment to viewing grades.

**Use Cases:**

1. **Login & Dashboard**

   * Access personalized dashboard showing current term, enrollment status, and grades.
     *(UC-001, UC-022)*

2. **Enrollment**

   * Add/drop eligible subjects while enrollment is open.
   * Validates prerequisites, unit caps, and section capacity.
     *(UC-010)*

3. **COR Generation**

   * Generate and download Certificate of Registration PDF.
     *(UC-011)*

4. **View Grades & INCs**

   * View finalized grades, track INCs, and monitor academic progress.
     *(UC-021)*

5. **Password Reset**

   * Recover access if password lost.
     *(UC-020)*

---

## ⚙️ **System (Automated Processes)**

**Overview:**
Background jobs and audit layers maintaining data integrity and traceability.

**Use Cases:**

1. **INC Lifecycle Enforcement**

   * Scheduled job checks grade age and updates expired INCs to `repeat_required`.
     *(UC-013)*

2. **Audit Logging**

   * Logs every critical CRUD operation automatically.
     *(UC-016)*

3. **Archive Automation**

   * Serializes and locks data on term closure.
     *(UC-014)*

---

## 🧭 **Summary of Role Dependencies**

```
Admin ─┬─ System Configuration
        ├─ User Management
        └─ Backup / Audit
Registrar ─┬─ Academic Structure
            ├─ Term / Enrollment Control
            └─ Archiving / Reports
Dean ─ Analytics & Faculty Oversight
Professor ─ Grading & INC Management
Admission ─ Student Onboarding
Student ─ Enrollment & Grade Viewing
System ─ Automation & Logging
```

