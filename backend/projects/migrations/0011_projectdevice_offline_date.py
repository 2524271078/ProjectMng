from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0010_optional_catalog_codes'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectdevice',
            name='offline_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='projectdevice',
            name='service_type',
            field=models.CharField(
                choices=[
                    ('new_install', '新上设备'),
                    ('renewal', '续保旧设备'),
                    ('offline', '下架'),
                ],
                db_index=True,
                default='new_install',
                max_length=32,
            ),
        ),
    ]
