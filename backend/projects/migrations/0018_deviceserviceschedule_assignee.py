from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0017_dashboardreminderdismissal"),
    ]

    operations = [
        migrations.AddField(
            model_name="deviceserviceschedule",
            name="assignee",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="device_service_schedules", to="projects.person"),
        ),
    ]
