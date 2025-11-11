# settingsapp/models.py
from django.db import models
from users.models import User

class Setting(models.Model):
    key_name = models.CharField(max_length=100, unique=True)
    value_text = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key_name} = {self.value_text}"
