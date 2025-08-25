-- ============================================
-- LIMPIEZA FINAL DE TABLAS DE NÓMINA
-- ============================================
-- Este script elimina todas las tablas relacionadas con el módulo de nómina
-- para preparar la base de datos para el nuevo sistema de payroll

-- Primero, deshabilitamos las verificaciones de claves foráneas temporalmente
SET foreign_key_checks = 0;

-- ============================================
-- TABLAS DE NÓMINA A ELIMINAR (≈6.5MB total)
-- ============================================

-- Tablas principales de nómina (más grandes)
DROP TABLE IF EXISTS nomina_conceptoconsolidado CASCADE;           -- 2240 kB
DROP TABLE IF EXISTS nomina_registroconceptoempleado CASCADE;      -- 2048 kB
DROP TABLE IF EXISTS nomina_registroconceptoempleadonovedades CASCADE; -- 872 kB

-- Tablas de cierre y control de nómina
DROP TABLE IF EXISTS nomina_incidenciacierre CASCADE;              -- 232 kB
DROP TABLE IF EXISTS nomina_nominaconsolidada CASCADE;             -- 232 kB
DROP TABLE IF EXISTS nomina_uploadlognomina CASCADE;               -- 224 kB
DROP TABLE IF EXISTS nomina_discrepanciacierre CASCADE;            -- 168 kB
DROP TABLE IF EXISTS nomina_tarjetaactivitylognomina CASCADE;      -- 144 kB
DROP TABLE IF EXISTS nomina_cierrenomina CASCADE;                  -- 144 kB

-- Tablas de movimientos y gestión de personal
DROP TABLE IF EXISTS nomina_movimientoausentismo CASCADE;          -- 120 kB
DROP TABLE IF EXISTS nomina_empleadocierrenovedades CASCADE;       -- 112 kB
DROP TABLE IF EXISTS nomina_conceptoremuneracion CASCADE;          -- 112 kB
DROP TABLE IF EXISTS nomina_empleadocierre CASCADE;                -- 112 kB
DROP TABLE IF EXISTS nomina_analistaincidencia CASCADE;            -- 104 kB
DROP TABLE IF EXISTS nomina_libroremuneracionesupload CASCADE;     -- 104 kB

-- Tablas de movimientos de personal
DROP TABLE IF EXISTS nomina_movimientopersonal CASCADE;            -- 96 kB
DROP TABLE IF EXISTS nomina_movimientovacaciones CASCADE;          -- 96 kB
DROP TABLE IF EXISTS nomina_analistafiniquito CASCADE;             -- 88 kB
DROP TABLE IF EXISTS nomina_analistaingreso CASCADE;               -- 88 kB
DROP TABLE IF EXISTS nomina_conceptoremuneracionnovedades CASCADE; -- 88 kB

-- Tablas de variaciones y movimientos menores
DROP TABLE IF EXISTS nomina_movimientoaltabaja CASCADE;            -- 80 kB
DROP TABLE IF EXISTS nomina_incidenciavariacionsalarial CASCADE;   -- 80 kB
DROP TABLE IF EXISTS nomina_movimientovariacioncontrato CASCADE;   -- 80 kB
DROP TABLE IF EXISTS nomina_archivonovedadesupload CASCADE;        -- 80 kB
DROP TABLE IF EXISTS nomina_archivoanalistaupload CASCADE;         -- 72 kB

-- Tablas de gestión y reportes
DROP TABLE IF EXISTS nomina_resolucionincidencia CASCADE;          -- 64 kB
DROP TABLE IF EXISTS nomina_reportenomina CASCADE;                 -- 64 kB
DROP TABLE IF EXISTS nomina_movimientosmesupload CASCADE;          -- 64 kB
DROP TABLE IF EXISTS nomina_checklistitem CASCADE;                 -- 48 kB
DROP TABLE IF EXISTS nomina_movimientovariacionsueldo CASCADE;     -- 40 kB
DROP TABLE IF EXISTS nomina_analisisdatoscierre CASCADE;           -- 32 kB

-- ============================================
-- VERIFICACIÓN DE LIMPIEZA
-- ============================================

-- Verificamos que no queden tablas de nómina
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name LIKE 'nomina_%'
ORDER BY table_name;

-- Restauramos las verificaciones de claves foráneas
SET foreign_key_checks = 1;

-- ============================================
-- RESUMEN DE LIMPIEZA
-- ============================================
-- Tablas eliminadas: ~30 tablas de nómina
-- Espacio liberado: ~6.5MB
-- Tablas restantes de contabilidad: ~18MB (preservadas)
-- Estado: Base de datos lista para nuevo sistema payroll

SELECT 'LIMPIEZA DE NÓMINA COMPLETADA - BASE DE DATOS PREPARADA PARA PAYROLL' as status;
