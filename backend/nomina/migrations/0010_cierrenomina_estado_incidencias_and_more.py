# Generated by Django 5.2.1 on 2025-06-12 06:03

import django.db.models.deletion
import nomina.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nomina', '0009_rename_vigente_conceptoremuneracionnovedades_activo_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='cierrenomina',
            name='estado_incidencias',
            field=models.CharField(choices=[('analisis_pendiente', 'Análisis de Incidencias Pendiente'), ('incidencias_generadas', 'Incidencias Detectadas'), ('resolucion_analista', 'En Resolución por Analista'), ('revision_supervisor', 'En Revisión por Supervisor'), ('devuelto_analista', 'Devuelto al Analista'), ('aprobado', 'Incidencias Aprobadas'), ('cierre_completado', 'Cierre Completado')], default='analisis_pendiente', max_length=50),
        ),
        migrations.AddField(
            model_name='cierrenomina',
            name='fecha_ultima_revision',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='cierrenomina',
            name='revisiones_realizadas',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='cierrenomina',
            name='supervisor_asignado',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cierres_supervisor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='IncidenciaCierre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_incidencia', models.CharField(choices=[('empleado_solo_libro', 'Empleado solo en Libro'), ('empleado_solo_novedades', 'Empleado solo en Novedades'), ('diff_datos_personales', 'Diferencia en Datos Personales'), ('diff_sueldo_base', 'Diferencia en Sueldo Base'), ('diff_concepto_monto', 'Diferencia en Monto por Concepto'), ('concepto_solo_libro', 'Concepto solo en Libro'), ('concepto_solo_novedades', 'Concepto solo en Novedades'), ('ingreso_no_reportado', 'Ingreso no reportado por Analista'), ('finiquito_no_reportado', 'Finiquito no reportado por Analista'), ('ausencia_no_reportada', 'Ausencia no reportada por Analista'), ('diff_fechas_ausencia', 'Diferencia en Fechas de Ausencia'), ('diff_dias_ausencia', 'Diferencia en Días de Ausencia'), ('diff_tipo_ausencia', 'Diferencia en Tipo de Ausencia')], max_length=50)),
                ('rut_empleado', models.CharField(max_length=20)),
                ('descripcion', models.TextField()),
                ('valor_libro', models.CharField(blank=True, max_length=500, null=True)),
                ('valor_novedades', models.CharField(blank=True, max_length=500, null=True)),
                ('valor_movimientos', models.CharField(blank=True, max_length=500, null=True)),
                ('valor_analista', models.CharField(blank=True, max_length=500, null=True)),
                ('concepto_afectado', models.CharField(blank=True, max_length=200, null=True)),
                ('fecha_detectada', models.DateTimeField(auto_now_add=True)),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente de Resolución'), ('resuelta_analista', 'Resuelta por Analista'), ('aprobada_supervisor', 'Aprobada por Supervisor'), ('rechazada_supervisor', 'Rechazada por Supervisor'), ('re_resuelta', 'Re-resuelta por Analista')], default='pendiente', max_length=20)),
                ('prioridad', models.CharField(choices=[('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta'), ('critica', 'Crítica')], default='media', max_length=10)),
                ('impacto_monetario', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('fecha_primera_resolucion', models.DateTimeField(blank=True, null=True)),
                ('fecha_ultima_accion', models.DateTimeField(auto_now=True)),
                ('asignado_a', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='incidencias_asignadas', to=settings.AUTH_USER_MODEL)),
                ('cierre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='incidencias', to='nomina.cierrenomina')),
                ('empleado_libro', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='nomina.empleadocierre')),
                ('empleado_novedades', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='nomina.empleadocierrenovedades')),
            ],
        ),
        migrations.CreateModel(
            name='ResolucionIncidencia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_resolucion', models.CharField(choices=[('justificacion', 'Justificación'), ('correccion', 'Corrección'), ('aprobacion', 'Aprobación'), ('rechazo', 'Rechazo'), ('consulta', 'Consulta'), ('solicitud_cambio', 'Solicitud de Cambio')], max_length=20)),
                ('comentario', models.TextField()),
                ('adjunto', models.FileField(blank=True, null=True, upload_to=nomina.models.resolucion_upload_to)),
                ('fecha_resolucion', models.DateTimeField(auto_now_add=True)),
                ('estado_anterior', models.CharField(max_length=20)),
                ('estado_nuevo', models.CharField(max_length=20)),
                ('valor_corregido', models.CharField(blank=True, max_length=500, null=True)),
                ('campo_corregido', models.CharField(blank=True, max_length=100, null=True)),
                ('incidencia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resoluciones', to='nomina.incidenciacierre')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('usuarios_mencionados', models.ManyToManyField(blank=True, related_name='resoluciones_mencionado', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-fecha_resolucion'],
            },
        ),
        migrations.AddIndex(
            model_name='incidenciacierre',
            index=models.Index(fields=['cierre', 'tipo_incidencia'], name='nomina_inci_cierre__d2088d_idx'),
        ),
        migrations.AddIndex(
            model_name='incidenciacierre',
            index=models.Index(fields=['cierre', 'estado'], name='nomina_inci_cierre__93d1fa_idx'),
        ),
        migrations.AddIndex(
            model_name='incidenciacierre',
            index=models.Index(fields=['rut_empleado', 'cierre'], name='nomina_inci_rut_emp_d5e509_idx'),
        ),
        migrations.AddIndex(
            model_name='incidenciacierre',
            index=models.Index(fields=['estado', 'prioridad'], name='nomina_inci_estado_d5a625_idx'),
        ),
        migrations.AddIndex(
            model_name='incidenciacierre',
            index=models.Index(fields=['asignado_a', 'estado'], name='nomina_inci_asignad_8518e6_idx'),
        ),
    ]
