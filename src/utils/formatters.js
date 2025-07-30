// src/utils/formatters.js

// src/utils/formatters.js

/**
 * Formatea un valor numérico como moneda chilena con signo peso y sin decimales.
 * Ejemplo: 1500000 -> "$1.500.000"
 */
export const formatearMonedaChilena = (valor) => {
  if (valor === null || valor === undefined || valor === '' || isNaN(valor)) {
    return "$0";
  }
  
  try {
    // Si el valor ya es un string formateado, extraer el número
    let numeroLimpio = valor;
    if (typeof valor === 'string') {
      numeroLimpio = valor.replace(/[$.,]/g, '').replace(/[^0-9-]/g, '');
    }
    
    // Convertir a entero para eliminar decimales
    const valorEntero = parseInt(parseFloat(numeroLimpio));
    
    // Usar Intl.NumberFormat para formato chileno consistente
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(valorEntero);
  } catch (error) {
    return "$0";
  }
};

/**
 * Formatea un número con separadores de miles chilenos (puntos)
 * Ejemplo: 1500000 -> "1.500.000"
 */
export const formatearNumeroChileno = (valor) => {
  if (valor === null || valor === undefined || valor === '' || isNaN(valor)) {
    return "0";
  }
  
  try {
    const valorEntero = parseInt(parseFloat(valor));
    return valorEntero.toLocaleString('es-CL').replace(/,/g, '.');
  } catch (error) {
    return "0";
  }
};

/**
 * Formatea un porcentaje con un decimal
 * Ejemplo: 0.25 -> "25,0%"
 */
export const formatearPorcentaje = (valor, decimales = 1) => {
  if (valor === null || valor === undefined || valor === '' || isNaN(valor)) {
    return "0,0%";
  }
  
  try {
    const porcentaje = parseFloat(valor) * 100;
    return `${porcentaje.toFixed(decimales).replace('.', ',')}%`;
  } catch (error) {
    return "0,0%";
  }
};
