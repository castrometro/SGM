// Etiquetas comunes para dashboards de nómina
export function prettifyEtiqueta(raw) {
  if (!raw) return '-';
  const lower = String(raw).toLowerCase();
  const mapa = {
    'licencia_medica': 'Licencia médica',
    'sin_justificar': 'Sin justificar',
    'vacaciones': 'Vacaciones',
    'cambio_datos': 'Cambio de datos',
    'cambio_contrato': 'Cambio de contrato',
    'cambio_sueldo': 'Cambio de sueldo',
    'reincorporacion': 'Reincorporación',
    'ingreso': 'Ingreso',
    'finiquito': 'Finiquito',
    'ausencia': 'Ausencia',
    'sin_subtipo': 'Sin subtipo'
  };
  if (mapa[lower]) return mapa[lower];
  return lower.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}
