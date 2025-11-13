# enrollment/models.py
from django.db import models
from academics.models import Program, Curriculum, Subject
from users.models import User

class Student(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('graduated', 'Graduated'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, null=True, blank=True)
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
    onboarding_complete = models.BooleanField(default=False)
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    documents_json = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        program_name = self.program.name if self.program else "No Program"
        return f"{self.user.username} ({program_name})"


class Term(models.Model):
    LEVEL_CHOICES = [
        ('SHS', 'Senior High School'),
        ('Bachelor', 'Bachelor'),
        ('Masteral', 'Masteral'),
    ]
    name = models.CharField(max_length=50)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='Bachelor')
    start_date = models.DateField()
    end_date = models.DateField()
    add_drop_deadline = models.DateField(null=True, blank=True)
    grade_encoding_deadline = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('name', 'level')

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"


class Section(models.Model):
    STATUS_CHOICES = [('open', 'Open'), ('full', 'Full'), ('closed', 'Closed')]
    subjects = models.ManyToManyField(Subject, related_name='sections')
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    professors = models.ManyToManyField(User, related_name='sections_taught', limit_choices_to={'role': 'professor'})
    section_code = models.CharField(max_length=20)
    capacity = models.PositiveIntegerField(default=40)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('term', 'section_code')

    def __str__(self):
        subjects_list = ', '.join([s.code for s in self.subjects.all()])
        return f"{self.section_code} ({subjects_list})"

    @property
    def enrolled_count(self):
        """Count the number of enrolled students in this section"""
        return self.studentsubject_set.filter(status='enrolled').count()

    @property
    def is_full(self):
        """Check if the section is at capacity"""
        return self.enrolled_count >= self.capacity

    def get_subjects_display(self):
        """Get comma-separated list of subject codes for admin display"""
        return ', '.join([s.code for s in self.subjects.all()])

    def get_professors_display(self):
        """Get comma-separated list of professor names for admin display"""
        return ', '.join([p.get_full_name() for p in self.professors.all()])


class StudentSubject(models.Model):
    STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('inc', 'Incomplete'),
        ('repeat_required', 'Repeat Required'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True)
    professor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'professor'}, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')
    created_at = models.DateTimeField(auto_now_add=True)


class Enrollment(models.Model):
    """
    Tracks term-level enrollments for students.
    Once created, enrollment is locked - no edits or re-enrollment allowed for that term.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    total_units = models.DecimalField(max_digits=5, decimal_places=1)
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),  # Not yet confirmed
            ('confirmed', 'Confirmed'),  # Locked, cannot edit
            ('completed', 'Completed'),  # Term finished
        ],
        default='confirmed'
    )
    confirmed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'term')  # One enrollment per student per term

    def __str__(self):
        return f"{self.student.user.username} - {self.term.name}"


class TransfereeEnrollment(models.Model):
    """
    Model to track transferee enrollments before account creation.
    Registrar/Admission will manually input credentials and verify TOR.
    Once verified, account is created and student becomes a regular Student.
    """
    TRANSFER_TYPE_CHOICES = [
        ('same_school', 'Transfer within same school (different course)'),
        ('external_school', 'Transfer from another school'),
    ]
    STATUS_CHOICES = [
        ('pending_credential_input', 'Pending - Credential Input'),
        ('pending_tor_verification', 'Pending - TOR Verification'),
        ('tor_verified', 'TOR Verified - Ready for Account Creation'),
        ('account_created', 'Account Created - Transferee Account Active'),
        ('rejected', 'Rejected'),
    ]

    # Personal Information (manually input by registrar)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    suffix = models.CharField(max_length=20, blank=True)
    email = models.EmailField()
    mobile = models.CharField(max_length=20, blank=True)

    # Transfer Information
    transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPE_CHOICES)
    source_school = models.CharField(max_length=255, help_text="Name of school transferring from")
    source_program = models.CharField(max_length=255, help_text="Program name at source school")

    # Richwell Information
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True)
    curriculum = models.ForeignKey(Curriculum, on_delete=models.SET_NULL, null=True)

    # Status and Verification
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending_credential_input')
    tor_verified = models.BooleanField(default=False)
    tor_verified_at = models.DateTimeField(null=True, blank=True)
    tor_verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                       limit_choices_to={'role__in': ['registrar', 'admin']},
                                       related_name='verified_transferees')

    # Account Creation
    created_user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='transferee_enrollment')
    account_created_at = models.DateTimeField(null=True, blank=True)
    account_created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                          limit_choices_to={'role__in': ['registrar', 'admin']},
                                          related_name='created_transferee_accounts')

    # Audit
    rejection_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True, help_text="Additional notes from registrar")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_transfer_type_display()}"


class TransfereeCredit(models.Model):
    """
    Credits subjects to transferee based on verified TOR.
    Registrar will manually input subjects and grades from TOR.
    Once account is created, these credits become StudentSubject records.
    """
    STATUS_CHOICES = [
        ('credited', 'Credited'),
        ('rejected', 'Rejected'),
    ]

    transferee = models.ForeignKey(TransfereeEnrollment, on_delete=models.CASCADE, related_name='credits')
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True,
                               help_text="Subject at Richwell College")
    source_subject_code = models.CharField(max_length=50, help_text="Subject code from source school")
    source_subject_name = models.CharField(max_length=255, help_text="Subject name from source school")
    grade = models.CharField(max_length=5, help_text="Grade from TOR (e.g., 2.5, A, B+, etc.)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='credited')
    rejection_reason = models.TextField(blank=True)
    credited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   limit_choices_to={'role__in': ['registrar', 'admin']},
                                   related_name='credited_subjects')
    credited_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transferee.first_name} - {self.source_subject_code}"
