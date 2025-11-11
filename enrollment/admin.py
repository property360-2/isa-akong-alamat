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
    list_display = ('section_code', 'get_subjects_display', 'term', 'get_professors_display', 'capacity', 'status', 'created_at')
    list_filter = ('status', 'term')
    search_fields = ('section_code', 'subjects__code', 'subjects__title', 'professors__username')
    ordering = ('-created_at',)
    filter_horizontal = ('subjects', 'professors')

    def get_subjects_display(self, obj):
        return ', '.join([s.code for s in obj.subjects.all()])
    get_subjects_display.short_description = 'Subjects'

    def get_professors_display(self, obj):
        return ', '.join([p.get_full_name() or p.username for p in obj.professors.all()])
    get_professors_display.short_description = 'Professors'


@admin.register(StudentSubject)
class StudentSubjectAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'section', 'term', 'professor', 'status', 'created_at')
    list_filter = ('status', 'term')
    search_fields = ('student__user__username', 'subject__code', 'subject__title')
    ordering = ('-created_at',)
