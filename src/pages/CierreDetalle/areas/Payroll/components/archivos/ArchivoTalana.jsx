import React from 'react';
import ArchivoBase from './ArchivoBase';

/**
 * Componente especializado para archivos de Talana
 * Maneja archivos de mayor tamaño y validaciones específicas
 */
const ArchivoTalana = ({ tipo, titulo, cierre, onEstadoChange }) => {
  const configuracion = {
    formatosPermitidos: ['.xlsx', '.xls'],
    tamaanoMaximo: 100 * 1024 * 1024, // 100MB para archivos Talana
    validacionesEspeciales: [
      'headers_talana',
      'estructura_nomina',
      'validacion_empleados'
    ]
  };

  // Títulos específicos para cada tipo de archivo Talana
  const titulos = {
    libro_remuneraciones: 'Libro de Remuneraciones',
    movimientos_mes: 'Movimientos del Mes'
  };

  const tituloFinal = titulo || titulos[tipo] || tipo;

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

export default ArchivoTalana;
