from django.db import migrations


class Migration(migrations.Migration):
    """Merge de ramas de migraciones 0242 para resolver conflicto de leaf nodes.

    Unifica:
      - 0242_movimientopersonal_drop_legacy
      - 0242_remove_nominaconsolidada_nomina_nomi_liquido_7d4a82_idx_and_more
    No aplica operaciones adicionales.
    """
    dependencies = [
        ('nomina', '0242_movimientopersonal_drop_legacy'),
        ('nomina', '0242_remove_nominaconsolidada_nomina_nomi_liquido_7d4a82_idx_and_more'),
    ]

    operations = []
