import hashlib
from datetime import date
import calendar
from django.core.management.base import BaseCommand
from django.db import transaction
from nomina.models import MovimientoPersonal

class Command(BaseCommand):
    help = "Backfill de campos normalizados en MovimientoPersonal (categoria, subtipo, fechas, dias, hashes)."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='No guarda cambios, solo muestra conteos')
        parser.add_argument('--batch', type=int, default=500, help='Tamaño de lote para bulk_update')

    def handle(self, *args, **options):
        dry = options['dry_run']
        batch_size = options['batch']

        qs = MovimientoPersonal.objects.all().order_by('id')
        total = qs.count()
        procesados = 0
        updates = []

        self.stdout.write(self.style.WARNING(f"Iniciando backfill MovimientoPersonal ({total} registros) dry_run={dry}"))

        for mv in qs.iterator():
            # Derivar categoria si falta
            if not mv.categoria:
                if mv.tipo_movimiento == 'ingreso':
                    mv.categoria = 'ingreso'
                elif mv.tipo_movimiento == 'finiquito':
                    mv.categoria = 'finiquito'
                elif mv.tipo_movimiento == 'ausentismo':
                    mv.categoria = 'ausencia'
                elif mv.tipo_movimiento == 'reincorporacion':
                    mv.categoria = 'reincorporacion'
                else:
                    mv.categoria = 'cambio_datos'

            # Subtipo (solo para ausencias)
            if mv.categoria == 'ausencia' and not mv.subtipo:
                raw = (mv.motivo or mv.descripcion or '').strip().lower()
                if raw == 'vacaciones':
                    mv.subtipo = 'vacaciones'
                elif not raw:
                    mv.subtipo = 'sin_justificar'
                else:
                    # Si tiene formato "tipo - detalle"
                    if ' - ' in raw:
                        base = raw.split(' - ', 1)[0].strip()
                    else:
                        base = raw
                    # Normalización básica
                    base = base.replace(' ', '_')[:40]
                    mv.subtipo = base if base else 'sin_justificar'

            # Descripcion si vacía
            if not mv.descripcion:
                mv.descripcion = mv.motivo

            # Fechas: para ausencias tomar fecha_movimiento como inicio si no hay
            if mv.categoria == 'ausencia':
                if not mv.fecha_inicio:
                    mv.fecha_inicio = mv.fecha_movimiento
                if not mv.fecha_fin:
                    # Si tenemos observaciones con patrón 'hasta:' podría parsearse; fallback igual a inicio
                    mv.fecha_fin = mv.fecha_inicio
            else:
                # Eventos instantáneos
                if not mv.fecha_inicio:
                    mv.fecha_inicio = mv.fecha_movimiento
                if not mv.fecha_fin:
                    mv.fecha_fin = mv.fecha_inicio

            # dias_evento
            if mv.fecha_inicio and mv.fecha_fin:
                try:
                    mv.dias_evento = (mv.fecha_fin - mv.fecha_inicio).days + 1
                except Exception:
                    mv.dias_evento = mv.dias_ausencia or 1
            else:
                mv.dias_evento = mv.dias_ausencia or 1

            # Derivar periodo desde cierre (periodo YYYY-MM en nomina_consolidada.cierre.periodo)
            cierre = getattr(mv.nomina_consolidada, 'cierre', None)
            dias_clipped = None
            multi_mes = False
            if cierre and mv.fecha_inicio and mv.fecha_fin:
                try:
                    year, month = map(int, cierre.periodo.split('-'))
                    start_periodo = date(year, month, 1)
                    last_day = calendar.monthrange(year, month)[1]
                    end_periodo = date(year, month, last_day)
                    clip_start = mv.fecha_inicio if mv.fecha_inicio > start_periodo else start_periodo
                    clip_end = mv.fecha_fin if mv.fecha_fin < end_periodo else end_periodo
                    if clip_end >= clip_start:
                        dias_clipped = (clip_end - clip_start).days + 1
                    else:
                        dias_clipped = 0
                    multi_mes = (mv.fecha_inicio < start_periodo) or (mv.fecha_fin > end_periodo)
                except Exception:
                    dias_clipped = mv.dias_evento
            if dias_clipped is not None:
                mv.dias_en_periodo = dias_clipped
            mv.multi_mes = multi_mes

            # Hashes
            if mv.fecha_inicio and mv.fecha_fin:
                base_hash = f"{mv.nomina_consolidada.rut_empleado}:{mv.categoria}:{mv.subtipo}:{mv.fecha_inicio}:{mv.fecha_fin}".lower()
                mv.hash_evento = hashlib.sha1(base_hash.encode('utf-8')).hexdigest()
                if cierre:
                    mv.hash_registro_periodo = hashlib.sha1(f"{mv.hash_evento}:{cierre.periodo}".encode('utf-8')).hexdigest()

            updates.append(mv)
            procesados += 1
            if len(updates) >= batch_size:
                if not dry:
                    with transaction.atomic():
                        MovimientoPersonal.objects.bulk_update(updates, [
                            'categoria','subtipo','descripcion','fecha_inicio','fecha_fin','dias_evento','dias_en_periodo','multi_mes','hash_evento','hash_registro_periodo'
                        ])
                updates.clear()
                self.stdout.write(f"Procesados {procesados}/{total}")

        if updates and not dry:
            with transaction.atomic():
                MovimientoPersonal.objects.bulk_update(updates, [
                    'categoria','subtipo','descripcion','fecha_inicio','fecha_fin','dias_evento','dias_en_periodo','multi_mes','hash_evento','hash_registro_periodo'
                ])

        self.stdout.write(self.style.SUCCESS("Backfill finalizado"))
