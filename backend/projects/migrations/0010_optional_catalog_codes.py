from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0007_device_nonstandard_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='product_code',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='productversion',
            name='version_code',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='devicemodel',
            name='model_code',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddConstraint(
            model_name='product',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_deleted=False) & ~models.Q(product_code=''),
                fields=('product_code',),
                name='uniq_active_product_code',
            ),
        ),
        migrations.RemoveConstraint(
            model_name='productversion',
            name='uniq_active_product_version',
        ),
        migrations.AddConstraint(
            model_name='productversion',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_deleted=False) & ~models.Q(version_code=''),
                fields=('product', 'version_code'),
                name='uniq_active_product_version',
            ),
        ),
        migrations.AddConstraint(
            model_name='devicemodel',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_deleted=False) & ~models.Q(model_code=''),
                fields=('model_code',),
                name='uniq_active_model_code',
            ),
        ),
    ]
