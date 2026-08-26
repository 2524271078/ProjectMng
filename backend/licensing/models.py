from django.db import models


class LicenseState(models.Model):
    """A singleton record containing the currently activated signed license."""

    license_payload = models.JSONField(default=dict, blank=True)
    signature = models.TextField(blank=True, default="")
    activated_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    last_validation_error = models.CharField(max_length=128, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_solo(cls):
        state, _ = cls.objects.get_or_create(pk=1)
        return state
