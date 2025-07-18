# Generated manually for bypassing servicios logic

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='areas',
            field=models.ManyToManyField(
                to='api.Area',
                related_name='clientes_directos',
                blank=True,
                help_text='Áreas directas del cliente (bypass de servicios contratados)'
            ),
        ),
    ]
