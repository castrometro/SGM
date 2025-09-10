from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('nomina', '0241_movimiento_personal_normalizacion'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='movimientopersonal',
            name='tipo_movimiento',
        ),
        migrations.RemoveField(
            model_name='movimientopersonal',
            name='motivo',
        ),
        migrations.RemoveField(
            model_name='movimientopersonal',
            name='dias_ausencia',
        ),
        migrations.RemoveField(
            model_name='movimientopersonal',
            name='fecha_movimiento',
        ),
        # Indexes referencing removed fields are implicitly dropped; ensure new ones created by previous migration/state.
    ]