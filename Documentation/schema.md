# 🧩 **RICHWELL SCHOOL PORTAL – DATABASE SCHEMA v2.0**

---

### 1. `Users`

All system users, from admins to students.

```sql
Users (
  id              BIGINT PRIMARY KEY,
  username        VARCHAR(100) UNIQUE NOT NULL,
  password_hash   TEXT NOT NULL,
  role            ENUM('student','professor','registrar','dean','admission','admin') NOT NULL,
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 2. `Programs`

Academic programs (BSCS, ABM, HUMSS, etc.)

```sql
Programs (
  id              BIGINT PRIMARY KEY,
  name            VARCHAR(255) NOT NULL,             
  level           ENUM('SHS','College','Bachelor','Masteral') NOT NULL,
  passing_grade   DECIMAL(3,2) DEFAULT 3.00,
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 3. `Curricula`

CHED/DepEd curriculum versions.

```sql
Curricula (
  id              BIGINT PRIMARY KEY,
  program_id      BIGINT REFERENCES Programs(id),
  version         VARCHAR(50) NOT NULL,               -- e.g. "CHED 2021 Rev"
  effective_sy    VARCHAR(20) NOT NULL,               -- e.g. "AY 2021-2022"
  active          BOOLEAN DEFAULT TRUE,
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 4. `Subjects`

Academic subjects with recommended year/sem and type.

```sql
Subjects (
  id                  BIGINT PRIMARY KEY,
  program_id          BIGINT REFERENCES Programs(id),
  code                VARCHAR(50) UNIQUE NOT NULL,   -- e.g. "CS101"
  title               VARCHAR(255) NOT NULL,         -- e.g. "Intro to Computing"
  description         TEXT,
  units               DECIMAL(3,1),
  type                ENUM('major','minor') DEFAULT 'minor',
  recommended_year    INT,                           -- e.g. 1, 2, 3, 4
  recommended_sem     INT,                           -- e.g. 1 = 1st sem, 2 = 2nd sem
  active              BOOLEAN DEFAULT TRUE,
  created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 5. `Prereqs`

Links subjects with their prerequisites.

```sql
Prereqs (
  id                  BIGINT PRIMARY KEY,
  subject_id          BIGINT REFERENCES Subjects(id),
  prereq_subject_id   BIGINT REFERENCES Subjects(id)
);
```

---

### 6. `CurriculumSubjects`

Curriculum-to-subject mapping for versioned programs.

```sql
CurriculumSubjects (
  id               BIGINT PRIMARY KEY,
  curriculum_id    BIGINT REFERENCES Curricula(id),
  subject_id       BIGINT REFERENCES Subjects(id),
  year_level       INT,
  term_no          INT,
  is_recommended   BOOLEAN DEFAULT TRUE,
  created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 7. `Students`

Student info, linked to users, program, and curriculum.

```sql
Students (
  id              BIGINT PRIMARY KEY,
  user_id         BIGINT REFERENCES Users(id),
  program_id      BIGINT REFERENCES Programs(id),
  curriculum_id   BIGINT REFERENCES Curricula(id),
  status          ENUM('active','inactive','graduated') DEFAULT 'active',
  documents_json  JSON,                              -- {"tor":"tor.pdf","id":"id.png"}
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 8. `Terms`

Defines semesters/trimesters per academic year.

```sql
Terms (
  id              BIGINT PRIMARY KEY,
  name            VARCHAR(50) NOT NULL,              -- e.g. "1st Semester AY 2025-2026"
  start_date      DATE NOT NULL,
  end_date        DATE NOT NULL,
  add_drop_deadline DATE,
  grade_encoding_deadline DATE,
  is_active       BOOLEAN DEFAULT FALSE,
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 9. `Sections`

Each subject offering per term (tied to a professor).

```sql
Sections (
  id              BIGINT PRIMARY KEY,
  subject_id      BIGINT REFERENCES Subjects(id),
  term_id         BIGINT REFERENCES Terms(id),
  professor_id    BIGINT REFERENCES Users(id),
  section_code    VARCHAR(20) NOT NULL,              -- e.g. "CS101-A"
  capacity        INT DEFAULT 40,
  status          ENUM('open','full','closed') DEFAULT 'open',
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(subject_id, term_id, section_code)
);
```

---

### 10. `StudentSubjects`

Student’s enrolled subjects per term + section.

```sql
StudentSubjects (
  id              BIGINT PRIMARY KEY,
  student_id      BIGINT REFERENCES Students(id),
  subject_id      BIGINT REFERENCES Subjects(id),
  term_id         BIGINT REFERENCES Terms(id),
  section_id      BIGINT REFERENCES Sections(id),
  professor_id    BIGINT REFERENCES Users(id),
  status          ENUM('enrolled','completed','failed','inc','repeat_required') DEFAULT 'enrolled',
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 11. `Grades`

Professor-submitted grades per subject.

```sql
Grades (
  id                  BIGINT PRIMARY KEY,
  student_subject_id  BIGINT REFERENCES StudentSubjects(id),
  subject_id          BIGINT REFERENCES Subjects(id),
  professor_id        BIGINT REFERENCES Users(id),
  grade               VARCHAR(10) NOT NULL,          -- e.g. "1.75", "INC", "5.00"
  posted_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 12. `AuditTrail`

Logs every major modification in the system.

```sql
AuditTrail (
  id              BIGINT PRIMARY KEY,
  actor_id        BIGINT REFERENCES Users(id),
  action          VARCHAR(100) NOT NULL,             
  entity          VARCHAR(100) NOT NULL,             
  entity_id       BIGINT,                            
  old_value_json  JSON,
  new_value_json  JSON,
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 13. `Archive`

One unified archive for any entity.

```sql
Archive (
  id              BIGINT PRIMARY KEY,
  entity          VARCHAR(100) NOT NULL,             -- e.g. "Students", "Grades", "Terms"
  entity_id       BIGINT,
  data_snapshot   JSON NOT NULL,                     -- full JSON of the original record
  reason          VARCHAR(255),                      -- e.g. "Graduated", "Term Closed"
  archived_by     BIGINT REFERENCES Users(id),
  archived_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 14. 🧩 `Settings`

Global system control table (your new toggle table).

```sql
Settings (
  id              BIGINT PRIMARY KEY,
  key_name        VARCHAR(100) UNIQUE NOT NULL,      -- e.g. "admission_link_enabled"
  value_text      VARCHAR(255) NOT NULL,             -- e.g. "true", "false", "30"
  description     VARCHAR(255),                      -- optional human note
  updated_by      BIGINT REFERENCES Users(id),
  updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Sample keys:**

| key_name               | value_text  | description                       |
| ---------------------- | ----------- | --------------------------------- |
| admission_link_enabled | true        | Enable/disable admission form     |
| enrollment_open        | false       | Allow or block student enrollment |
| freshman_unit_cap      | 30          | Unit limit for freshmen           |
| passing_grade          | 3.00        | Default passing grade             |
| timezone               | Asia/Manila | System timezone                   |

---

## ⚙️ **Core Rules Recap**

| Rule                 | Description                                                  |
| -------------------- | ------------------------------------------------------------ |
| **Freshman Cap**     | Max 30 units for new students (`Settings.freshman_unit_cap`) |
| **Prerequisites**    | Must pass/credit prereq subjects                             |
| **Recommended Flow** | Based on `recommended_year` and `recommended_sem`            |
| **INC Lifecycle**    | Repeat required if uncompleted within deadline               |
| **Sections**         | Students enroll per section, tied to professor               |
| **Professor Access** | Professors see and grade only their sections                 |
| **Archiving**        | Old data snapshots stored in `Archive`                       |
| **Settings**         | Controls system toggles (admission, enrollment, etc.)        |
| **AuditTrail**       | Every change logged for accountability                       |

---

## 🔗 **Relationship Overview**

```
Users ─┐
       ├── Professors → Sections → StudentSubjects → Grades
       └── Students ─┐
Programs ─┐           │
Curricula ─┤           └──> linked via CurriculumSubjects
Subjects ──┘
Prereqs  ───> Subject dependency
Terms ─────┬──> Sections
            └──> StudentSubjects
Settings ──> system controls
Archive ←─── all entities for data preservation
AuditTrail ← logs all changes
```

---
