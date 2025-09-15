from django.core.management.base import BaseCommand
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from nomina.models import RegistroConceptoEmpleadoNovedades


def normalizar_valor(valor_raw):
    if valor_raw is None:
        return None
    try:
        d = Decimal(str(valor_raw))
        d0 = d.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        return str(int(d0))
    except (InvalidOperation, ValueError, TypeError):
        return None


class Command(BaseCommand):
    help = "Normaliza montos de novedades a pesos (entero, HALF_UP)."

    def add_arguments(self, parser):
        parser.add_argument('--cierre-id', type=int, help='ID de cierre para limitar la normalización')
        parser.add_argument('--dry-run', action='store_true', help='Solo mostrar conteo sin escribir cambios')

    def handle(self, *args, **options):
        cierre_id = options.get('cierre_id')
        dry_run = options.get('dry_run', False)

        qs = RegistroConceptoEmpleadoNovedades.objects.all()
        if cierre_id:
            qs = qs.filter(empleado__cierre_id=cierre_id)

        total = qs.count()
        actualizados = 0

        for reg in qs.iterator(chunk_size=1000):
            nuevo = normalizar_valor(reg.monto)
            if nuevo is not None and nuevo != reg.monto:
                actualizados += 1
                if not dry_run:
                    reg.monto = nuevo
                    reg.save(update_fields=['monto'])

        self.stdout.write(self.style.SUCCESS(
            f"Normalización completada. Registros evaluados: {total}, actualizados: {actualizados}. Dry-run: {dry_run}"
        ))
