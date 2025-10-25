#!/bin/bash

# 🧪 SCRIPT DE PRUEBA: Consolidación Refactorizada
# ================================================
# Verifica que el módulo tasks_refactored/consolidacion.py funcione correctamente

echo "🔍 VERIFICACIÓN DE CONSOLIDACIÓN REFACTORIZADA"
echo "=============================================="
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Verificar que no hay dependencias de tasks.py
echo "📋 1. Verificando dependencias..."
if grep -q "from.*tasks import\|from nomina.tasks import" backend/nomina/tasks_refactored/consolidacion.py; then
    echo -e "${RED}❌ ERROR: Encontradas dependencias de tasks.py${NC}"
    grep "from.*tasks import" backend/nomina/tasks_refactored/consolidacion.py
    exit 1
else
    echo -e "${GREEN}✅ Sin dependencias de tasks.py${NC}"
fi
echo ""

# 2. Contar funciones definidas
echo "📊 2. Contando funciones definidas..."
FUNCS=$(grep -c "^@shared_task\|^def " backend/nomina/tasks_refactored/consolidacion.py)
echo -e "${GREEN}✅ $FUNCS funciones/tasks encontradas${NC}"
echo ""

# 3. Verificar imports en views
echo "🔗 3. Verificando integración con views..."
if grep -q "consolidar_datos_nomina_con_logging" backend/nomina/views_consolidacion.py; then
    echo -e "${GREEN}✅ views_consolidacion.py usa tasks_refactored${NC}"
else
    echo -e "${RED}❌ ERROR: views_consolidacion.py no usa tasks_refactored${NC}"
    exit 1
fi
echo ""

# 4. Verificar que el módulo se puede importar
echo "🐍 4. Probando importación en Django..."
docker compose exec -T django python manage.py shell << 'EOF'
try:
    from nomina.tasks_refactored.consolidacion import (
        normalizar_rut,
        calcular_chunk_size_dinamico,
        log_consolidacion_start,
        log_consolidacion_complete,
        log_consolidacion_error,
        consolidar_datos_nomina_con_logging,
        consolidar_datos_nomina_task_optimizado,
        procesar_empleados_libro_paralelo,
        procesar_movimientos_personal_paralelo,
        procesar_conceptos_consolidados_paralelo,
        finalizar_consolidacion_post_movimientos,
        consolidar_datos_nomina_task_secuencial
    )
    print("✅ Todas las funciones importadas correctamente")
    
    # Probar funciones auxiliares
    rut = normalizar_rut("12.345.678-9")
    assert rut == "123456789", f"Error en normalizar_rut: {rut}"
    print(f"✅ normalizar_rut('12.345.678-9') = '{rut}'")
    
    chunk = calcular_chunk_size_dinamico(150)
    assert chunk == 50, f"Error en calcular_chunk_size_dinamico: {chunk}"
    print(f"✅ calcular_chunk_size_dinamico(150) = {chunk}")
    
    print("")
    print("🎉 TODAS LAS PRUEBAS PASARON")
    exit(0)
except ImportError as e:
    print(f"❌ ERROR DE IMPORTACIÓN: {e}")
    exit(1)
except AssertionError as e:
    print(f"❌ ERROR EN PRUEBA: {e}")
    exit(1)
except Exception as e:
    print(f"❌ ERROR INESPERADO: {e}")
    exit(1)
EOF

RESULT=$?
echo ""

if [ $RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ Importación exitosa${NC}"
else
    echo -e "${RED}❌ ERROR en importación${NC}"
    exit 1
fi
echo ""

# 5. Listar cierres disponibles para prueba
echo "📁 5. Listando cierres disponibles para prueba..."
docker compose exec -T django python manage.py shell << 'EOF'
from nomina.models import CierreNomina

cierres = CierreNomina.objects.all().order_by('-created_at')[:5]

if not cierres:
    print("⚠️  No hay cierres disponibles")
    exit(0)

print(f"📊 Últimos {len(cierres)} cierres:")
print("")
for cierre in cierres:
    print(f"  ID: {cierre.id}")
    print(f"  Cliente: {cierre.cliente.razon_social}")
    print(f"  Periodo: {cierre.periodo}")
    print(f"  Estado: {cierre.estado}")
    print(f"  Consolidación: {cierre.estado_consolidacion or 'N/A'}")
    print(f"  Empleados: {cierre.nomina_consolidada.count()}")
    print("")

# Sugerir cierre para prueba
cierre_prueba = cierres.filter(
    estado__in=['verificado_sin_discrepancias', 'datos_consolidados']
).first()

if cierre_prueba:
    print(f"💡 Sugerencia: Usar cierre ID {cierre_prueba.id} ({cierre_prueba.cliente.razon_social})")
    print(f"   Estado: {cierre_prueba.estado}")
    print("")
    print(f"   Para probar manualmente:")
    print(f"   POST /api/nomina/consolidacion/{cierre_prueba.id}/consolidar/")
    print(f"   Body: {{ \"modo\": \"optimizado\" }}")
EOF

echo ""

# 6. Verificar estructura de archivos
echo "📂 6. Verificando estructura de archivos..."
FILES=(
    "backend/nomina/tasks_refactored/__init__.py"
    "backend/nomina/tasks_refactored/consolidacion.py"
    "backend/nomina/views_consolidacion.py"
)

ALL_OK=true
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅${NC} $file"
    else
        echo -e "${RED}❌${NC} $file (NO ENCONTRADO)"
        ALL_OK=false
    fi
done
echo ""

if [ "$ALL_OK" = false ]; then
    echo -e "${RED}❌ Algunos archivos no se encontraron${NC}"
    exit 1
fi

# 7. Verificar que Celery puede ver las tasks
echo "🔄 7. Verificando registro de tasks en Celery..."
docker compose exec -T celery_worker celery -A sgm_backend inspect registered | grep consolidar_datos_nomina_con_logging > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Task consolidar_datos_nomina_con_logging registrada en Celery${NC}"
else
    echo -e "${YELLOW}⚠️  No se pudo verificar task en Celery (puede estar OK si el worker está apagado)${NC}"
fi
echo ""

# Resumen final
echo "════════════════════════════════════════════"
echo -e "${GREEN}✅ VERIFICACIÓN COMPLETA${NC}"
echo "════════════════════════════════════════════"
echo ""
echo "📦 Módulo: backend/nomina/tasks_refactored/consolidacion.py"
echo "📏 Tamaño: $(wc -l < backend/nomina/tasks_refactored/consolidacion.py) líneas"
echo "🔧 Funciones: $FUNCS"
echo ""
echo "🎯 PRÓXIMOS PASOS:"
echo "  1. Usar la UI para consolidar un cierre"
echo "  2. Monitorear logs: docker compose logs -f celery_worker"
echo "  3. Verificar resultados en la base de datos"
echo ""
echo "📚 Documentación completa: FLUJO_CONSOLIDACION_VISUAL.md"
echo ""
