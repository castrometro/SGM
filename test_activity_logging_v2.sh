#!/bin/bash
# Test de Activity Logging V2

echo "🧪 Testing Activity Logging V2 System"
echo "======================================"
echo ""

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Verificar que el middleware está activo
echo -e "${BLUE}1. Verificando middleware en settings.py...${NC}"
if grep -q "nomina.middleware.activity_middleware.ActivityCaptureMiddleware" /root/SGM/backend/sgm_backend/settings.py; then
    echo -e "${GREEN}✅ Middleware configurado${NC}"
else
    echo -e "${YELLOW}⚠️  Middleware no encontrado${NC}"
fi
echo ""

# 2. Verificar URLs de las APIs
echo -e "${BLUE}2. Verificando URLs de APIs V2...${NC}"
if grep -q "list_activities" /root/SGM/backend/nomina/urls.py; then
    echo -e "${GREEN}✅ APIs V2 registradas${NC}"
else
    echo -e "${YELLOW}⚠️  APIs V2 no encontradas${NC}"
fi
echo ""

# 3. Verificar modelo ActivityEvent
echo -e "${BLUE}3. Verificando modelo ActivityEvent...${NC}"
docker compose exec -T django python manage.py shell << 'PYEOF'
try:
    from nomina.models import ActivityEvent
    count = ActivityEvent.objects.count()
    print(f"✅ Modelo ActivityEvent OK - {count} eventos en BD")
    
    # Mostrar los últimos 3 eventos
    if count > 0:
        print("\n📊 Últimos eventos registrados:")
        for event in ActivityEvent.objects.all().order_by('-timestamp')[:3]:
            print(f"  - {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {event.action} | Cliente {event.cliente_id}")
except Exception as e:
    print(f"❌ Error: {e}")
PYEOF
echo ""

# 4. Verificar que frontend tiene el logger V2
echo -e "${BLUE}4. Verificando activityLogger_v2.js...${NC}"
if [ -f "/root/SGM/src/utils/activityLogger_v2.js" ]; then
    echo -e "${GREEN}✅ Logger V2 presente${NC}"
    
    # Verificar que está habilitado
    if grep -q "enabled: true" /root/SGM/src/utils/activityLogger_v2.js; then
        echo -e "${GREEN}✅ Logger V2 ACTIVADO${NC}"
    else
        echo -e "${YELLOW}⚠️  Logger V2 desactivado${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Logger V2 no encontrado${NC}"
fi
echo ""

# 5. Verificar componentes con logging habilitado
echo -e "${BLUE}5. Verificando componentes con logging activado...${NC}"
COMPONENTS=(
    "IngresosCard.jsx"
    "FiniquitosCard.jsx"
    "AusentismosCard.jsx"
    "MovimientosMesCard.jsx"
)

for component in "${COMPONENTS[@]}"; do
    file="/root/SGM/src/components/TarjetasCierreNomina/$component"
    if grep -q "createActivityLogger" "$file" && ! grep -q "// TODO" "$file" | head -1 | grep -q "createActivityLogger"; then
        if grep -q "import.*createActivityLogger.*activityLogger_v2" "$file"; then
            echo -e "${GREEN}✅ $component - Logger V2 activo${NC}"
        else
            echo -e "${YELLOW}⚠️  $component - Import incorrecto${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  $component - Logger comentado${NC}"
    fi
done
echo ""

# 6. Test manual de logging
echo -e "${BLUE}6. Prueba de logging manual...${NC}"
echo "Ejecutar en Django shell:"
echo ""
echo "docker compose exec django python manage.py shell"
echo ""
echo "Luego ejecutar:"
echo ""
cat << 'PYCODE'
from nomina.models import ActivityEvent

# Crear evento de prueba
event = ActivityEvent.log(
    cliente_id=1,
    user_id=1,
    action='test_manual',
    resource_type='system',
    details={'test': 'Activity Logging V2 funcionando'}
)
print(f"✅ Evento creado: {event.id}")
print(f"   Cliente: {event.cliente_id}")
print(f"   Action: {event.action}")
print(f"   Details: {event.details}")
PYCODE
echo ""

# 7. Verificar frontend compila
echo -e "${BLUE}7. Estado del frontend...${NC}"
if curl -s http://localhost:5174 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend accesible en http://localhost:5174${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend no responde (puede estar iniciando)${NC}"
fi
echo ""

echo "======================================"
echo -e "${GREEN}✅ Verificación completada${NC}"
echo ""
echo "📝 Próximos pasos para probar end-to-end:"
echo "   1. Acceder a un cierre de nómina"
echo "   2. Abrir tarjeta de Ingresos/Finiquitos/Ausentismos"
echo "   3. Verificar eventos en BD con:"
echo "      docker compose exec django python manage.py shell"
echo "      >>> from nomina.models import ActivityEvent"
echo "      >>> ActivityEvent.objects.filter(action='session_started').order_by('-timestamp')[:5]"
