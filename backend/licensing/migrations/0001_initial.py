from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="LicenseState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("license_payload", models.JSONField(blank=True, default=dict)),
                ("signature", models.TextField(blank=True, default="")),
                ("activated_at", models.DateTimeField(blank=True, null=True)),
                ("last_seen_at", models.DateTimeField(blank=True, null=True)),
                ("last_validation_error", models.CharField(blank=True, default="", max_length=128)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
