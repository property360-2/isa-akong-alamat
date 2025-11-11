from django.contrib import admin
from .models import AuditTrail, Archive


@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ('actor', 'action', 'entity', 'entity_id', 'created_at')
    list_filter = ('action', 'entity', 'created_at')
    search_fields = ('actor__username', 'entity', 'action')
    ordering = ('-created_at',)
    readonly_fields = ('actor', 'action', 'entity', 'entity_id', 'old_value_json', 'new_value_json', 'created_at')


@admin.register(Archive)
class ArchiveAdmin(admin.ModelAdmin):
    list_display = ('entity', 'entity_id', 'reason', 'archived_by', 'archived_at')
    list_filter = ('entity', 'archived_at')
    search_fields = ('entity', 'reason', 'archived_by__username')
    ordering = ('-archived_at',)
    readonly_fields = ('entity', 'entity_id', 'data_snapshot', 'reason', 'archived_by', 'archived_at')
