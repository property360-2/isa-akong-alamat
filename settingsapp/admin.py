from django.contrib import admin
from .models import Setting


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ('key_name', 'value_text', 'description', 'updated_by', 'updated_at')
    search_fields = ('key_name', 'description')
    ordering = ('key_name',)
