from django.core.management.base import BaseCommand
from django.db import transaction
from nomina.models import ConceptoConsolidado, HeaderValorEmpleado, ConceptoRemuneracion, CierreNomina

CLASIF_TO_TIPO = {
    'haberes_imponibles': 'haber_imponible',
    'haberes_no_imponibles': 'haber_no_imponible',
    'descuentos_legales': 'descuento_legal',
    'otros_descuentos': 'otro_descuento',
    'aportes_patronales': 'aporte_patronal',
    'impuestos': 'impuesto',
}

class Command(BaseCommand):
    help = "Reclasifica ConceptoConsolidado.tipo_concepto según ConceptoRemuneracion.clasificacion (corrige 'impuestos' y 'aportes_patronales' que quedaron como 'informativo')."

    def add_arguments(self, parser):
        parser.add_argument('--cierre-id', type=int, help='ID del cierre a procesar (opcional).')
        parser.add_argument('--cliente-id', type=int, help='Filtrar por cliente (opcional).')
        parser.add_argument('--periodo', type=str, help='Filtrar por periodo (YYYY-MM) (opcional).')
        parser.add_argument('--dry-run', action='store_true', help='No guarda cambios, sólo muestra conteos.')

    def handle(self, *args, **options):
        cierre_id = options.get('cierre_id')
        cliente_id = options.get('cliente_id')
        periodo = options.get('periodo')
        dry_run = options.get('dry_run')

        qs = ConceptoConsolidado.objects.select_related('nomina_consolidada__cierre')
        if cierre_id:
            qs = qs.filter(nomina_consolidada__cierre_id=cierre_id)
        elif cliente_id and periodo:
            qs = qs.filter(nomina_consolidada__cierre__cliente_id=cliente_id, nomina_consolidada__cierre__periodo=periodo)
        elif cliente_id:
            qs = qs.filter(nomina_consolidada__cierre__cliente_id=cliente_id)
        elif periodo:
            qs = qs.filter(nomina_consolidada__cierre__periodo=periodo)

        total = qs.count()
        self.stdout.write(self.style.NOTICE(f"Analizando {total} conceptos consolidados..."))

        cambios = 0
        por_motivo = {k: 0 for k in ['impuestos','aportes_patronales','otros']}

        # Para performance, trabajar en transacción si no es dry-run
        ctx = transaction.atomic() if not dry_run else nullcontext()
        with ctx:
            for cc in qs.iterator(chunk_size=1000):
                # Resolver clasificacion esperada
                clasificacion = None

                # 1) Intentar con codigo_concepto (id de ConceptoRemuneracion en str)
                concepto_ref = None
                if cc.codigo_concepto and str(cc.codigo_concepto).isdigit():
                    try:
                        concepto_ref = ConceptoRemuneracion.objects.get(id=int(cc.codigo_concepto))
                        clasificacion = concepto_ref.clasificacion
                    except ConceptoRemuneracion.DoesNotExist:
                        concepto_ref = None

                # 2) Fallback por HeaderValorEmpleado mapeado con mismo nombre_header y nomina
                if not clasificacion:
                    hv = HeaderValorEmpleado.objects.filter(
                        nomina_consolidada=cc.nomina_consolidada,
                        nombre_header=cc.nombre_concepto,
                        concepto_remuneracion__isnull=False
                    ).select_related('concepto_remuneracion').first()
                    if hv and hv.concepto_remuneracion:
                        concepto_ref = hv.concepto_remuneracion
                        clasificacion = concepto_ref.clasificacion

                if not clasificacion:
                    continue  # No hay referencia clara; omitir

                tipo_esperado = CLASIF_TO_TIPO.get(clasificacion)
                if not tipo_esperado:
                    continue

                if cc.tipo_concepto != tipo_esperado:
                    # Contabilizar motivo
                    if clasificacion == 'impuestos':
                        por_motivo['impuestos'] += 1
                    elif clasificacion == 'aportes_patronales':
                        por_motivo['aportes_patronales'] += 1
                    else:
                        por_motivo['otros'] += 1

                    if not dry_run:
                        cc.tipo_concepto = tipo_esperado
                        cc.save(update_fields=['tipo_concepto'])
                    cambios += 1

        self.stdout.write(self.style.SUCCESS(
            f"Listo. Cambios{' (simulados)' if dry_run else ''}: {cambios}. "
            f"Impuestos: {por_motivo['impuestos']}, Aportes: {por_motivo['aportes_patronales']}, Otros: {por_motivo['otros']}"
        ))

# Utilidad para usar contexto vacío en dry-run
from contextlib import contextmanager
@contextmanager
def nullcontext():
    yield
