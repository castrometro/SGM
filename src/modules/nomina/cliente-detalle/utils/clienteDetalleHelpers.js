// src/modules/nomina/cliente-detalle/utils/clienteDetalleHelpers.js

/**
 * 🛠️ Utilidades para el módulo de Detalle de Cliente de Nómina
 */

/**
 * Normaliza una cadena removiendo acentos y convirtiendo a minúsculas
 */
const normalizar = (str) => {
  if (!str) return '';
  return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
};

/**
 * Valida que el usuario tenga acceso al área de Nómina
 */
export const validarAccesoNomina = (userData) => {
  if (!userData || !userData.areas) return false;
  
  return userData.areas.some(area => {
    const areaNombre = typeof area === 'string' ? area : area.nombre;
    return normalizar(areaNombre) === 'nomina';
  });
};

/**
 * Procesa los datos del resumen para la vista
 * Normaliza estructura esperada por los componentes KPI
 */
export const procesarDatosResumen = (kpisData) => {
  if (!kpisData?.tieneCierre || !kpisData?.raw?.informe) {
    return null;
  }

  const informe = kpisData.raw.informe;
  const libro = informe.datos_cierre?.libro_resumen_v2 || {};
  
  // Estructura normalizada para componentes
  return {
    ...libro,
    ultimo_cierre: kpisData.periodo,
    estado_cierre_actual: kpisData.estado_cierre,
    empleados_activos: libro?.cierre?.total_empleados ?? kpisData.kpis?.total_empleados ?? null,
    total_empleados: libro?.cierre?.total_empleados ?? kpisData.kpis?.total_empleados ?? null,
    kpis: kpisData.kpis,
    source: kpisData.source,
    periodo: kpisData.periodo,
  };
};

/**
 * Extrae información del último cierre
 */
export const extraerInfoUltimoCierre = (resumen) => {
  return {
    periodo: resumen?.ultimo_cierre || null,
    estado: resumen?.estado_cierre_actual || null,
    empleados: resumen?.total_empleados || resumen?.empleados_activos || 0
  };
};
