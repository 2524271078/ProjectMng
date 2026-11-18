import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("projects", "0018_deviceserviceschedule_assignee"),
    ]

    operations = [
        migrations.CreateModel(
            name="ServiceExpiryEmailRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("remark", models.TextField(blank=True, default="")),
                ("status", models.CharField(choices=[("pending", "待发送"), ("sending", "发送中"), ("sent", "已发送"), ("failed", "发送失败")], db_index=True, default="pending", max_length=16)),
                ("extra", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("service_end_date", models.DateField(db_index=True)),
                ("recipient_name", models.CharField(blank=True, default="", max_length=100)),
                ("recipient_email", models.EmailField(blank=True, default="", max_length=254)),
                ("message_subject", models.CharField(blank=True, default="", max_length=255)),
                ("sent_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("last_error", models.TextField(blank=True, default="")),
                ("attempt_count", models.PositiveIntegerField(default=0)),
                ("trigger_source", models.CharField(choices=[("manual", "单条发送"), ("batch", "一键发送"), ("scheduled", "自动发送")], default="manual", max_length=16)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_created", to=settings.AUTH_USER_MODEL)),
                ("project_device", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="expiry_email_records", to="projects.projectdevice")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_updated", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="serviceexpiryemailrecord",
            constraint=models.UniqueConstraint(fields=("project_device", "service_end_date"), name="uniq_project_device_service_expiry_email"),
        ),
        migrations.AddIndex(
            model_name="serviceexpiryemailrecord",
            index=models.Index(fields=["status", "service_end_date"], name="projects_se_status_4a7b31_idx"),
        ),
    ]
