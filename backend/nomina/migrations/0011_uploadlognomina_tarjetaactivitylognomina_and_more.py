# Generated by Django 5.2.1 on 2025-07-06 07:43

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_add_supervisor_relation'),
        ('nomina', '0010_cierrenomina_estado_incidencias_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UploadLogNomina',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_upload', models.CharField(choices=[('libro_remuneraciones', 'Libro de Remuneraciones'), ('movimientos_mes', 'Movimientos del Mes'), ('novedades', 'Novedades'), ('movimientos_ingresos', 'Movimientos - Ingresos'), ('movimientos_finiquitos', 'Movimientos - Finiquitos'), ('movimientos_incidencias', 'Movimientos - Incidencias'), ('archivos_analista', 'Archivos del Analista')], max_length=30)),
                ('fecha_subida', models.DateTimeField(auto_now_add=True)),
                ('nombre_archivo_original', models.CharField(max_length=255)),
                ('ruta_archivo', models.CharField(blank=True, help_text='Ruta relativa del archivo en storage', max_length=500)),
                ('tamaño_archivo', models.BigIntegerField(help_text='Tamaño en bytes')),
                ('hash_archivo', models.CharField(blank=True, help_text='SHA-256 del archivo', max_length=64)),
                ('estado', models.CharField(choices=[('subido', 'Archivo subido'), ('procesando', 'Procesando'), ('analizando_hdrs', 'Analizando Headers'), ('hdrs_analizados', 'Headers Analizados'), ('clasif_en_proceso', 'Clasificación en Proceso'), ('clasif_pendiente', 'Clasificación Pendiente'), ('clasificado', 'Clasificado'), ('completado', 'Procesado correctamente'), ('procesado', 'Procesado'), ('error', 'Con errores'), ('con_errores_parciales', 'Con Errores Parciales'), ('datos_eliminados', 'Datos procesados eliminados')], default='subido', max_length=30)),
                ('errores', models.TextField(blank=True)),
                ('resumen', models.JSONField(blank=True, null=True)),
                ('tiempo_procesamiento', models.DurationField(blank=True, null=True)),
                ('ip_usuario', models.GenericIPAddressField(blank=True, null=True)),
                ('registros_procesados', models.PositiveIntegerField(default=0)),
                ('registros_exitosos', models.PositiveIntegerField(default=0)),
                ('registros_fallidos', models.PositiveIntegerField(default=0)),
                ('headers_detectados', models.JSONField(blank=True, default=list)),
                ('iteracion', models.PositiveIntegerField(default=1, help_text='Número de iteración de procesamiento para este cierre (1=inicial, 2+=reproceso)')),
                ('es_iteracion_principal', models.BooleanField(default=True, help_text='Marca si es la iteración principal visible al usuario')),
                ('cierre', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='nomina.cierrenomina')),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.cliente')),
                ('usuario', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Log de Upload Nómina',
                'verbose_name_plural': 'Logs de Uploads Nómina',
                'ordering': ['-fecha_subida'],
            },
        ),
        migrations.CreateModel(
            name='TarjetaActivityLogNomina',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tarjeta', models.CharField(choices=[('libro_remuneraciones', 'Tarjeta: Libro de Remuneraciones'), ('movimientos_mes', 'Tarjeta: Movimientos del Mes'), ('novedades', 'Tarjeta: Novedades'), ('archivos_analista', 'Tarjeta: Archivos del Analista'), ('incidencias', 'Tarjeta: Incidencias'), ('revision', 'Tarjeta: Revisión')], max_length=25)),
                ('accion', models.CharField(choices=[('upload_excel', 'Subida de Excel'), ('manual_create', 'Creación Manual'), ('manual_edit', 'Edición Manual'), ('manual_delete', 'Eliminación Manual'), ('bulk_delete', 'Eliminación Masiva'), ('view_data', 'Visualización de Datos'), ('view_list', 'Visualización de Lista'), ('validation_error', 'Error de Validación'), ('process_start', 'Inicio de Procesamiento'), ('process_complete', 'Procesamiento Completado'), ('header_analysis', 'Análisis de Headers'), ('classification_start', 'Inicio de Clasificación'), ('classification_complete', 'Clasificación Completada'), ('reprocesar', 'Reprocesamiento'), ('delete_all', 'Eliminación Total')], max_length=25)),
                ('descripcion', models.TextField()),
                ('detalles', models.JSONField(blank=True, null=True)),
                ('resultado', models.CharField(choices=[('exito', 'Exitoso'), ('error', 'Error'), ('warning', 'Advertencia')], default='exito', max_length=10)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('cierre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activity_logs_nomina', to='nomina.cierrenomina')),
                ('usuario', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('upload_log', models.ForeignKey(blank=True, help_text='Referencia al log del upload relacionado', null=True, on_delete=django.db.models.deletion.SET_NULL, to='nomina.uploadlognomina')),
            ],
            options={
                'verbose_name': 'Log de Actividad de Tarjeta Nómina',
                'verbose_name_plural': 'Logs de Actividad de Tarjetas Nómina',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddField(
            model_name='archivoanalistaupload',
            name='upload_log',
            field=models.ForeignKey(blank=True, help_text='Referencia al log del upload que generó este archivo', null=True, on_delete=django.db.models.deletion.SET_NULL, to='nomina.uploadlognomina'),
        ),
        migrations.AddField(
            model_name='archivonovedadesupload',
            name='upload_log',
            field=models.ForeignKey(blank=True, help_text='Referencia al log del upload que generó este archivo', null=True, on_delete=django.db.models.deletion.SET_NULL, to='nomina.uploadlognomina'),
        ),
        migrations.AddField(
            model_name='libroremuneracionesupload',
            name='upload_log',
            field=models.ForeignKey(blank=True, help_text='Referencia al log del upload que generó este archivo', null=True, on_delete=django.db.models.deletion.SET_NULL, to='nomina.uploadlognomina'),
        ),
        migrations.AddField(
            model_name='movimientosmesupload',
            name='upload_log',
            field=models.ForeignKey(blank=True, help_text='Referencia al log del upload que generó este archivo', null=True, on_delete=django.db.models.deletion.SET_NULL, to='nomina.uploadlognomina'),
        ),
        migrations.AddIndex(
            model_name='uploadlognomina',
            index=models.Index(fields=['cliente', 'tipo_upload'], name='nomina_uplo_cliente_80a255_idx'),
        ),
        migrations.AddIndex(
            model_name='uploadlognomina',
            index=models.Index(fields=['estado', 'fecha_subida'], name='nomina_uplo_estado_35590f_idx'),
        ),
        migrations.AddIndex(
            model_name='uploadlognomina',
            index=models.Index(fields=['tipo_upload', 'estado'], name='nomina_uplo_tipo_up_ac3588_idx'),
        ),
        migrations.AddIndex(
            model_name='uploadlognomina',
            index=models.Index(fields=['cierre', 'tipo_upload', 'iteracion'], name='nomina_uplo_cierre__fea5eb_idx'),
        ),
        migrations.AddIndex(
            model_name='uploadlognomina',
            index=models.Index(fields=['cierre', 'tipo_upload', 'es_iteracion_principal'], name='nomina_uplo_cierre__daec57_idx'),
        ),
        migrations.AddIndex(
            model_name='tarjetaactivitylognomina',
            index=models.Index(fields=['cierre', 'tarjeta'], name='nomina_tarj_cierre__dcbaec_idx'),
        ),
        migrations.AddIndex(
            model_name='tarjetaactivitylognomina',
            index=models.Index(fields=['usuario', 'timestamp'], name='nomina_tarj_usuario_36363d_idx'),
        ),
        migrations.AddIndex(
            model_name='tarjetaactivitylognomina',
            index=models.Index(fields=['tarjeta', 'accion'], name='nomina_tarj_tarjeta_befaec_idx'),
        ),
    ]
