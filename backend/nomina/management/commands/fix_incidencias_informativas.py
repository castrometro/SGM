from django.core.management.base import BaseCommand
from nomina.models import IncidenciaCierre

class Command(BaseCommand):
    help = "Marca incidencias informativas como resueltas por analista (evita flujo de aprobación)"

    def handle(self, *args, **options):
        tipos_informativos = ['ingreso_empleado', 'empleado_nuevo']
        qs = IncidenciaCierre.objects.filter(tipo_incidencia__in=tipos_informativos, estado='pendiente')
        total = qs.count()
        updated = qs.update(estado='resuelta_analista')
        self.stdout.write(self.style.SUCCESS(f"Actualizadas {updated}/{total} incidencias informativas a resuelta_analista"))
