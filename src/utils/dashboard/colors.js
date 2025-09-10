// Utilidades de colores y ordenamiento para dashboards de nómina

export const BASE_PALETTE = [
  '#0f766e', // dark teal
  '#0d9488', // teal
  '#0891b2', // cyan
  '#0ea5e9', // sky
  '#1d4ed8', // blue
  '#6366f1', // indigo
  '#7c3aed', // violet
  '#9333ea', // purple
  '#c026d3', // fuchsia
  '#db2777', // rose
  '#f59e0b', // amber
  '#fbbf24', // light amber
  '#fde047'  // yellow
];

// Genera un map clave->color ordenando desc por value
export function buildOrderedColorMap(data, keyField = 'key', valueField = 'value', palette = BASE_PALETTE) {
  const sorted = [...data].sort((a,b)=> (b[valueField]||0) - (a[valueField]||0));
  const map = {};
  sorted.forEach((d,i)=> { map[d[keyField] || d.name] = palette[i] || palette[palette.length-1]; });
  return map;
}
