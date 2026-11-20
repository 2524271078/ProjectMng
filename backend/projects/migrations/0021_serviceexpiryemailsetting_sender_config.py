from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0020_serviceexpiryemailsetting"),
    ]

    operations = [
        migrations.AddField(
            model_name="serviceexpiryemailsetting",
            name="email_host_user",
            field=models.CharField(blank=True, default="", max_length=254),
        ),
        migrations.AddField(
            model_name="serviceexpiryemailsetting",
            name="email_host_password",
            field=models.CharField(blank=True, default="", max_length=512),
        ),
        migrations.AddField(
            model_name="serviceexpiryemailsetting",
            name="default_from_email",
            field=models.CharField(blank=True, default="", max_length=254),
        ),
    ]
