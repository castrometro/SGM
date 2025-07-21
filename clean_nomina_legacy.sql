-- Script para eliminar completamente todas las tablas legacy de nómina
-- y permitir un inicio limpio con la nueva arquitectura

-- Eliminar tablas legacy específicas
DROP TABLE IF EXISTS nomina_empleadocierre CASCADE;
DROP TABLE IF EXISTS nomina_movimientonomina CASCADE;
DROP TABLE IF EXISTS nomina_movimientoausentismo CASCADE;
DROP TABLE IF EXISTS nomina_incidenciacierre CASCADE;
DROP TABLE IF EXISTS nomina_interaccionincidenciacierre CASCADE;

-- Eliminar tablas que pueden existir en ambos modelos (reset completo)
DROP TABLE IF EXISTS nomina_cierrenomina CASCADE;
DROP TABLE IF EXISTS nomina_mapeoconcepto CASCADE;
DROP TABLE IF EXISTS nomina_mapeonovedades CASCADE;
DROP TABLE IF EXISTS nomina_logarchivo CASCADE;

-- Eliminar tablas del nuevo modelo si existen (para reset completo)
DROP TABLE IF EXISTS nomina_empleadonumina CASCADE;
DROP TABLE IF EXISTS nomina_empleadoconcepto CASCADE;
DROP TABLE IF EXISTS nomina_ausentismo CASCADE;
DROP TABLE IF EXISTS nomina_incidencia CASCADE;
DROP TABLE IF EXISTS nomina_interaccionincidencia CASCADE;
DROP TABLE IF EXISTS nomina_kpinomina CASCADE;
DROP TABLE IF EXISTS nomina_empleadoofuscado CASCADE;
DROP TABLE IF EXISTS nomina_indiceempleadobusqueda CASCADE;
DROP TABLE IF EXISTS nomina_comparacionmensual CASCADE;
DROP TABLE IF EXISTS nomina_cacheconsultas CASCADE;

-- Limpiar registros de migraciones de nómina
DELETE FROM django_migrations WHERE app = 'nomina';

-- Mostrar mensaje de confirmación
SELECT 'Tablas legacy de nómina eliminadas. Listo para aplicar nueva arquitectura.' AS status;
