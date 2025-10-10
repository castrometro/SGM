#!/bin/bash

# Script para hacer benchmark específico del sistema SGM actual
# Mide rendimiento real mientras procesas archivos Excel
# Uso: ./benchmark-sgm-actual.sh

echo "🏋️ BENCHMARK SISTEMA SGM ACTUAL"
echo "==============================="

# Verificar si el sistema SGM está corriendo
check_sgm_running() {
    if ! docker ps | grep -q "sgm\|django\|postgres"; then
        echo "⚠️  Sistema SGM no detectado corriendo"
        echo "¿Quieres que inicie el sistema para hacer el benchmark? (y/n)"
        read -r respuesta
        if [ "$respuesta" = "y" ]; then
            echo "Iniciando sistema..."
            if [ -f "docker-compose.yml" ]; then
                docker-compose up -d
                echo "Esperando que el sistema esté listo..."
                sleep 30
            else
                echo "❌ No se encontró docker-compose.yml"
                return 1
            fi
        else
            echo "❌ Benchmark cancelado. Necesito el sistema corriendo para medir."
            return 1
        fi
    fi
    return 0
}

# Función para medir recursos en tiempo real durante X segundos
monitor_real_time() {
    local duration=$1
    local label=$2
    local output_file="benchmark_${label}_$(date +%H%M%S).csv"
    
    echo "🔍 Monitoreando '$label' por $duration segundos..."
    echo "timestamp,cpu_percent,memory_used_gb,memory_percent,docker_containers" > "$output_file"
    
    for i in $(seq 1 $duration); do
        timestamp=$(date '+%H:%M:%S')
        
        # CPU total del sistema
        cpu_percent=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
        
        # Memoria del sistema
        memory_info=$(free | awk 'NR==2{printf "%.2f,%.1f", $3/1024/1024, $3*100/$2}')
        
        # Contenedores Docker activos
        docker_count=$(docker ps -q | wc -l)
        
        echo "$timestamp,$cpu_percent,$memory_info,$docker_count" >> "$output_file"
        sleep 1
    done
    
    echo "📊 Datos guardados en: $output_file"
    return "$output_file"
}

# Función para analizar un archivo CSV de benchmark
analyze_benchmark() {
    local csv_file=$1
    
    echo "📈 ANÁLISIS DE $csv_file:"
    echo "========================"
    
    # Usar awk para análisis estadístico
    awk -F',' 'NR>1 {
        cpu[NR] = $2; 
        mem[NR] = $3; 
        count++
    } 
    END {
        # Calcular estadísticas CPU
        cpu_sum = 0; cpu_max = 0; cpu_min = 999;
        for(i=2; i<=count+1; i++) {
            cpu_sum += cpu[i];
            if(cpu[i] > cpu_max) cpu_max = cpu[i];
            if(cpu[i] < cpu_min) cpu_min = cpu[i];
        }
        cpu_avg = cpu_sum / count;
        
        # Calcular estadísticas Memoria
        mem_sum = 0; mem_max = 0; mem_min = 999;
        for(i=2; i<=count+1; i++) {
            mem_sum += mem[i];
            if(mem[i] > mem_max) mem_max = mem[i];
            if(mem[i] < mem_min) mem_min = mem[i];
        }
        mem_avg = mem_sum / count;
        
        printf "CPU:\n";
        printf "  Promedio: %.1f%%\n", cpu_avg;
        printf "  Máximo:   %.1f%%\n", cpu_max;
        printf "  Mínimo:   %.1f%%\n", cpu_min;
        printf "\nMemoria:\n";
        printf "  Promedio: %.2f GB\n", mem_avg;
        printf "  Máximo:   %.2f GB\n", mem_max;
        printf "  Mínimo:   %.2f GB\n", mem_min;
    }' "$csv_file"
}

# Test de carga específico para rinde gastos
test_carga_rindegastos() {
    echo "🎯 TEST DE CARGA ESPECÍFICO - RINDE GASTOS"
    echo "=========================================="
    
    # Crear archivo Excel de prueba realista
    python3 << 'PYTHON_EOF'
import pandas as pd
import os
from datetime import datetime, timedelta
import random

def crear_archivo_realista():
    print("Creando archivo Excel realista para rinde gastos...")
    
    # Datos más realistas
    empleados = [f"Juan Pérez {i}" for i in range(1, 51)]
    ruts = [f"1{random.randint(1000000, 9999999)}-{random.randint(0, 9)}" for _ in range(50)]
    centros_costo = [f"CC{i:03d}" for i in [100, 101, 102, 200, 201, 300, 301, 400]]
    tipos_gasto = ["Combustible", "Peajes", "Estacionamiento", "Alimentación", "Hospedaje", "Transporte", "Materiales", "Otros"]
    
    data = []
    
    # Generar 2000 registros (archivo mediano realista)
    for i in range(2000):
        fecha = datetime.now() - timedelta(days=random.randint(1, 30))
        empleado = random.choice(empleados)
        rut = random.choice(ruts)
        cc = random.choice(centros_costo)
        tipo = random.choice(tipos_gasto)
        
        # Montos realistas según tipo de gasto
        if tipo == "Combustible":
            monto = random.randint(25000, 80000)
        elif tipo in ["Alimentación", "Hospedaje"]:
            monto = random.randint(15000, 45000)
        elif tipo in ["Peajes", "Estacionamiento"]:
            monto = random.randint(1000, 8000)
        else:
            monto = random.randint(5000, 30000)
        
        data.append({
            'Fecha': fecha.strftime('%Y-%m-%d'),
            'RUT': rut,
            'Nombre Empleado': empleado,
            'Centro de Costo': cc,
            'Tipo de Gasto': tipo,
            'Monto': monto,
            'Descripción': f"Gasto {tipo.lower()} - {random.choice(['Proyecto A', 'Proyecto B', 'Operaciones', 'Mantención'])}",
            'Número Documento': f"DOC{random.randint(100000, 999999)}",
            'Proveedor': f"Proveedor {random.randint(1, 20)} S.A.",
            'Observaciones': f"Observación {i+1}" if i % 10 == 0 else ""
        })
    
    df = pd.DataFrame(data)
    archivo = f"test_rindegastos_realista_{len(df)}_registros.xlsx"
    df.to_excel(archivo, index=False)
    
    size_mb = os.path.getsize(archivo) / (1024 * 1024)
    print(f"✅ Archivo creado: {archivo}")
    print(f"   📊 {len(df)} registros")
    print(f"   💾 {size_mb:.2f} MB")
    print(f"   📅 Rango de fechas: {df['Fecha'].min()} a {df['Fecha'].max()}")
    print(f"   💰 Monto total: ${df['Monto'].sum():,.0f}")
    
    return archivo

if __name__ == "__main__":
    crear_archivo_realista()
PYTHON_EOF
    
    # Obtener nombre del archivo creado
    archivo_test=$(ls test_rindegastos_realista_*.xlsx 2>/dev/null | head -1)
    
    if [ -z "$archivo_test" ]; then
        echo "❌ No se pudo crear archivo de prueba"
        return 1
    fi
    
    echo ""
    echo "📤 Archivo de prueba listo: $archivo_test"
    echo ""
    echo "🚀 INSTRUCCIONES PARA BENCHMARK MANUAL:"
    echo "======================================="
    echo "1. Abre tu navegador en: http://localhost:5174 (o donde tengas el SGM)"
    echo "2. Ve a la sección de Captura Masiva de Gastos"
    echo "3. Cuando veas 'LISTO PARA SUBIR', presiona ENTER aquí para empezar a medir"
    echo "4. Sube el archivo: $archivo_test"
    echo "5. El script medirá automáticamente durante el procesamiento"
    echo ""
    read -p "Presiona ENTER cuando estés listo para empezar el benchmark..." -r
    
    # Empezar medición
    echo "🔥 INICIANDO BENCHMARK - Sube tu archivo AHORA!"
    monitor_real_time 300 "procesamiento_excel" &  # 5 minutos de medición
    monitor_pid=$!
    
    echo "⏱️  Medición en progreso... (máximo 5 minutos)"
    echo "   - Sube tu archivo Excel ahora"
    echo "   - El sistema medirá automáticamente"
    echo "   - Presiona Ctrl+C si el procesamiento termina antes"
    
    # Esperar que termine la medición o que el usuario cancele
    wait $monitor_pid 2>/dev/null
    
    # Analizar resultados
    ultimo_csv=$(ls benchmark_procesamiento_excel_*.csv 2>/dev/null | tail -1)
    if [ -n "$ultimo_csv" ]; then
        analyze_benchmark "$ultimo_csv"
        
        # Crear reporte específico
        echo ""
        echo "📋 REPORTE ESPECÍFICO RINDE GASTOS:"
        echo "=================================="
        echo "Archivo procesado: $archivo_test"
        echo "Duración medición: $(wc -l < "$ultimo_csv") segundos"
        echo ""
        
        # Extraer picos de rendimiento
        max_cpu=$(awk -F',' 'NR>1 {if($2>max) max=$2} END {print max}' "$ultimo_csv")
        max_mem=$(awk -F',' 'NR>1 {if($3>max) max=$3} END {print max}' "$ultimo_csv")
        
        echo "🎯 PARA 3 USUARIOS CONCURRENTES (Proyección):"
        echo "CPU requerido: $(echo "$max_cpu * 3" | bc -l | cut -d'.' -f1)%"
        echo "RAM requerida: $(echo "$max_mem * 3" | bc -l)GB"
        echo ""
        echo "💡 RECOMENDACIÓN HARDWARE:"
        if (( $(echo "$max_cpu * 3 > 80" | bc -l) )); then
            echo "CPU: Mínimo 4 cores (uso proyectado alto)"
        else
            echo "CPU: 2 cores suficientes"
        fi
        
        if (( $(echo "$max_mem * 3 > 6" | bc -l) )); then
            echo "RAM: Mínimo 8GB (uso proyectado alto)"
        else
            echo "RAM: 4GB suficientes"
        fi
    fi
    
    # Limpiar archivo temporal
    if [ -f "$archivo_test" ]; then
        rm "$archivo_test"
    fi
}

# Función principal
main() {
    echo "Iniciando benchmark del sistema SGM..."
    
    # Verificar requisitos
    if ! command -v python3 &> /dev/null; then
        echo "❌ Se requiere Python3 para el benchmark"
        exit 1
    fi
    
    if ! python3 -c "import pandas" 2>/dev/null; then
        echo "⚠️  Instalando pandas para el benchmark..."
        pip3 install pandas openpyxl --quiet
    fi
    
    # Verificar sistema SGM
    if ! check_sgm_running; then
        exit 1
    fi
    
    # Crear directorio de resultados
    mkdir -p "benchmark_$(date +%Y%m%d)"
    cd "benchmark_$(date +%Y%m%d)" || exit 1
    
    echo "📁 Trabajando en directorio: $(pwd)"
    echo ""
    
    # Medir sistema en reposo
    echo "1️⃣ Midiendo sistema en reposo..."
    monitor_real_time 30 "reposo"
    sleep 5
    
    # Analizar reposo
    reposo_csv=$(ls benchmark_reposo_*.csv | tail -1)
    if [ -n "$reposo_csv" ]; then
        analyze_benchmark "$reposo_csv"
    fi
    
    echo ""
    echo "2️⃣ Test de carga con archivo Excel..."
    test_carga_rindegastos
    
    echo ""
    echo "✅ BENCHMARK COMPLETADO"
    echo "======================"
    echo "📁 Archivos generados:"
    ls -la *.csv 2>/dev/null || echo "No se generaron archivos CSV"
    
    echo ""
    echo "🎯 CONCLUSIONES DEL BENCHMARK:"
    echo "=============================="
    
    # Comparar con estimaciones originales
    echo "Comparando con estimaciones teóricas..."
    echo "- Estimación CPU 3 usuarios: 70-90%"
    echo "- Estimación RAM 3 usuarios: 4-6GB"
    echo ""
    echo "Revisa los archivos CSV para datos precisos y ajusta"
    echo "la configuración Docker según los resultados reales."
}

# Ejecutar
main "$@"