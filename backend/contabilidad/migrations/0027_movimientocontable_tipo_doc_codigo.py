from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0026_movimientocontable_flag_incompleto'),
    ]

    operations = [
        migrations.AddField(
            model_name='movimientocontable',
            name='tipo_doc_codigo',
            field=models.CharField(max_length=10, blank=True, default=''),
        ),
    ]
