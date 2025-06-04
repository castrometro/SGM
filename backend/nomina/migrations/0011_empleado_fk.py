from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('nomina', '0010_empleado'),
    ]

    operations = [
        migrations.AddField(
            model_name='movimientoaltabaja',
            name='empleado',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='nomina.empleado'),
        ),
        migrations.AddField(
            model_name='movimientoausentismo',
            name='empleado',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='nomina.empleado'),
        ),
        migrations.AddField(
            model_name='movimientovacaciones',
            name='empleado',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='nomina.empleado'),
        ),
        migrations.AddField(
            model_name='variacionsueldobase',
            name='empleado',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='nomina.empleado'),
        ),
        migrations.AddField(
            model_name='variaciontipocontrato',
            name='empleado',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='nomina.empleado'),
        ),
        migrations.AddField(
            model_name='registroingresoanalista',
            name='empleado',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='nomina.empleado'),
        ),
        migrations.AddField(
            model_name='registrofiniquitoanalista',
            name='empleado',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='nomina.empleado'),
        ),
        migrations.AddField(
            model_name='registroausentismoanalista',
            name='empleado',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='nomina.empleado'),
        ),
        migrations.AddField(
            model_name='incidenciacomparacion',
            name='empleado',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='nomina.empleado'),
        ),
        migrations.AddField(
            model_name='novedad',
            name='empleado',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='nomina.empleado'),
        ),
        migrations.AddField(
            model_name='incidencianovedad',
            name='empleado',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='nomina.empleado'),
        ),
    ]
