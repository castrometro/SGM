/**
 * Formatea una fecha string de la base de datos a formato local
 * sin problemas de zona horaria.
 * 
 * Problema: cuando se hace new Date("2024-01-15"), JavaScript lo interpreta
 * como UTC medianoche, y al convertirlo a zona horaria local (Chile UTC-3/-4)
 * puede caer en el día anterior.
 * 
 * Solución: parsear la fecha como fecha local sin conversión de zona horaria.
 * 
 * @param {string|Date} fecha - Fecha en formato string YYYY-MM-DD o objeto Date
 * @returns {string} Fecha formateada en español chileno (dd/mm/yyyy) o '-' si no hay fecha
 */
export function formatearFechaLocal(fecha) {
  if (!fecha) return '-';
  
  // Si ya es un objeto Date, usarlo directamente
  if (fecha instanceof Date) {
    return fecha.toLocaleDateString('es-CL');
  }
  
  // Si es string, parsear como fecha local
  const fechaStr = String(fecha).trim();
  
  // Intentar parsear fecha en formato ISO (YYYY-MM-DD)
  const match = fechaStr.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (match) {
    const [, year, month, day] = match;
    // Crear fecha en zona horaria local (sin conversión UTC)
    const fechaLocal = new Date(
      parseInt(year, 10),
      parseInt(month, 10) - 1, // Los meses en JS son 0-indexed
      parseInt(day, 10)
    );
    return fechaLocal.toLocaleDateString('es-CL');
  }
  
  // Fallback: intentar parsear con Date (puede tener problemas de zona horaria)
  try {
    return new Date(fechaStr).toLocaleDateString('es-CL');
  } catch (e) {
    console.warn('Error parseando fecha:', fechaStr, e);
    return '-';
  }
}

/**
 * Convierte una fecha string a objeto Date local (sin ajuste de zona horaria)
 * @param {string} fechaStr - Fecha en formato YYYY-MM-DD
 * @returns {Date|null} Objeto Date en zona horaria local o null si no es válida
 */
export function parseFechaLocal(fechaStr) {
  if (!fechaStr || fechaStr === '-') return null;
  
  const match = String(fechaStr).trim().match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (match) {
    const [, year, month, day] = match;
    return new Date(
      parseInt(year, 10),
      parseInt(month, 10) - 1,
      parseInt(day, 10)
    );
  }
  
  return null;
}
