from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('nomina', '0240_add_categoria_totales'),
    ]

    operations = [
        migrations.AddField(
            model_name='movimientopersonal',
            name='descripcion',
            field=models.CharField(max_length=300, null=True, blank=True, help_text='Descripción textual directa del origen'),
        ),
        migrations.AddField(
            model_name='movimientopersonal',
            name='categoria',
            field=models.CharField(max_length=20, null=True, blank=True, help_text='Clasificación general: ingreso | finiquito | ausencia | reincorporacion | cambio_datos'),
        ),
        migrations.AddField(
            model_name='movimientopersonal',
            name='subtipo',
            field=models.CharField(max_length=40, null=True, blank=True, help_text='Subtipo de la ausencia o detalle del evento (vacaciones, licencia_medica, sin_justificar, etc.)'),
        ),
        migrations.AddField(
            model_name='movimientopersonal',
            name='fecha_inicio',
            field=models.DateField(null=True, blank=True, help_text='Inicio real del evento (ausencia, vacaciones, etc.)'),
        ),
        migrations.AddField(
            model_name='movimientopersonal',
            name='fecha_fin',
            field=models.DateField(null=True, blank=True, help_text='Fin real del evento'),
        ),
        migrations.AddField(
            model_name='movimientopersonal',
            name='dias_evento',
            field=models.IntegerField(null=True, blank=True, help_text='Duración total del evento (fin - inicio + 1)'),
        ),
        migrations.AddField(
            model_name='movimientopersonal',
            name='dias_en_periodo',
            field=models.IntegerField(null=True, blank=True, help_text='Días del evento imputables al periodo del cierre'),
        ),
        migrations.AddField(
            model_name='movimientopersonal',
            name='multi_mes',
            field=models.BooleanField(default=False, help_text='El evento cruza límites de mes'),
        ),
        migrations.AddField(
            model_name='movimientopersonal',
            name='hash_evento',
            field=models.CharField(max_length=64, null=True, blank=True, db_index=True, help_text='Hash global del evento (rango completo)'),
        ),
        migrations.AddField(
            model_name='movimientopersonal',
            name='hash_registro_periodo',
            field=models.CharField(max_length=80, null=True, blank=True, db_index=True, help_text='Hash del evento ligado al periodo (hash_evento + periodo)'),
        ),
        migrations.AddField(
            model_name='movimientopersonal',
            name='detalle_fuente',
            field=models.JSONField(null=True, blank=True, help_text='Snapshot opcional de campos origen para auditoría'),
        ),
        migrations.AddIndex(
            model_name='movimientopersonal',
            index=models.Index(fields=['categoria', 'subtipo'], name='nomina_movi_categoria_subtipo_idx'),
        ),
        migrations.AddIndex(
            model_name='movimientopersonal',
            index=models.Index(fields=['fecha_inicio'], name='nomina_movi_fecha_inicio_idx'),
        ),
        migrations.AddIndex(
            model_name='movimientopersonal',
            index=models.Index(fields=['hash_evento'], name='nomina_movi_hash_evento_idx'),
        ),
    ]
