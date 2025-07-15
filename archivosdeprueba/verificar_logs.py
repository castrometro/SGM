#!/usr/bin/env python3
"""
Script simple para verificar logs desde el shell de Django
"""

from contabilidad.models import TarjetaActivityLog

def verificar_logs():
    # Contar logs totales
    total = TarjetaActivityLog.objects.count()
    print(f"📊 Total de logs: {total}")
    
    # Últimos 10 logs
    logs = TarjetaActivityLog.objects.order_by('-id')[:10]
    
    print("\n🔍 Últimos 10 logs de actividad:")
    print("-" * 80)
    
    for log in logs:
        timestamp = log.timestamp.strftime('%d/%m %H:%M:%S')
        cliente = log.cierre.cliente.nombre if log.cierre else "N/A"
        print(f"{timestamp} | {cliente} | {log.tarjeta} | {log.accion}")
        print(f"  📝 {log.descripcion}")
        print()

if __name__ == "__main__":
    verificar_logs()
