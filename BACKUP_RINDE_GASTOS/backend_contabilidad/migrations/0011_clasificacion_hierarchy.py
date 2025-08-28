from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('contabilidad', '0010_rename_cierremensual_cierrecontabilidad'),
    ]

    operations = [
        migrations.AddField(
            model_name='clasificacionset',
            name='idioma',
            field=models.CharField(choices=[('es', 'Español'), ('en', 'English')], default='es', max_length=2),
        ),
        migrations.AddField(
            model_name='clasificacionoption',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sub_opciones', to='contabilidad.clasificacionoption'),
        ),
    ]
