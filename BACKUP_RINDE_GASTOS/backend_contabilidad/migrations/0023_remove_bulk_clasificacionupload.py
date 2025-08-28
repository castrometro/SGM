import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0005_cliente_bilingue"),
        ("contabilidad", "0022_uploadlog_ruta_archivo"),
    ]

    operations = [
        migrations.CreateModel(
            name="ClasificacionArchivo",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("archivo", models.FileField(upload_to="clasificacion/")),
                ("fecha_subida", models.DateTimeField(auto_now_add=True)),
                (
                    "cliente",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, to="api.cliente"
                    ),
                ),
                (
                    "upload_log",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        help_text="Referencia al log del upload que generó este archivo",
                        to="contabilidad.uploadlog",
                    ),
                ),
            ],
        ),
        migrations.RenameField(
            model_name="clasificacioncuentaarchivo",
            old_name="upload",
            new_name="upload_log",
        ),
        migrations.AlterField(
            model_name="clasificacioncuentaarchivo",
            name="upload_log",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="clasificaciones_archivo",
                to="contabilidad.uploadlog",
            ),
        ),
        migrations.DeleteModel(name="BulkClasificacionUpload"),
    ]
