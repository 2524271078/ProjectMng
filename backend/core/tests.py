from django.db import models
from django.test import TransactionTestCase

from core.models import ActiveManager, BaseModel


class DemoRecord(BaseModel):
    name = models.CharField(max_length=50)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        app_label = "core"


class BaseModelTests(TransactionTestCase):
    def test_base_model_provides_extensible_audit_fields(self):
        field_names = {field.name for field in BaseModel._meta.fields}

        self.assertIn("remark", field_names)
        self.assertIn("status", field_names)
        self.assertIn("extra", field_names)
        self.assertIn("created_at", field_names)
        self.assertIn("updated_at", field_names)
        self.assertIn("created_by", field_names)
        self.assertIn("updated_by", field_names)
        self.assertIn("is_deleted", field_names)

    def test_active_manager_excludes_soft_deleted_rows(self):
        DemoRecord.all_objects.create(name="active")
        DemoRecord.all_objects.create(name="deleted", is_deleted=True)

        self.assertEqual(list(DemoRecord.objects.values_list("name", flat=True)), ["active"])
        self.assertEqual(DemoRecord.all_objects.count(), 2)
