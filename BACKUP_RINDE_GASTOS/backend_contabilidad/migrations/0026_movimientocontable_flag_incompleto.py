from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0025_libromayorupload_uploadlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='movimientocontable',
            name='flag_incompleto',
            field=models.BooleanField(default=False),
        ),
    ]
