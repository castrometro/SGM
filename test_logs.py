#!/usr/bin/env python3
"""
Script para probar que los logs funcionan correctamente
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
django.setup()

from api.models import ActividadTarjeta, Cliente
from datetime import date

def verificar_logs_recientes():
    """Verificar los logs más recientes relacionados con clasificaciones"""
    print("=== VERIFICANDO LOGS DE CLASIFICACIONES ===\n")
    
    # Obtener logs recientes de clasificaciones
    logs_clasificacion = ActividadTarjeta.objects.filter(
        tarjeta='clasificacion',
        fecha_creacion__date=date.today()
    ).order_by('-fecha_creacion')[:20]
    
    if not logs_clasificacion.exists():
        print("❌ No se encontraron logs de clasificaciones para hoy")
        print("💡 Intenta usar el modal para generar logs")
        return
    
    print(f"✅ Se encontraron {logs_clasificacion.count()} logs de clasificaciones para hoy:\n")
    
    for log in logs_clasificacion:
        cliente_nombre = log.cliente.nombre if log.cliente else "Sin cliente"
        usuario_nombre = log.usuario.username if log.usuario else "Sin usuario"
        
        print(f"🕐 {log.fecha_creacion.strftime('%H:%M:%S')}")
        print(f"👤 Usuario: {usuario_nombre}")
        print(f"🏢 Cliente: {cliente_nombre}")
        print(f"🔧 Acción: {log.accion}")
        print(f"📝 Descripción: {log.descripcion}")
        if log.detalles:
            print(f"📋 Detalles: {log.detalles}")
        print(f"✅ Resultado: {log.resultado}")
        print("-" * 50)

def verificar_clientes_disponibles():
    """Mostrar clientes disponibles para testing"""
    print("\n=== CLIENTES DISPONIBLES ===\n")
    
    clientes = Cliente.objects.all()[:10]
    if not clientes.exists():
        print("❌ No hay clientes en la base de datos")
        return
    
    for cliente in clientes:
        print(f"ID: {cliente.id} - {cliente.nombre}")

if __name__ == "__main__":
    verificar_logs_recientes()
    verificar_clientes_disponibles()
    
    print("\n=== INSTRUCCIONES PARA PROBAR ===")
    print("1. Abre el frontend y navega a la tarjeta de clasificaciones")
    print("2. Abre el modal de clasificaciones")
    print("3. Cambia a la pestaña 'Sets y Opciones'")
    print("4. Crea, edita o elimina algunos sets/opciones")
    print("5. Vuelve a la pestaña 'Registros Raw' y crea/edita/elimina registros")
    print("6. Ejecuta este script nuevamente para ver los logs generados")
    print("\n🔍 Para ver logs en tiempo real: python3 /root/SGM/test_logs.py")
