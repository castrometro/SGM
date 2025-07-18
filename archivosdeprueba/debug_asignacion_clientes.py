#!/usr/bin/env python
"""
Debug de asignación de clientes a analistas
Analiza por qué algunos clientes aparecen disponibles y otros no
"""

import os
import sys
import django
from django.db import transaction
from django.db.models import Q, Prefetch

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.append('/root/SGM')
sys.path.append('/root/SGM/backend')

django.setup()

from api.models import Cliente, Usuario, AsignacionClienteUsuario, ServicioCliente, Servicio, Area

def debug_clientes_disponibles(analista_id, gerente_id):
    """
    Simula la lógica EXACTA de clientes_disponibles() del backend
    """
    print(f"\n{'='*60}")
    print(f"DEBUG: Clientes disponibles para Analista ID: {analista_id}")
    print(f"{'='*60}")
    
    try:
        # Obtener objetos
        analista = Usuario.objects.get(id=analista_id, tipo_usuario='analista')
        gerente = Usuario.objects.get(id=gerente_id, tipo_usuario='gerente')
        
        print(f"🔍 Analista: {analista.nombre} {analista.apellido} ({analista.correo_bdo})")
        print(f"🔍 Gerente: {gerente.nombre} {gerente.apellido} ({gerente.correo_bdo})")
        
        # Obtener áreas
        areas_gerente = gerente.areas.all()
        areas_analista = analista.areas.all()
        
        print(f"\n📍 Áreas del Gerente: {[area.nombre for area in areas_gerente]}")
        print(f"📍 Áreas del Analista: {[area.nombre for area in areas_analista]}")
        
        # Áreas en común (LÓGICA EXACTA DEL BACKEND)
        areas_gerente_ids = list(areas_gerente.values_list('id', flat=True))
        areas_analista_ids = list(areas_analista.values_list('id', flat=True))
        areas_comunes_ids = list(set(areas_gerente_ids) & set(areas_analista_ids))
        
        print(f"🔗 Áreas en común (IDs): {areas_comunes_ids}")
        
        if not areas_comunes_ids:
            print("❌ No hay áreas en común entre gerente y analista")
            return []
        
        # ========== LÓGICA EXACTA DEL BACKEND ==========
        # Clientes que tienen servicios contratados en las áreas comunes
        clientes_con_servicios_area = Cliente.objects.filter(
            servicios_contratados__servicio__area_id__in=areas_comunes_ids
        ).distinct()
        
        print(f"\n📊 Clientes con servicios en áreas comunes: {clientes_con_servicios_area.count()}")
        
        # 1. Excluir clientes que YA ESTÁN asignados a este analista
        clientes_ya_asignados_a_analista = AsignacionClienteUsuario.objects.filter(
            usuario=analista
        ).values_list('cliente_id', flat=True)
        
        print(f"✅ Clientes ya asignados a este analista: {len(clientes_ya_asignados_a_analista)}")
        
        # 2. Excluir clientes que ya tienen analista asignado en alguna de las áreas comunes (pero de otros analistas)
        clientes_ocupados_en_areas = []
        for cliente in clientes_con_servicios_area.exclude(id__in=clientes_ya_asignados_a_analista):
            asignaciones_existentes = AsignacionClienteUsuario.objects.filter(
                cliente=cliente,
                usuario__areas__id__in=areas_comunes_ids
            ).exclude(usuario=analista).prefetch_related('usuario__areas')
            
            if asignaciones_existentes.exists():
                # Verificar si hay conflicto de áreas
                for asignacion in asignaciones_existentes:
                    areas_asignado_ids = list(asignacion.usuario.areas.values_list('id', flat=True))
                    if set(areas_comunes_ids) & set(areas_asignado_ids):
                        clientes_ocupados_en_areas.append(cliente.id)
                        break
        
        # Obtener lista final de clientes disponibles
        clientes_excluidos = list(clientes_ya_asignados_a_analista) + clientes_ocupados_en_areas
        disponibles = clientes_con_servicios_area.exclude(id__in=clientes_excluidos)
        
        print(f"\n📊 Clientes ocupados en áreas: {len(clientes_ocupados_en_areas)}")
        print(f"📊 Total excluidos: {len(clientes_excluidos)}")
        print(f"📊 DISPONIBLES FINALES: {disponibles.count()}")
        
        # ========== ANÁLISIS DETALLADO ==========
        print(f"\n{'='*50}")
        print("ANÁLISIS DETALLADO - POR QUÉ NO APARECEN CLIENTES")
        print(f"{'='*50}")
        
        # Verificar TODOS los clientes que no aparecen
        todos_los_clientes = Cliente.objects.all()
        print(f"\n📊 Total de clientes en el sistema: {todos_los_clientes.count()}")
        
        clientes_sin_servicios = 0
        clientes_sin_servicios_en_areas = 0
        
        for cliente in todos_los_clientes:
            if cliente not in disponibles:
                servicios_cliente = cliente.servicios_contratados.all()
                
                if not servicios_cliente.exists():
                    clientes_sin_servicios += 1
                    print(f"🚫 {cliente.nombre} ({cliente.rut}) - SIN SERVICIOS CONTRATADOS")
                    continue
                
                servicios_en_areas = cliente.servicios_contratados.filter(
                    servicio__area_id__in=areas_comunes_ids
                )
                
                if not servicios_en_areas.exists():
                    clientes_sin_servicios_en_areas += 1
                    areas_cliente = [s.servicio.area.nombre for s in servicios_cliente]
                    print(f"🚫 {cliente.nombre} ({cliente.rut}) - SERVICIOS EN OTRAS ÁREAS: {areas_cliente}")
                    continue
                
                if cliente.id in clientes_ya_asignados_a_analista:
                    print(f"✅ {cliente.nombre} ({cliente.rut}) - YA ASIGNADO A ESTE ANALISTA")
                    continue
                
                if cliente.id in clientes_ocupados_en_areas:
                    print(f"❌ {cliente.nombre} ({cliente.rut}) - OCUPADO POR OTRO ANALISTA")
                    asignaciones = AsignacionClienteUsuario.objects.filter(
                        cliente=cliente,
                        usuario__areas__id__in=areas_comunes_ids
                    ).exclude(usuario=analista).select_related('usuario')
                    
                    for asignacion in asignaciones:
                        areas_asignado = list(asignacion.usuario.areas.values_list('id', flat=True))
                        if set(areas_comunes_ids) & set(areas_asignado):
                            print(f"    → Asignado a: {asignacion.usuario.nombre} {asignacion.usuario.apellido}")
                    continue
        
        print(f"\n{'='*50}")
        print("RESUMEN DE EXCLUSIONES")
        print(f"{'='*50}")
        print(f"🚫 Clientes sin servicios contratados: {clientes_sin_servicios}")
        print(f"🚫 Clientes con servicios en otras áreas: {clientes_sin_servicios_en_areas}")
        print(f"✅ Clientes ya asignados a este analista: {len(clientes_ya_asignados_a_analista)}")
        print(f"❌ Clientes ocupados por otros analistas: {len(clientes_ocupados_en_areas)}")
        print(f"✅ CLIENTES DISPONIBLES: {disponibles.count()}")
        
        if disponibles.exists():
            print(f"\n✅ CLIENTES DISPONIBLES:")
            for cliente in disponibles:
                servicios = cliente.servicios_contratados.filter(
                    servicio__area_id__in=areas_comunes_ids
                )
                areas_servicios = [s.servicio.area.nombre for s in servicios]
                print(f"   - {cliente.nombre} ({cliente.rut}) - Áreas: {areas_servicios}")
        
        return disponibles
        
        print(f"\n{'='*50}")
        print("RESUMEN")
        print(f"{'='*50}")
        print(f"📊 Total clientes con servicios en áreas comunes: {clientes_con_servicios.count()}")
        print(f"✅ Clientes disponibles: {len(clientes_disponibles)}")
        print(f"❌ Clientes ocupados: {len(clientes_ocupados)}")
        print(f"🔄 Clientes ya asignados a este analista: {len(clientes_ya_asignados)}")
        
        if clientes_disponibles:
            print(f"\n✅ CLIENTES DISPONIBLES:")
            for cliente in clientes_disponibles:
                print(f"   - {cliente.nombre} ({cliente.rut})")
        
        if clientes_ocupados:
            print(f"\n❌ CLIENTES OCUPADOS:")
            for cliente in clientes_ocupados:
                print(f"   - {cliente.nombre} ({cliente.rut})")
        
        return clientes_disponibles, clientes_ocupados
        
    except Usuario.DoesNotExist as e:
        print(f"❌ Error: {e}")
        return [], []

def debug_todas_las_asignaciones():
    """
    Muestra todas las asignaciones actuales
    """
    print(f"\n{'='*60}")
    print("TODAS LAS ASIGNACIONES ACTUALES")
    print(f"{'='*60}")
    
    asignaciones = AsignacionClienteUsuario.objects.all().select_related(
        'cliente', 'usuario'
    ).prefetch_related('usuario__areas')
    
    for asignacion in asignaciones:
        areas_usuario = [area.nombre for area in asignacion.usuario.areas.all()]
        print(f"👤 {asignacion.usuario.nombre} {asignacion.usuario.apellido} ({asignacion.usuario.tipo_usuario})")
        print(f"   🏢 Cliente: {asignacion.cliente.nombre} ({asignacion.cliente.rut})")
        print(f"   📍 Áreas: {areas_usuario}")
        print(f"   📅 Fecha: {asignacion.fecha_asignacion.strftime('%Y-%m-%d %H:%M')}")
        print()

def debug_clientes_sin_asignar():
    """
    Muestra clientes que no tienen ninguna asignación
    """
    print(f"\n{'='*60}")
    print("CLIENTES SIN ASIGNACIÓN")
    print(f"{'='*60}")
    
    clientes_sin_asignar = Cliente.objects.filter(
        asignaciones__isnull=True
    ).prefetch_related('servicios_contratados__servicio__area')
    
    for cliente in clientes_sin_asignar:
        print(f"🏢 {cliente.nombre} ({cliente.rut})")
        servicios = cliente.servicios_contratados.all()
        if servicios:
            print(f"   📋 Servicios: {[f'{s.servicio.nombre} ({s.servicio.area.nombre})' for s in servicios]}")
        else:
            print(f"   📋 Sin servicios contratados")
        print()

def debug_analistas_areas():
    """
    Muestra todos los analistas y sus áreas
    """
    print(f"\n{'='*60}")
    print("ANALISTAS Y SUS ÁREAS")
    print(f"{'='*60}")
    
    analistas = Usuario.objects.filter(
        tipo_usuario='analista',
        is_active=True
    ).prefetch_related('areas')
    
    for analista in analistas:
        areas = [area.nombre for area in analista.areas.all()]
        print(f"👤 {analista.nombre} {analista.apellido} ({analista.correo_bdo})")
        print(f"   📍 Áreas: {areas}")
        
        # Contar clientes asignados
        clientes_count = AsignacionClienteUsuario.objects.filter(usuario=analista).count()
        print(f"   📊 Clientes asignados: {clientes_count}")
        print()

def main():
    """
    Función principal de debug
    """
    print("🔍 DEBUG: Asignación de Clientes a Analistas")
    print("=" * 60)
    
    # Mostrar estructura general
    debug_analistas_areas()
    debug_todas_las_asignaciones()
    debug_clientes_sin_asignar()
    
    # Ejemplo específico - necesitas ajustar estos IDs
    print("\n" + "="*60)
    print("EJEMPLO ESPECÍFICO")
    print("="*60)
    
    # Obtener IDs de ejemplo
    gerente = Usuario.objects.filter(tipo_usuario='gerente').first()
    analista = Usuario.objects.filter(tipo_usuario='analista').first()
    
    if gerente and analista:
        print(f"Usando Gerente: {gerente.nombre} {gerente.apellido} (ID: {gerente.id})")
        print(f"Usando Analista: {analista.nombre} {analista.apellido} (ID: {analista.id})")
        
        debug_clientes_disponibles(analista.id, gerente.id)
    else:
        print("❌ No se encontraron gerente o analista de ejemplo")

if __name__ == "__main__":
    main()
