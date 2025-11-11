from django.contrib import admin
from .models import Program, Curriculum, Subject, Prereq, CurriculumSubject


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'passing_grade', 'created_at')
    list_filter = ('level',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Curriculum)
class CurriculumAdmin(admin.ModelAdmin):
    list_display = ('program', 'version', 'effective_sy', 'active', 'created_at')
    list_filter = ('active', 'program')
    search_fields = ('version', 'effective_sy')
    ordering = ('-created_at',)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'program', 'units', 'type', 'recommended_year', 'recommended_sem', 'active')
    list_filter = ('program', 'type', 'active', 'recommended_year', 'recommended_sem')
    search_fields = ('code', 'title', 'description')
    ordering = ('code',)


@admin.register(Prereq)
class PrereqAdmin(admin.ModelAdmin):
    list_display = ('subject', 'prereq_subject')
    search_fields = ('subject__code', 'subject__title', 'prereq_subject__code', 'prereq_subject__title')
    autocomplete_fields = ['subject', 'prereq_subject']


@admin.register(CurriculumSubject)
class CurriculumSubjectAdmin(admin.ModelAdmin):
    list_display = ('curriculum', 'subject', 'year_level', 'term_no', 'is_recommended', 'created_at')
    list_filter = ('curriculum', 'year_level', 'term_no', 'is_recommended')
    search_fields = ('subject__code', 'subject__title')
    ordering = ('curriculum', 'year_level', 'term_no')
