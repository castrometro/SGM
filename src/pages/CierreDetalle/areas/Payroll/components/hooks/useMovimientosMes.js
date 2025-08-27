// src/pages/CierreDetalle/areas/Payroll/components/hooks/useMovimientosMes.js
// Hook específico para manejo de archivos de movimientos del mes

import { useState, useEffect } from 'react';
import useArchivoUploadReal from './useArchivoUploadReal';
import useProcesamientoStatus from './useProcesamientoStatus';

const useMovimientosMes = (cierreId, activa = true) => {
  const [estado, setEstado] = useState({
    subida: null,
    procesamiento: null,
    estadisticas: null,
    error: null
  });

  // Hook para subida de archivos
  const {
    estado: estadoSubida,
    subirArchivo,
    limpiarError: limpiarErrorSubida
  } = useArchivoUploadReal('movimientos_mes', cierreId);

  // Hook para monitoreo de procesamiento
  const {
    estado: estadoProcesamiento,
    refrescar: refrescarProcesamiento
  } = useProcesamientoStatus(
    estadoSubida.archivo?.id,
    cierreId,
    'movimientos_mes'
  );

  // Función para manejar subida de archivo
  const handleSubirArchivo = async (archivo) => {
    if (!activa) {
      setEstado(prev => ({ 
        ...prev, 
        error: 'La subida está deshabilitada en este momento' 
      }));
      return false;
    }

    try {
      limpiarError();
      const exito = await subirArchivo(archivo);
      
      if (exito) {
        // El procesamiento se iniciará automáticamente via signals
        await refrescarProcesamiento();
        return true;
      }
      return false;
    } catch (error) {
      setEstado(prev => ({
        ...prev,
        error: `Error subiendo archivo: ${error.message}`
      }));
      return false;
    }
  };

  // Función para obtener estadísticas del procesamiento
  const obtenerEstadisticas = () => {
    if (!estadoProcesamiento.archivo) return null;

    const archivo = estadoProcesamiento.archivo;
    const estadoProceso = archivo.estado_procesamiento;
    
    // Mapear estados a información user-friendly
    const estadosInfo = {
      'pendiente': {
        texto: 'Pendiente de procesamiento',
        color: 'text-yellow-400',
        icono: '⏳',
        descripcion: 'El archivo se subió correctamente y está en cola para procesamiento'
      },
      'parseando': {
        texto: 'Procesando datos...',
        color: 'text-blue-400',
        icono: '🔄',
        descripcion: 'Extrayendo y validando datos de altas/bajas y ausentismo'
      },
      'parsing_completo': {
        texto: 'Procesamiento completado',
        color: 'text-green-400',
        icono: '✅',
        descripcion: `${archivo.registros_procesados || 0} registros procesados exitosamente`
      },
      'error': {
        texto: 'Error en procesamiento',
        color: 'text-red-400',
        icono: '❌',
        descripcion: 'Ocurrió un error durante el procesamiento. Revisa el formato del archivo.'
      }
    };

    return {
      ...estadosInfo[estadoProceso] || estadosInfo['pendiente'],
      archivo,
      registrosProcesados: archivo.registros_procesados || 0,
      erroresDetectados: archivo.errores_detectados || 0,
      fechaSubida: archivo.fecha_subida,
      fechaProcesamiento: archivo.fecha_procesamiento
    };
  };

  // Función para limpiar errores
  const limpiarError = () => {
    setEstado(prev => ({ ...prev, error: null }));
    limpiarErrorSubida();
  };

  // Actualizar estado consolidado
  useEffect(() => {
    setEstado(prev => ({
      ...prev,
      subida: estadoSubida,
      procesamiento: estadoProcesamiento,
      estadisticas: obtenerEstadisticas()
    }));
  }, [estadoSubida, estadoProcesamiento]);

  // Propiedades derivadas para facilitar el uso
  const derivadas = {
    // Estados de subida
    estaSubiendo: estadoSubida.subiendo,
    archivoSubido: !!estadoSubida.archivo,
    
    // Estados de procesamiento
    estaProcesando: estadoProcesamiento.archivo?.estado_procesamiento === 'parseando',
    procesamientoCompleto: estadoProcesamiento.archivo?.estado_procesamiento === 'parsing_completo',
    procesamientoConError: estadoProcesamiento.archivo?.estado_procesamiento === 'error',
    
    // Información del archivo
    nombreArchivo: estadoSubida.archivo?.nombre_original,
    tamañoArchivo: estadoSubida.archivo?.tamaño,
    fechaSubida: estadoSubida.archivo?.fecha_subida,
    
    // Información de procesamiento
    registrosProcesados: estadoProcesamiento.archivo?.registros_procesados || 0,
    erroresDetectados: estadoProcesamiento.archivo?.errores_detectados || 0,
    
    // Error consolidado
    errorConsolidado: estado.error || estadoSubida.error || estadoProcesamiento.error
  };

  // Propiedades que dependen de derivadas (calculadas después)
  const propiedadesDependientes = {
    // Utilidades
    puedeSubir: activa && !derivadas.estaSubiendo && !derivadas.estaProcesando,
    mostrarRuedita: derivadas.estaSubiendo || derivadas.estaProcesando
  };

  return {
    // Estado consolidado
    estado: {
      ...estado,
      ...derivadas,
      ...propiedadesDependientes
    },
    
    // Acciones
    subirArchivo: handleSubirArchivo,
    limpiarError,
    refrescar: refrescarProcesamiento,
    
    // Información específica
    estadisticas: obtenerEstadisticas(),
    
    // Estados específicos (para compatibilidad)
    estadoSubida,
    estadoProcesamiento
  };
};

export default useMovimientosMes;
