from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0009_projectdevice_service_end_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='nonstandard_name',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
    ]