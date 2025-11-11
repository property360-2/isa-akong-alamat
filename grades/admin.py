from django.contrib import admin
from .models import Grade


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student_subject', 'subject', 'professor', 'grade', 'posted_at')
    list_filter = ('grade', 'posted_at')
    search_fields = ('student_subject__student__user__username', 'subject__code', 'professor__username')
    ordering = ('-posted_at',)
