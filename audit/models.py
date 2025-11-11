# audit/models.py
from django.db import models
from users.models import User

class AuditTrail(models.Model):
    actor = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    entity = models.CharField(max_length=100)
    entity_id = models.BigIntegerField(null=True, blank=True)
    old_value_json = models.JSONField(null=True, blank=True)
    new_value_json = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} on {self.entity} ({self.actor.username})"


class Archive(models.Model):
    entity = models.CharField(max_length=100)
    entity_id = models.BigIntegerField(null=True, blank=True)
    data_snapshot = models.JSONField()
    reason = models.CharField(max_length=255, null=True, blank=True)
    archived_by = models.ForeignKey(User, on_delete=models.CASCADE)
    archived_at = models.DateTimeField(auto_now_add=True)
