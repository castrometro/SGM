#!/bin/bash

# Script para medir los requisitos REALES de tu SGM
# Autor: Análisis de Performance SGM
# Uso: ./medir-requisitos-reales.sh

echo "🔬 MEDICIÓN DE REQUISITOS REALES - SGM CONTABILIDAD"
echo "=================================================="

# Crear directorio para logs de medición
MEDICION_DIR="mediciones_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$MEDICION_DIR"

echo "📊 Guardando mediciones en: $MEDICION_DIR"

# Función para capturar métricas del sistema
capturar_metricas() {
    local etiqueta="$1"
    local archivo="$MEDICION_DIR/metricas_${etiqueta}.log"
    
    echo "=== MEDICIÓN: $etiqueta - $(date) ===" >> "$archivo"
    
    # CPU
    echo "--- CPU ---" >> "$archivo"
    top -bn1 | grep "Cpu(s)" >> "$archivo"
    
    # Memoria
    echo "--- MEMORIA ---" >> "$archivo"
    free -h >> "$archivo"
    
    # Memoria por proceso
    echo "--- TOP PROCESOS POR MEMORIA ---" >> "$archivo"
    ps aux --sort=-%mem | head -10 >> "$archivo"
    
    # Docker stats si está corriendo
    if command -v docker &> /dev/null && docker ps -q &> /dev/null; then
        echo "--- DOCKER STATS ---" >> "$archivo"
        docker stats --no-stream >> "$archivo" 2>/dev/null || echo "Docker no disponible" >> "$archivo"
    fi
    
    # Disco
    echo "--- ESPACIO EN DISCO ---" >> "$archivo"
    df -h >> "$archivo"
    
    # Red (si está disponible)
    echo "--- RED ---" >> "$archivo"
    netstat -i >> "$archivo" 2>/dev/null || echo "netstat no disponible" >> "$archivo"
    
    # Procesos Python/Django/Celery
    echo "--- PROCESOS PYTHON ---" >> "$archivo"
    ps aux | grep -E "(python|django|celery|gunicorn)" | grep -v grep >> "$archivo"
    
    echo "" >> "$archivo"
}

# Función para simular carga
simular_carga_excel() {
    echo "📈 Simulando procesamiento de archivos Excel..."
    
    # Crear archivo Excel de prueba si no existe
    if [ ! -f "test_excel_simulation.py" ]; then
        cat > test_excel_simulation.py << 'PYTHON_EOF'
import pandas as pd
import time
import psutil
import sys
from openpyxl import Workbook
import os

def crear_archivo_prueba(filas=1000):
    """Crear archivo Excel de prueba"""
    print(f"Creando archivo Excel con {filas} filas...")
    
    # Datos simulados típicos de rinde gastos
    data = {
        'fecha': pd.date_range('2024-01-01', periods=filas),
        'rut': [f'12345678-{i%10}' for i in range(filas)],
        'nombre': [f'Empleado {i}' for i in range(filas)],
        'monto': [round(50000 + (i * 1000), 2) for i in range(filas)],
        'centro_costo': [f'CC{i%10:03d}' for i in range(filas)],
        'descripcion': [f'Gasto número {i} descripción larga para simular datos reales' for i in range(filas)],
        'tipo_gasto': ['Combustible', 'Alimentación', 'Transporte', 'Hospedaje', 'Otros'][i%5] for i in range(filas),
        'proyecto': [f'PRY{i%20:03d}' for i in range(filas)]
    }
    
    df = pd.DataFrame(data)
    archivo = f'test_rindegastos_{filas}_filas.xlsx'
    df.to_excel(archivo, index=False)
    print(f"Archivo creado: {archivo} ({os.path.getsize(archivo)/1024/1024:.2f} MB)")
    return archivo

def procesar_archivo_simulado(archivo):
    """Simular el procesamiento que hace Celery"""
    print(f"Procesando {archivo}...")
    
    # Medir recursos iniciales
    proceso = psutil.Process()
    cpu_inicial = proceso.cpu_percent()
    memoria_inicial = proceso.memory_info().rss / 1024 / 1024  # MB
    
    inicio = time.time()
    
    # Simular procesamiento real
    df = pd.read_excel(archivo)
    print(f"Cargado DataFrame con {len(df)} filas")
    
    # Simular validaciones y transformaciones
    time.sleep(1)  # Simular tiempo de procesamiento
    
    # Operaciones típicas del sistema
    df['monto_formateado'] = df['monto'].apply(lambda x: f"${x:,.2f}")
    df['rut_limpio'] = df['rut'].str.replace('-', '')
    df['mes'] = df['fecha'].dt.month
    df['año'] = df['fecha'].dt.year
    
    # Agrupaciones típicas
    resumen_cc = df.groupby('centro_costo')['monto'].sum()
    resumen_tipo = df.groupby('tipo_gasto')['monto'].sum()
    
    # Simular escritura de resultado
    archivo_resultado = archivo.replace('.xlsx', '_procesado.xlsx')
    df.to_excel(archivo_resultado, index=False)
    
    fin = time.time()
    
    # Medir recursos finales
    cpu_final = proceso.cpu_percent()
    memoria_final = proceso.memory_info().rss / 1024 / 1024  # MB
    
    print(f"Procesamiento completado en {fin-inicio:.2f} segundos")
    print(f"Memoria usada: {memoria_final:.2f} MB (delta: +{memoria_final-memoria_inicial:.2f} MB)")
    print(f"CPU promedio: {(cpu_inicial+cpu_final)/2:.1f}%")
    
    return {
        'tiempo': fin-inicio,
        'memoria_mb': memoria_final,
        'cpu_pct': (cpu_inicial+cpu_final)/2,
        'filas_procesadas': len(df)
    }

def main():
    print("🧪 SIMULACIÓN DE PROCESAMIENTO EXCEL")
    print("====================================")
    
    # Diferentes tamaños de archivo para medir escalabilidad
    tamaños = [100, 500, 1000, 2500] if len(sys.argv) == 1 else [int(sys.argv[1])]
    
    resultados = []
    
    for filas in tamaños:
        print(f"\n--- Prueba con {filas} filas ---")
        archivo = crear_archivo_prueba(filas)
        resultado = procesar_archivo_simulado(archivo)
        resultado['filas'] = filas
        resultados.append(resultado)
        
        # Limpiar archivo temporal
        os.remove(archivo)
        archivo_procesado = archivo.replace('.xlsx', '_procesado.xlsx')
        if os.path.exists(archivo_procesado):
            os.remove(archivo_procesado)
    
    # Resumen de resultados
    print("\n📊 RESUMEN DE MEDICIONES:")
    print("=========================")
    print(f"{'Filas':<8} {'Tiempo (s)':<12} {'Memoria (MB)':<15} {'CPU (%)':<10}")
    print("-" * 50)
    
    for r in resultados:
        print(f"{r['filas']:<8} {r['tiempo']:<12.2f} {r['memoria_mb']:<15.2f} {r['cpu_pct']:<10.1f}")
    
    # Proyección para 3 usuarios
    if len(resultados) > 0:
        promedio = resultados[-1]  # Usar el archivo más grande
        print(f"\n🎯 PROYECCIÓN PARA 3 USUARIOS CONCURRENTES:")
        print(f"Memoria estimada: {promedio['memoria_mb'] * 3:.2f} MB")
        print(f"CPU estimado: {promedio['cpu_pct'] * 3:.1f}%")

if __name__ == "__main__":
    main()
PYTHON_EOF
    fi
    
    # Ejecutar simulación si Python está disponible
    if command -v python3 &> /dev/null; then
        echo "Ejecutando simulación con Python..."
        python3 test_excel_simulation.py 1000 2>&1 | tee "$MEDICION_DIR/simulacion_excel.log"
    else
        echo "Python3 no disponible para simulación"
    fi
}

# PASO 1: Medir sistema en reposo
echo "📊 PASO 1: Midiendo sistema en REPOSO..."
capturar_metricas "reposo"
sleep 5

# PASO 2: Si Docker está corriendo, medir con SGM activo
if docker ps | grep -q sgm; then
    echo "📊 PASO 2: Midiendo con SGM ACTIVO..."
    capturar_metricas "sgm_activo"
    sleep 5
    
    # PASO 3: Simular carga si es posible
    echo "📊 PASO 3: Simulando CARGA DE TRABAJO..."
    capturar_metricas "pre_carga"
    simular_carga_excel
    capturar_metricas "post_carga"
else
    echo "📊 Docker/SGM no está corriendo. Saltando medición con carga."
fi

# PASO 4: Análisis de los resultados
echo ""
echo "📋 ANÁLISIS DE RESULTADOS"
echo "========================="

# Extraer métricas clave
for archivo in "$MEDICION_DIR"/*.log; do
    if [ -f "$archivo" ]; then
        echo ""
        echo "--- $(basename "$archivo") ---"
        
        # CPU
        if grep -q "Cpu(s)" "$archivo"; then
            cpu_line=$(grep "Cpu(s)" "$archivo" | tail -1)
            echo "CPU: $cpu_line"
        fi
        
        # Memoria
        if grep -q "Mem:" "$archivo"; then
            mem_line=$(grep "Mem:" "$archivo" | tail -1)
            echo "Memoria: $mem_line"
        fi
        
        # Docker stats si hay
        if grep -q "CONTAINER" "$archivo"; then
            echo "Docker containers activos encontrados"
        fi
    fi
done

# Crear resumen ejecutivo
cat > "$MEDICION_DIR/RESUMEN_EJECUTIVO.md" << 'EOF'
# Resumen Ejecutivo - Medición de Requisitos SGM

## Metodología de Medición

Esta medición se realizó capturando métricas del sistema en diferentes estados:
1. **Reposo**: Sistema base sin carga
2. **SGM Activo**: Con contenedores Docker corriendo
3. **Bajo Carga**: Simulando procesamiento de archivos Excel

## Interpretación de Resultados

### Memoria Mínima Requerida
- **Sistema en reposo**: Base del sistema operativo
- **SGM activo**: Memoria base + contenedores Docker
- **Bajo carga**: Pico máximo durante procesamiento

### CPU Mínimo Requerido
- **Promedio normal**: Operaciones típicas de navegación
- **Picos de procesamiento**: Durante subida y procesamiento de Excel
- **Concurrencia**: Multiplicar por número de usuarios simultáneos

### Recomendaciones

1. **Mínimo absoluto**: Memoria en reposo + 50% buffer
2. **Recomendado**: Pico máximo medido + 25% buffer  
3. **Producción**: Recomendado + capacidad de crecimiento

### Fórmula de Escalamiento

```
Usuarios adicionales = Memoria_pico_1_usuario × N_usuarios × 1.2
CPU_requerido = CPU_pico_1_usuario × N_usuarios × 0.8 (overlap)
```

## Próximos Pasos

1. Revisar archivos de medición detallados
2. Comparar con especificaciones estimadas
3. Ajustar configuración Docker según resultados reales
4. Implementar monitoreo continuo en producción
EOF

echo ""
echo "✅ Medición completada!"
echo "📁 Resultados guardados en: $MEDICION_DIR/"
echo "📄 Ver resumen: cat $MEDICION_DIR/RESUMEN_EJECUTIVO.md"
echo ""
echo "🔍 Para revisar mediciones detalladas:"
echo "   ls -la $MEDICION_DIR/"
echo "   cat $MEDICION_DIR/metricas_*.log"
echo ""
echo "💡 INTERPRETACIÓN RÁPIDA:"

# Mostrar uso actual de memoria y CPU
echo "Memoria actual del sistema:"
free -h | grep -E "(Mem|Swap)"

echo ""
echo "CPU actual:"
top -bn1 | grep "Cpu(s)"

echo ""
echo "🎯 Con estos datos REALES puedes:"
echo "1. Validar las estimaciones teóricas"
echo "2. Ajustar la configuración Docker"
echo "3. Dimensionar hardware con precisión"
echo "4. Configurar alertas de monitoreo"