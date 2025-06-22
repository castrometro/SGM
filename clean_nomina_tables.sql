-- Script para limpiar completamente las tablas de nómina
-- Se ejecuta en PostgreSQL para eliminar todas las tablas existentes

-- Eliminar tablas en orden de dependencias (de hijas a padres)

-- Tablas de auditoría
DROP TABLE IF EXISTS nomina_auditoriaaccion CASCADE;
DROP TABLE IF EXISTS nomina_logprocesamiento CASCADE;

-- Tablas Gold Layer
DROP TABLE IF EXISTS nomina_movimientocierrefinal CASCADE;
DROP TABLE IF EXISTS nomina_conceptocierrefinal CASCADE;
DROP TABLE IF EXISTS nomina_empleadocierrefinal CASCADE;
DROP TABLE IF EXISTS nomina_cierrenominafinal CASCADE;

-- Tablas Silver Layer
DROP TABLE IF EXISTS nomina_fixincidencia CASCADE;
DROP TABLE IF EXISTS nomina_comentarioincidencia CASCADE;
DROP TABLE IF EXISTS nomina_incidenciacierre CASCADE;

-- Tablas Bronze Layer
DROP TABLE IF EXISTS nomina_movimientoingesta CASCADE;
DROP TABLE IF EXISTS nomina_conceptoingesta CASCADE;
DROP TABLE IF EXISTS nomina_empleadoingesta CASCADE;
DROP TABLE IF EXISTS nomina_archivoingesta CASCADE;

-- Tablas de catálogos
DROP TABLE IF EXISTS nomina_reglavalidacioncierre CASCADE;
DROP TABLE IF EXISTS nomina_conceptoremuneracion CASCADE;

-- Tabla principal de control
DROP TABLE IF EXISTS nomina_cierrenomina CASCADE;

-- Eliminar tablas antiguas si existen (legacy)
DROP TABLE IF EXISTS nomina_empleado CASCADE;
DROP TABLE IF EXISTS nomina_concepto CASCADE;
DROP TABLE IF EXISTS nomina_movimiento CASCADE;
DROP TABLE IF EXISTS nomina_archivo CASCADE;
DROP TABLE IF EXISTS nomina_clasificacion CASCADE;
DROP TABLE IF EXISTS nomina_mapeoheader CASCADE;
DROP TABLE IF EXISTS nomina_tipoarchivo CASCADE;
DROP TABLE IF EXISTS nomina_tipodocumento CASCADE;
DROP TABLE IF EXISTS nomina_loggingproceso CASCADE;
DROP TABLE IF EXISTS nomina_loggingprocesamiento CASCADE;

-- Eliminar secuencias si existen
DROP SEQUENCE IF EXISTS nomina_cierrenomina_id_seq CASCADE;
DROP SEQUENCE IF EXISTS nomina_archivoingesta_id_seq CASCADE;
DROP SEQUENCE IF EXISTS nomina_empleadoingesta_id_seq CASCADE;
DROP SEQUENCE IF EXISTS nomina_conceptoingesta_id_seq CASCADE;
DROP SEQUENCE IF EXISTS nomina_movimientoingesta_id_seq CASCADE;
DROP SEQUENCE IF EXISTS nomina_incidenciacierre_id_seq CASCADE;
DROP SEQUENCE IF EXISTS nomina_comentarioincidencia_id_seq CASCADE;
DROP SEQUENCE IF EXISTS nomina_fixincidencia_id_seq CASCADE;
DROP SEQUENCE IF EXISTS nomina_cierrenominafinal_id_seq CASCADE;
DROP SEQUENCE IF EXISTS nomina_empleadocierrefinal_id_seq CASCADE;
DROP SEQUENCE IF EXISTS nomina_conceptocierrefinal_id_seq CASCADE;
DROP SEQUENCE IF EXISTS nomina_movimientocierrefinal_id_seq CASCADE;
DROP SEQUENCE IF EXISTS nomina_conceptoremuneracion_id_seq CASCADE;
DROP SEQUENCE IF EXISTS nomina_reglavalidacioncierre_id_seq CASCADE;
DROP SEQUENCE IF EXISTS nomina_logprocesamiento_id_seq CASCADE;
DROP SEQUENCE IF EXISTS nomina_auditoriaaccion_id_seq CASCADE;

-- Limpiar registros de migración para nomina
DELETE FROM django_migrations WHERE app = 'nomina';

-- Mensaje de confirmación
SELECT 'Tablas de nómina eliminadas correctamente. Ejecutar migrate nomina ahora.' as mensaje;
