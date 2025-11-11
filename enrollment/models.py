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
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    documents_json = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.program.name})"


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
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    professor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'professor'})
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')
    created_at = models.DateTimeField(auto_now_add=True)
