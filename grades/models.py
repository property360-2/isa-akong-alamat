# grades/models.py
from django.db import models
from enrollment.models import StudentSubject
from users.models import User
from academics.models import Subject

class Grade(models.Model):
    student_subject = models.ForeignKey(StudentSubject, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    professor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'professor'})
    grade = models.CharField(max_length=10)
    posted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_subject.student.user.username} - {self.grade}"
