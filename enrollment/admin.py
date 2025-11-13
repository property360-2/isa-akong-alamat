from django.contrib import admin
from .models import Student, Term, Section, StudentSubject, TransfereeEnrollment, TransfereeCredit


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


class TransfereeCreditInline(admin.TabularInline):
    model = TransfereeCredit
    extra = 1
    fields = ('source_subject_code', 'source_subject_name', 'subject', 'grade', 'status', 'rejection_reason')
    readonly_fields = ('credited_at', 'credited_by')


@admin.register(TransfereeEnrollment)
class TransfereeEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'transfer_type', 'program', 'status', 'tor_verified', 'account_created_at', 'created_at')
    list_filter = ('status', 'transfer_type', 'tor_verified', 'program')
    search_fields = ('first_name', 'last_name', 'email', 'source_school', 'source_program')
    ordering = ('-created_at',)
    inlines = [TransfereeCreditInline]
    readonly_fields = ('created_at', 'updated_at', 'tor_verified_at', 'account_created_at')

    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'middle_name', 'last_name', 'suffix', 'email', 'mobile')
        }),
        ('Transfer Information', {
            'fields': ('transfer_type', 'source_school', 'source_program')
        }),
        ('Program Assignment', {
            'fields': ('program', 'curriculum')
        }),
        ('Verification Status', {
            'fields': ('status', 'tor_verified', 'tor_verified_at', 'tor_verified_by')
        }),
        ('Account Creation', {
            'fields': ('created_user', 'account_created_at', 'account_created_by')
        }),
        ('Additional Information', {
            'fields': ('notes', 'rejection_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    get_full_name.short_description = 'Full Name'

    def has_delete_permission(self, request):
        # Only admins can delete transferee records
        return request.user.is_superuser


@admin.register(TransfereeCredit)
class TransfereeCreditAdmin(admin.ModelAdmin):
    list_display = ('get_transferee_name', 'source_subject_code', 'subject', 'grade', 'status', 'credited_at')
    list_filter = ('status', 'credited_at')
    search_fields = ('transferee__first_name', 'transferee__last_name', 'source_subject_code', 'source_subject_name')
    ordering = ('-credited_at',)
    readonly_fields = ('credited_at',)

    fieldsets = (
        ('Transferee', {
            'fields': ('transferee',)
        }),
        ('Source School Subject', {
            'fields': ('source_subject_code', 'source_subject_name', 'grade')
        }),
        ('Richwell Subject Mapping', {
            'fields': ('subject', 'status')
        }),
        ('Rejection', {
            'fields': ('rejection_reason',)
        }),
        ('Audit', {
            'fields': ('credited_by', 'credited_at')
        }),
    )

    def get_transferee_name(self, obj):
        return f"{obj.transferee.first_name} {obj.transferee.last_name}"
    get_transferee_name.short_description = 'Transferee'

    def has_delete_permission(self, request):
        # Only admins can delete credit records
        return request.user.is_superuser
