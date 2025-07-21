#!/bin/bash

# Script para probar los endpoints de libro de remuneraciones

echo "📋 TESTING ENDPOINTS LIBRO DE REMUNERACIONES"
echo "============================================="

BASE_URL="http://localhost:8000"

# 1. Obtener token de autenticación
echo "🔐 1. Obteniendo token de autenticación..."
TOKEN=$(curl -s -X POST "$BASE_URL/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@bdo.cl", "password": "admin123"}' \
  | grep -o '"access":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ Error: No se pudo obtener el token de autenticación"
  exit 1
fi

echo "✅ Token obtenido: ${TOKEN:0:20}..."

# 2. Verificar que exista al menos un cierre
echo "📊 2. Verificando cierres disponibles..."
CIERRES=$(curl -s -X GET "$BASE_URL/api/nomina/cierres/" \
  -H "Authorization: Bearer $TOKEN")

echo "Cierres disponibles:"
echo "$CIERRES" | head -5

# Extraer el primer cierre_id (asumiendo formato JSON)
CIERRE_ID=$(echo "$CIERRES" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -z "$CIERRE_ID" ]; then
  echo "❌ Error: No se encontraron cierres disponibles"
  exit 1
fi

echo "✅ Usando cierre ID: $CIERRE_ID"

# 3. Probar endpoint de estado (antes de subir archivo)
echo "📈 3. Consultando estado inicial del libro..."
curl -X GET "$BASE_URL/api/nomina/libros-remuneraciones/estado/$CIERRE_ID/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq '.'

echo ""

# 4. Crear archivo de prueba temporal
echo "📄 4. Creando archivo Excel de prueba..."
cat > /tmp/test_libro.csv << 'EOF'
Año,Mes,Rut de la Empresa,Rut del Trabajador,Nombre,Apellido Paterno,Apellido Materno,Sueldo Base,Horas Extras,Descuento Salud
2025,7,12345678-9,11111111-1,Juan,Pérez,González,800000,50000,-80000
2025,7,12345678-9,22222222-2,María,López,Martínez,750000,30000,-75000
2025,7,12345678-9,33333333-3,Carlos,Rodríguez,Silva,900000,80000,-90000
EOF

echo "✅ Archivo de prueba creado: /tmp/test_libro.csv"

# 5. Probar endpoint de subida
echo "🚀 5. Probando subida de archivo..."
RESPONSE=$(curl -X POST "$BASE_URL/api/nomina/libros-remuneraciones/" \
  -H "Authorization: Bearer $TOKEN" \
  -F "cierre=$CIERRE_ID" \
  -F "archivo=@/tmp/test_libro.csv")

echo "Respuesta de subida:"
echo "$RESPONSE" | jq '.'

# 6. Esperar un poco y consultar estado
echo "⏱️  6. Esperando 5 segundos y consultando estado..."
sleep 5

curl -X GET "$BASE_URL/api/nomina/libros-remuneraciones/estado/$CIERRE_ID/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq '.'

echo ""
echo "🎉 Test completado!"

# Limpiar archivo temporal
rm -f /tmp/test_libro.csv
