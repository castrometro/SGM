"""
Script para debuggear y actualizar manualmente el estado de un cierre.

Uso:
python manage.py shell
exec(open('debug_estado_cierre.py').read())
"""

# Importaciones necesarias
from contabilidad.models import CierreContabilidad
from contabilidad.models_incidencias import Incidencia

def debuggear_cierre(cierre_id):
    """
    Función para debuggear el estado de un cierre específico
    """
    try:
        cierre = CierreContabilidad.objects.get(id=cierre_id)
        
        print(f"=== DEBUG CIERRE {cierre_id} ===")
        print(f"Cliente: {cierre.cliente.nombre}")
        print(f"Período: {cierre.periodo}")
        print(f"Estado actual: {cierre.estado}")
        print(f"Fecha sin incidencias: {cierre.fecha_sin_incidencias}")
        print(f"Fecha finalización: {cierre.fecha_finalizacion}")
        
        # Contar incidencias
        total_incidencias = Incidencia.objects.filter(cierre=cierre).count()
        incidencias_pendientes = Incidencia.objects.filter(cierre=cierre, estado='pendiente').count()
        incidencias_resueltas = Incidencia.objects.filter(cierre=cierre, estado='resuelta').count()
        
        print(f"\n=== INCIDENCIAS ===")
        print(f"Total incidencias: {total_incidencias}")
        print(f"Incidencias pendientes: {incidencias_pendientes}")
        print(f"Incidencias resueltas: {incidencias_resueltas}")
        
        # Verificar si puede finalizar
        puede, motivo = cierre.puede_finalizar()
        print(f"\n=== ESTADO FINALIZACIÓN ===")
        print(f"Puede finalizar: {puede}")
        print(f"Motivo: {motivo}")
        
        # Mostrar tipos de incidencias pendientes
        if incidencias_pendientes > 0:
            print(f"\n=== INCIDENCIAS PENDIENTES POR TIPO ===")
            tipos_pendientes = Incidencia.objects.filter(
                cierre=cierre, 
                estado='pendiente'
            ).values('tipo').distinct()
            
            for tipo_info in tipos_pendientes:
                tipo = tipo_info['tipo']
                count = Incidencia.objects.filter(
                    cierre=cierre, 
                    estado='pendiente', 
                    tipo=tipo
                ).count()
                print(f"  {tipo}: {count} incidencias")
        
        return cierre
        
    except CierreContabilidad.DoesNotExist:
        print(f"❌ Cierre con ID {cierre_id} no encontrado")
        return None

def actualizar_estado_cierre(cierre_id):
    """
    Función para forzar la actualización del estado de un cierre
    """
    try:
        cierre = CierreContabilidad.objects.get(id=cierre_id)
        estado_anterior = cierre.estado
        
        print(f"🔄 Actualizando estado del cierre {cierre_id}...")
        print(f"Estado anterior: {estado_anterior}")
        
        estado_nuevo = cierre.actualizar_estado_automatico()
        
        print(f"Estado nuevo: {estado_nuevo}")
        
        if estado_anterior != estado_nuevo:
            print(f"✅ Estado actualizado: {estado_anterior} → {estado_nuevo}")
        else:
            print(f"ℹ️  Estado sin cambios: {estado_nuevo}")
            
        return cierre
        
    except CierreContabilidad.DoesNotExist:
        print(f"❌ Cierre con ID {cierre_id} no encontrado")
        return None

def listar_cierres_candidatos():
    """
    Lista todos los cierres que podrían estar listos para actualizar estado
    """
    print("=== CIERRES CANDIDATOS PARA ACTUALIZACIÓN ===")
    
    # Buscar cierres que no están en sin_incidencias pero podrían estarlo
    cierres = CierreContabilidad.objects.exclude(
        estado__in=['sin_incidencias', 'finalizado', 'generando_reportes']
    ).order_by('-id')
    
    for cierre in cierres:
        incidencias_pendientes = Incidencia.objects.filter(
            cierre=cierre, 
            estado='pendiente'
        ).count()
        
        print(f"ID {cierre.id}: {cierre.cliente.nombre} - {cierre.periodo}")
        print(f"  Estado: {cierre.estado}")
        print(f"  Incidencias pendientes: {incidencias_pendientes}")
        print(f"  {'✅ Candidato' if incidencias_pendientes == 0 else '❌ Tiene incidencias'}")
        print()

# Ejemplos de uso:
print("Funciones disponibles:")
print("- debuggear_cierre(ID) - Para ver detalles de un cierre")
print("- actualizar_estado_cierre(ID) - Para actualizar estado de un cierre")
print("- listar_cierres_candidatos() - Para ver cierres que pueden actualizarse")
print()
print("Ejemplo: debuggear_cierre(123)")
