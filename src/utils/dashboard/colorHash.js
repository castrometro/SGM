// Generación de índice y clase de color determinista por empleado

const EMP_COLOR_CLASSES = [
  'border-l-teal-500',
  'border-l-emerald-500',
  'border-l-sky-500',
  'border-l-indigo-500',
  'border-l-fuchsia-500',
  'border-l-rose-500',
  'border-l-amber-500',
  'border-l-lime-500',
  'border-l-cyan-500',
  'border-l-orange-500'
];

export function colorIndexForEmpleado(empleado){
  if (!empleado) return -1;
  const key = String(empleado.id || empleado.rut || empleado.uuid || '');
  if (!key) return -1;
  let hash = 0;
  for (let i=0;i<key.length;i++) hash = (hash * 31 + key.charCodeAt(i)) & 0xffffffff;
  return Math.abs(hash) % EMP_COLOR_CLASSES.length;
}

export function colorClassForEmpleado(empleado){
  const idx = colorIndexForEmpleado(empleado);
  return idx === -1 ? 'border-l-4 border-l-gray-700' : 'border-l-4 ' + EMP_COLOR_CLASSES[idx];
}

export { EMP_COLOR_CLASSES };
