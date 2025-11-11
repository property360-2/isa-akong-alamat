# academics/models.py
from django.db import models

class Program(models.Model):
    LEVEL_CHOICES = [
        ('SHS', 'Senior High School'),
        ('College', 'College'),
        ('Bachelor', 'Bachelor'),
        ('Masteral', 'Masteral'),
    ]
    name = models.CharField(max_length=255)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    passing_grade = models.DecimalField(max_digits=3, decimal_places=2, default=3.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Curriculum(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='curricula')
    version = models.CharField(max_length=50)
    effective_sy = models.CharField(max_length=20)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.program.name} - {self.version}"


class Subject(models.Model):
    TYPE_CHOICES = [('major', 'Major'), ('minor', 'Minor')]
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    units = models.DecimalField(max_digits=3, decimal_places=1)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='minor')
    recommended_year = models.PositiveIntegerField(null=True, blank=True)
    recommended_sem = models.PositiveIntegerField(null=True, blank=True)
    active = models.BooleanField(default=True)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.title}"


class Prereq(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='subject_prereqs')
    prereq_subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='is_prerequisite_of')

    def __str__(self):
        return f"{self.prereq_subject.code} → {self.subject.code}"


class CurriculumSubject(models.Model):
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    year_level = models.PositiveIntegerField()
    term_no = models.PositiveIntegerField()
    is_recommended = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
