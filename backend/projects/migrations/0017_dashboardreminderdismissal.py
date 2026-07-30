from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("projects", "0016_backfill_service_item_schedules"),
    ]

    operations = [
        migrations.CreateModel(
            name="DashboardReminderDismissal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reminder_key", models.CharField(max_length=160)),
                ("dismissed_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="dashboard_reminder_dismissals", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name="dashboardreminderdismissal",
            constraint=models.UniqueConstraint(fields=("user", "reminder_key"), name="uniq_user_dashboard_reminder_dismissal"),
        ),
        migrations.AddIndex(
            model_name="dashboardreminderdismissal",
            index=models.Index(fields=["user", "reminder_key"], name="projects_da_user_id_6620ee_idx"),
        ),
    ]
