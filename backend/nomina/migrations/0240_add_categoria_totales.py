# Generated migration: agregar campos de totales por categoria y eliminar totales viejos
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('nomina', '0005_add_historial_verificacion_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='nominaconsolidada',
            name='haberes_imponibles',
            field=models.DecimalField(default=0, max_digits=15, decimal_places=2),
        ),
        migrations.AddField(
            model_name='nominaconsolidada',
            name='haberes_no_imponibles',
            field=models.DecimalField(default=0, max_digits=15, decimal_places=2),
        ),
        migrations.AddField(
            model_name='nominaconsolidada',
            name='dctos_legales',
            field=models.DecimalField(default=0, max_digits=15, decimal_places=2),
        ),
        migrations.AddField(
            model_name='nominaconsolidada',
            name='otros_dctos',
            field=models.DecimalField(default=0, max_digits=15, decimal_places=2),
        ),
        migrations.AddField(
            model_name='nominaconsolidada',
            name='impuestos',
            field=models.DecimalField(default=0, max_digits=15, decimal_places=2),
        ),
        migrations.AddField(
            model_name='nominaconsolidada',
            name='horas_extras_cantidad',
            field=models.DecimalField(default=0, max_digits=10, decimal_places=4),
        ),
        migrations.AddField(
            model_name='nominaconsolidada',
            name='aportes_patronales',
            field=models.DecimalField(default=0, max_digits=15, decimal_places=2),
        ),
        migrations.RemoveField(
            model_name='nominaconsolidada',
            name='total_haberes',
        ),
        migrations.RemoveField(
            model_name='nominaconsolidada',
            name='total_descuentos',
        ),
        migrations.RemoveField(
            model_name='nominaconsolidada',
            name='liquido_pagar',
        ),
    ]
