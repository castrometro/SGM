// src/pages/CierreDetalle/areas/Payroll/components/hooks/useProcesamientoStatus.js
// Hook para monitorear el estado de procesamiento de archivos de payroll

import { useState, useEffect, useRef } from 'react';
import { verificarExistenciaArchivo } from '../../../../../../api/payroll';

const useProcesamientoStatus = (archivoId, cierreId, tipoArchivo) => {
  const [estado, setEstado] = useState({
    archivo: null,
    procesamiento: null,
    cargando: false,
    error: null,
    ultimaActualizacion: null
  });

  const intervalRef = useRef(null);
  const activoRef = useRef(true);

  // Función para consultar el estado
  const consultarEstado = async () => {
    if (!cierreId || !tipoArchivo || !activoRef.current) return;

    try {
      setEstado(prev => ({ ...prev, cargando: true, error: null }));
      
      // Agregar timeout de 10 segundos
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Timeout: La consulta tardó demasiado')), 10000)
      );
      
      const apiPromise = verificarExistenciaArchivo(cierreId, tipoArchivo);
      const respuesta = await Promise.race([apiPromise, timeoutPromise]);
      
      if (activoRef.current) {
        setEstado(prev => ({
          ...prev,
          archivo: respuesta.archivo,
          procesamiento: respuesta.procesamiento || null,
          cargando: false,
          ultimaActualizacion: new Date()
        }));

        // Determinar si necesitamos seguir monitoreando
        const necesitaMonitoreo = respuesta.archivo?.estado_procesamiento === 'parseando' || 
                                 respuesta.archivo?.estado_procesamiento === 'pendiente';
        
        if (necesitaMonitoreo && !intervalRef.current) {
          iniciarPolling();
        } else if (!necesitaMonitoreo && intervalRef.current) {
          detenerPolling();
        }
      }
    } catch (error) {
      console.error('Error consultando estado:', error);
      if (activoRef.current) {
        setEstado(prev => ({
          ...prev,
          cargando: false,
          error: error.message
        }));
      }
    }
  };

  // Iniciar polling cada 2 segundos (más responsive)
  const iniciarPolling = () => {
    if (intervalRef.current) return;
    intervalRef.current = setInterval(consultarEstado, 2000);
  };

  // Detener polling
  const detenerPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  // Consulta manual (para refrescar)
  const refrescar = async () => {
    await consultarEstado();
  };

  // Efecto para consulta inicial y limpieza
  useEffect(() => {
    if (cierreId && tipoArchivo) {
      consultarEstado();
    }

    return () => {
      activoRef.current = false;
      detenerPolling();
    };
  }, [cierreId, tipoArchivo]);

  // Efecto de limpieza al desmontar
  useEffect(() => {
    return () => {
      activoRef.current = false;
      detenerPolling();
    };
  }, []);

  // Estados derivados para facilitar uso
  const esProcesando = estado.archivo?.estado_procesamiento === 'parseando' || 
                      estado.archivo?.estado_procesamiento === 'pendiente';
  const esProcesado = estado.archivo?.estado_procesamiento === 'parsing_completo';
  const tieneError = estado.archivo?.estado_procesamiento === 'error';
  
  // Función para obtener mensaje de progreso
  const obtenerMensajeProgreso = () => {
    if (!estado.procesamiento) return null;
    
    const { fase_completada, empleados_extraidos, items_extraidos, valores_extraidos } = estado.procesamiento;
    
    switch (fase_completada) {
      case 'headers_extraidos':
        return `📋 Headers extraídos (${items_extraidos} conceptos detectados)`;
      case 'empleados_extraidos':
        return `👥 Empleados procesados (${empleados_extraidos} empleados, ${items_extraidos} conceptos)`;
      case 'valores_extraidos':
        return `✅ Procesamiento completado (${empleados_extraidos} empleados, ${valores_extraidos} valores)`;
      case 'iniciando':
        return '🚀 Iniciando procesamiento...';
      default:
        return '⏳ Procesando...';
    }
  };

  // Función para calcular porcentaje de progreso
  const calcularPorcentaje = () => {
    if (!estado.procesamiento) return 0;
    
    const { fase_completada } = estado.procesamiento;
    
    switch (fase_completada) {
      case 'headers_extraidos':
        return 33;
      case 'empleados_extraidos':
        return 66;
      case 'valores_extraidos':
        return 100;
      case 'iniciando':
        return 10;
      default:
        return 0;
    }
  };

  return {
    estado,
    consultarEstado,
    refrescar,
    iniciarPolling,
    detenerPolling,
    // Estados derivados
    esProcesando,
    esProcesado,
    tieneError,
    // Helpers para UI
    obtenerMensajeProgreso,
    calcularPorcentaje,
    // Estado de la consulta
    cargando: estado.cargando,
    error: estado.error,
    ultimaActualizacion: estado.ultimaActualizacion
  };
};

export default useProcesamientoStatus;
