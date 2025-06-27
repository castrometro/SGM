from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0024_remove_clasificacioncuentaarchivo_contabilida_upload__5b9df0_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='libromayorupload',
            name='upload_log',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                blank=True,
                null=True,
                help_text='Referencia al log del upload que generó este archivo',
                to='contabilidad.uploadlog',
            ),
        ),
    ]
