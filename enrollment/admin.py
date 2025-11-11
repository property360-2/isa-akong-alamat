from django.contrib import admin
from .models import Student, Term, Section, StudentSubject


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'program', 'curriculum', 'status', 'created_at')
    list_filter = ('status', 'program')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    ordering = ('-created_at',)


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'add_drop_deadline', 'grade_encoding_deadline', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('-start_date',)


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('section_code', 'subject', 'term', 'professor', 'capacity', 'status', 'created_at')
    list_filter = ('status', 'term', 'subject__program')
    search_fields = ('section_code', 'subject__code', 'subject__title', 'professor__username')
    ordering = ('-created_at',)


@admin.register(StudentSubject)
class StudentSubjectAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'section', 'term', 'professor', 'status', 'created_at')
    list_filter = ('status', 'term')
    search_fields = ('student__user__username', 'subject__code', 'subject__title')
    ordering = ('-created_at',)
