# Generated by Django 5.2.1 on 2025-05-20 16:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0007_analisiscuentacierre'),
    ]

    operations = [
        migrations.AddField(
            model_name='cuentacontable',
            name='nombre_en',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
