# Generated migration for adding new estado choices

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nomina', '0016_alter_cierrenomina_estado_incidencias'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cierrenomina',
            name='estado',
            field=models.CharField(
                choices=[
                    ('pendiente', 'Pendiente'),
                    ('en_proceso', 'En Proceso'),
                    ('datos_consolidados', 'Datos Consolidados'),
                    ('reportes_generados', 'Reportes Generados'),
                    ('validacion_senior', 'Validación Senior'),
                    ('completado', 'Completado'),
                    ('analisis_generado', 'Análisis Generado'),
                    ('incidencias_abiertas', 'Incidencias Abiertas'),
                    ('sin_incidencias', 'Sin Incidencias'),
                ],
                default='pendiente',
                max_length=30
            ),
        ),
    ]
