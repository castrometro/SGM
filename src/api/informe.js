// API: Construye un informe v2 reutilizando endpoints del Libro de Remuneraciones
// Evita depender de movimientos de personal: se basa en conceptos consolidados y el resumen existente.

import { obtenerDetalleNominaConsolidada, obtenerResumenNominaConsolidada } from './nomina';
import { construirInformeV2DesdeLibro } from '../utils/informeV2FromLibro';

export async function obtenerInformeV2DesdeLibro(cierreId) {
  const [detalle, resumen] = await Promise.all([
    obtenerDetalleNominaConsolidada(cierreId),
    obtenerResumenNominaConsolidada(cierreId),
  ]);
  const informe = construirInformeV2DesdeLibro(detalle, resumen);
  return { informe, detalle, resumen };
}

export default obtenerInformeV2DesdeLibro;
