# Generated by Django 5.2.1 on 2025-06-18 18:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_cliente_bilingue'),
        ('contabilidad', '0023_remove_bulk_clasificacionupload'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='clasificacioncuentaarchivo',
            name='contabilida_upload__5b9df0_idx',
        ),
        migrations.AlterField(
            model_name='clasificacionarchivo',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='uploadlog',
            name='estado',
            field=models.CharField(choices=[('subido', 'Archivo subido'), ('procesando', 'Procesando'), ('completado', 'Procesado correctamente'), ('error', 'Con errores'), ('datos_eliminados', 'Datos procesados eliminados')], default='subido', max_length=20),
        ),
        migrations.AddIndex(
            model_name='clasificacioncuentaarchivo',
            index=models.Index(fields=['upload_log', 'procesado'], name='contabilida_upload__c57733_idx'),
        ),
    ]
