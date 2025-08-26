import React from 'react';
import ArchivoBase from './ArchivoBase';

/**
 * Componente especializado para archivos del Analista
 * Maneja archivos más pequeños con validaciones específicas
 */
const ArchivoAnalista = ({ tipo, titulo, cierre, onEstadoChange }) => {
  const configuracion = {
    formatosPermitidos: ['.xlsx', '.xls', '.csv'],
    tamaanoMaximo: 50 * 1024 * 1024, // 50MB para archivos del Analista
    validacionesEspeciales: [
      'headers_analista',
      'datos_empleados',
      'formatos_fecha'
    ]
  };

  // Títulos específicos para cada tipo de archivo del Analista
  const titulos = {
    ausentismos: 'Ausentismos',
    ingresos: 'Ingresos',
    finiquitos: 'Finiquitos',
    novedades: 'Novedades'
  };

  const tituloFinal = titulo || titulos[tipo] || tipo.charAt(0).toUpperCase() + tipo.slice(1);

  return (
    <ArchivoBase
      tipo={tipo}
      titulo={tituloFinal}
      cierre={cierre}
      onEstadoChange={onEstadoChange}
      configuracion={configuracion}
    />
  );
};

export default ArchivoAnalista;
