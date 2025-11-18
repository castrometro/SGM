// src/modules/contabilidad/cliente-detalle/utils/clienteDetalleHelpers.js

/**
 * 🛠️ Utilidades para el módulo de Detalle de Cliente de Contabilidad
 */

/**
 * Normaliza una cadena removiendo acentos y convirtiendo a minúsculas
 */
const normalizar = (str) => {
  if (!str) return '';
  return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
};

/**
 * Valida que el usuario tenga acceso al área de Contabilidad
 */
export const validarAccesoContabilidad = (userData) => {
  if (!userData || !userData.areas) return false;
  
  return userData.areas.some(area => {
    const areaNombre = typeof area === 'string' ? area : area.nombre;
    return normalizar(areaNombre) === 'contabilidad';
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
  const libro = informe.datos_cierre?.libro_mayor || {};
  
  // Estructura normalizada para componentes
  return {
    ...libro,
    ultimo_cierre: kpisData.periodo,
    estado_cierre_actual: kpisData.estado_cierre,
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
    total_movimientos: resumen?.kpis?.total_movimientos || 0
  };
};
