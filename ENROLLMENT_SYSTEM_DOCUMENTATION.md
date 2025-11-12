# Enhanced Enrollment System Documentation

## Overview

The new enrollment system intelligently handles student subject enrollment with support for:
- Students with and without incomplete ('inc') subjects
- Dynamic student level determination based on academic history
- Smart prerequisite checking that accepts incomplete but passing subjects
- Comprehensive grade history tracking
- 30-unit maximum per term enforcement

## Key Features

### 1. Helper Functions (enrollment/student_enrollment_views.py)

#### `get_student_grade_history(student)`
**Purpose:** Retrieve all subjects a student has taken with grades and status

**Returns:** List of dicts containing:
- `student_subject`: StudentSubject record
- `subject`: Subject object
- `term`: Term object
- `professor`: Assigned professor
- `status`: Current status (completed, failed, inc, repeat_required)
- `grade`: Grade value or "Not Posted"
- `grade_value`: Numeric grade or None

**Usage:**
```python
grade_history = get_student_grade_history(student)
```

---

#### `get_completed_subjects_with_grades(student)`
**Purpose:** Get all subjects with 'completed' status and their grade values

**Returns:** Dict with subject_id as key:
```python
{
    subject_id: {
        'grade_value': float,
        'subject': Subject,
        'status': 'completed'
    }
}
```

**Usage:**
```python
completed = get_completed_subjects_with_grades(student)
for subject_id, data in completed.items():
    print(f"{data['subject'].code}: {data['grade_value']}")
```

---

#### `get_incomplete_subjects(student)`
**Purpose:** Retrieve all subjects with 'inc' status

**Returns:** QuerySet of StudentSubject records with status='inc'

**Usage:**
```python
incomplete = get_incomplete_subjects(student)
print(f"Student has {incomplete.count()} incomplete subjects")
```

---

#### `get_student_current_level(student)`
**Purpose:** Determine student's current year/semester based on academic history

**Algorithm:**
1. Find all subjects student has completed or failed
2. Match against curriculum to find highest year/semester completed
3. Advance to next semester or next year's first semester
4. Default to (1, 1) for new students

**Returns:** Tuple `(year_level, term_no)`
- year_level: 1-4 (or more)
- term_no: 1 or 2

**Example:**
```python
year, term = get_student_current_level(student)
print(f"Student is in Year {year}, Semester {term}")
```

---

#### `check_prerequisite_with_grades(student, subject, passing_grade=None)`
**Purpose:** Smart prerequisite checking that accepts:
- Completed subjects with any grade
- Incomplete subjects where grade meets or exceeds passing grade

**Parameters:**
- `student`: Student object
- `subject`: Subject to check prerequisites for
- `passing_grade`: Optional override (defaults to program's passing_grade)

**Returns:** Dict with keys:
```python
{
    'can_take': bool,           # Can student take this subject?
    'unmet': [Subject, ...],    # Prerequisites NOT met
    'with_inc': [               # Prerequisites met via incomplete
        {
            'subject': Subject,
            'grade': grade_value,
            'status': 'incomplete_but_passing'
        }
    ]
}
```

**Example:**
```python
check = check_prerequisite_with_grades(student, calculus_ii)
if check['can_take']:
    print("All prerequisites met!")
else:
    print(f"Missing: {[s.code for s in check['unmet']]}")
```

---

#### `get_available_subjects_for_student(student, active_term, include_inc_path=False)`
**Purpose:** Get all subjects available for enrollment, considering:
- Student's current level
- Prerequisites status
- Whether student has incomplete subjects

**Parameters:**
- `student`: Student object
- `active_term`: Current term
- `include_inc_path`: If True, allow enrollment in next level if student has incomplete subjects

**Returns:** Tuple of:
1. List of subject dicts with keys:
   - `subject`: Subject object
   - `curriculum_level`: (year, semester) in curriculum
   - `current_level`: Student's current level
   - `can_take`: bool
   - `unmet_prereqs`: [Subject, ...]
   - `with_inc_prereqs`: [Subject info dicts]
   - `is_available`: bool
2. `has_inc`: bool - whether student has incomplete subjects

**Example:**
```python
available, has_incomplete = get_available_subjects_for_student(
    student, active_term, include_inc_path=True
)

for item in available:
    if item['can_take']:
        print(f"✓ {item['subject'].code} - Available")
    else:
        unmet = [s.code for s in item['unmet_prereqs']]
        print(f"✗ {item['subject'].code} - Missing: {unmet}")
```

---

## Views

### `student_enroll_subjects(request)`
**Route:** `/enrollment/student/subjects/`

**Functionality:**
1. Check student onboarding status
2. Get active term
3. Determine student's current level
4. Get available subjects using smart prerequisite checking
5. Retrieve grade history
6. Handle POST: Validate selections and store in session

**Context Variables:**
- `student`: Student object
- `active_term`: Current term
- `available_subjects`: List of available subject dicts
- `grade_history`: Student's grade history
- `incomplete_subjects`: Queryset of incomplete subjects
- `has_incomplete`: bool
- `current_level`: (year, semester)

**Validations:**
- At least one subject selected
- Total units ≤ 30
- All prerequisites met
- No double enrollment in same subject/term

---

### `student_confirm_enrollment(request)`
**Route:** `/enrollment/student/confirm/`

**Functionality:**
1. Display enrollment summary
2. On POST: Create Enrollment and StudentSubject records
3. Record audit trail
4. Clear session data

*Note: This view remains largely unchanged*

---

### `student_view_enrollment(request, term_id)`
**Route:** `/enrollment/student/term/<term_id>/`

**Functionality:**
Display student's enrolled subjects for a specific term

*Note: This view remains unchanged*

---

### `student_grade_history(request)`
**Route:** `/enrollment/student/grade-history/`

**Functionality:**
1. Retrieve complete grade history
2. Calculate GPA (only from completed subjects)
3. Display statistics: completed, failed, incomplete counts
4. Render detailed grade history table

**Context Variables:**
- `student`: Student object
- `grade_history`: List of grade history dicts
- `gpa`: Calculated GPA or None
- `total_completed`: int
- `total_failed`: int
- `total_incomplete`: int

---

### `api_check_prerequisites(request)`
**Route:** `/enrollment/api/prerequisites/?subject_id=<id>`

**Functionality:**
JSON API for real-time prerequisite checking

**Response:**
```json
{
    "subject_code": "CALCULUS II",
    "prerequisites": [
        {
            "code": "CALCULUS I",
            "title": "Calculus I",
            "is_met": true,
            "status": "completed"
        },
        {
            "code": "ALGEBRA",
            "title": "Linear Algebra",
            "is_met": false,
            "status": "unmet"
        }
    ],
    "all_met": false,
    "unmet_count": 1,
    "unmet_subjects": [
        {"code": "ALGEBRA", "title": "Linear Algebra"}
    ]
}
```

---

## Templates

### `templates/student/enroll_subjects.html`
**Features:**
- Tab-based interface (Available Subjects & Grade History)
- Expandable prerequisite details
- Real-time unit total calculation
- Unit limit warning (> 30 units)
- Summary sidebar showing:
  - Current level
  - Incomplete subjects list
  - Selected subjects count
  - Total units
- Incomplete subjects alert

**Key Elements:**
- Select all/none checkbox
- Status indicators (Ready/Blocked)
- Clickable "Blocked" status to show prerequisite details
- Grade history table (separate tab)

---

### `templates/student/grade_history.html`
**Features:**
- Summary cards: GPA, Completed, Failed, Incomplete counts
- Detailed grade table with all subjects
- Color-coded grade circles (green ≥3.0, blue ≥2.0, red <2.0)
- Status badges with icons
- Breakdown statistics
- Responsive design

---

## Database Models

No new models were created. The system uses existing models:
- `StudentSubject` - with status choices: enrolled, completed, failed, inc, repeat_required
- `Grade` - stores grade values
- `Prereq` - prerequisite relationships
- `CurriculumSubject` - maps subjects to year/semester in curriculum
- `Program` - contains passing_grade threshold

---

## Enrollment Flow

### For New Student (No History)
1. System determines level: Year 1, Semester 1
2. Shows only 1st year, 1st semester subjects
3. All subjects with no prerequisites shown as "Ready"
4. Subjects with prerequisites shown as "Blocked"
5. Student can only enroll in subjects where all prerequisites are completed

### For Student with Completed Subjects
1. System determines level based on highest completed subject
2. Shows subjects at current level
3. Prerequisite checking considers:
   - Completed subjects (any grade)
   - Incomplete subjects with passing grade
4. If grade ≥ passing_grade, incomplete subject counts as prerequisite

### For Student with Incomplete Subjects
1. Same level determination as above
2. System shows:
   - Subjects at current level
   - Subjects at next level (if `include_inc_path=True`)
3. Alert shows count of incomplete subjects
4. Incomplete subjects listed in sidebar
5. Prerequisites can be met via:
   - Completed subjects
   - Incomplete subjects with passing grade

---

## Example Scenarios

### Scenario 1: New Freshman
- No prior courses taken
- Level: Year 1, Semester 1
- Available: All 1st year, 1st semester subjects with no prerequisites
- Blocked: Subjects requiring prerequisites

### Scenario 2: Student with Inc Grade > Passing
- Took Math 101 (incomplete) with grade 2.5, program passing grade 2.0
- Tried to take Calculus I which requires Math 101
- **Result:** Can enroll in Calculus I (incomplete prerequisite meets passing grade)

### Scenario 3: Student with Inc Grade < Passing
- Took Physics 101 (incomplete) with grade 1.5, program passing grade 2.0
- Tried to take Physics 102 which requires Physics 101
- **Result:** Cannot enroll (incomplete prerequisite fails passing grade threshold)

### Scenario 4: Student Exceeding Unit Limit
- Selects subjects totaling 35 units
- Submit button disabled
- Warning message: "Exceeds 30 units"

---

## Configuration

### Per-Program Passing Grade
Located in `Program` model:
```python
passing_grade = models.DecimalField(max_digits=3, decimal_places=2, default=3.00)
```

Modify in Django admin to change passing grade threshold per program.

### Maximum Units Per Term
Hardcoded to 30 units in `student_enroll_subjects()` view.

To change:
```python
if total_units > 30:  # Change 30 to desired limit
    messages.error(request, f'Total units ({total_units}) exceeds maximum of 30 units.')
```

---

## Testing Checklist

### Basic Functionality
- [ ] New student can enroll in first-year subjects
- [ ] Cannot enroll in subjects with unmet prerequisites
- [ ] Cannot exceed 30-unit limit
- [ ] Multiple subjects can be selected
- [ ] Grade history displays correctly
- [ ] GPA calculated only from completed subjects

### Incomplete Subject Handling
- [ ] Student with incomplete subjects sees warning
- [ ] Incomplete subjects listed in sidebar
- [ ] Can progress to next level with incomplete subjects
- [ ] Incomplete subject with passing grade satisfies prerequisites
- [ ] Incomplete subject with failing grade blocks prerequisites

### Data Integrity
- [ ] No double enrollment in same subject/term
- [ ] Enrollment creates Enrollment record with correct total units
- [ ] StudentSubject records created for each selected subject
- [ ] Audit trail recorded for enrollment confirmation

### UI/UX
- [ ] Tab switching works (Subjects vs Grade History)
- [ ] Prerequisite details expand/collapse on click
- [ ] Select all/none checkbox works
- [ ] Unit total updates in real-time
- [ ] Unit warning appears when > 30 units
- [ ] All status badges display correctly

---

## API Endpoints

### Check Prerequisites
**Endpoint:** `GET /enrollment/api/prerequisites/?subject_id=<id>`

**Authentication:** Required (login_required)

**Response:** JSON with prerequisite status

**Use Cases:**
- Real-time prerequisite validation in forms
- AJAX tooltip showing prerequisite status
- Programmatic verification

---

## Migration Notes

If updating from previous enrollment system:

1. No database migrations needed (uses existing models)
2. Update templates or use new ones
3. Update URL patterns if needed
4. Clear Django cache if issues arise

---

## Performance Considerations

### Database Queries
- Functions use `.select_related()` and `.filter()` for efficiency
- Grade history uses single database query
- Prerequisite checking is O(n) where n = number of prerequisites

### Optimization Tips
- Consider caching grade history for students who don't change frequently
- Use database indexing on StudentSubject.status
- Batch prerequisite checking if handling multiple subjects

---

## Future Enhancements

1. **Concurrent Enrollment Paths**
   - Allow different subject sequences based on student choice
   - Track alternative curriculum paths

2. **Grade-Based Progression**
   - Automatically unlock next-level subjects when previous is completed
   - Block subjects if GPA falls below threshold

3. **Wait Lists**
   - Allow students to request enrollment if section is full
   - Email notification when spot opens

4. **Bulk Operations**
   - Import student enrollments from CSV
   - Export grade reports in various formats

5. **Predictive Enrollment**
   - Suggest subjects based on curriculum requirements
   - Warn about bottleneck prerequisites

---

## Troubleshooting

### Issue: Student can't see available subjects
**Solution:** Check:
1. `onboarding_complete` is True
2. Active term exists for student's program level
3. Curriculum is assigned to student
4. CurriculumSubject records exist for the term

### Issue: Incomplete subjects not counted as prerequisites
**Solution:**
1. Verify Grade record exists for the StudentSubject
2. Check grade value is >= Program.passing_grade
3. Ensure StudentSubject.status = 'inc'

### Issue: GPA calculation incorrect
**Solution:**
1. Only completed subjects with posted grades are counted
2. Verify Grade records exist for all completed subjects
3. Check Program.passing_grade is set correctly

---

## Support

For issues or questions, contact the development team with:
- Student username
- Subject code attempting to enroll in
- Error message (if any)
- Current term name
