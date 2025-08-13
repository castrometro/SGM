import { useState, useEffect } from "react";
import { subirArchivoGastos, consultarEstadoGastos, descargarResultadoGastos } from "../../../api/capturaGastos";
import { CAPTURA_CONFIG, UI_MESSAGES } from "../config/capturaConfig";

/**
 * Hook principal para manejar el estado y lógica de la captura masiva de gastos
 */
export const useCapturaGastos = () => {
  const [archivo, setArchivo] = useState(null);
  const [procesando, setProcesando] = useState(false);
  const [resultados, setResultados] = useState(null);
  const [taskId, setTaskId] = useState(null);
  const [error, setError] = useState(null);
  const [headersExcel, setHeadersExcel] = useState(null);
  const [mapeoCC, setMapeoCC] = useState({
    col10: '',
    col11: '',
    col12: ''
  });
  const [mostrarMapeoCC, setMostrarMapeoCC] = useState(false);

  // Polling para verificar estado de la tarea
  useEffect(() => {
    if (taskId && procesando) {
      const interval = setInterval(async () => {
        try {
          const estado = await consultarEstadoGastos(taskId);
          
          if (estado.estado === 'completado') {
            setResultados({
              total: estado.total_filas || 0,
              exitosos: estado.total_filas_procesadas || 0,
              errores: 0,
              grupos: estado.grupos || [],
              archivo_disponible: estado.archivo_excel_disponible
            });
            setProcesando(false);
            clearInterval(interval);
          } else if (estado.estado === 'error') {
            setError(`Error en el procesamiento: ${estado.error || 'Error desconocido'}`);
            setProcesando(false);
            clearInterval(interval);
          }
        } catch (error) {
          console.error('Error consultando estado:', error);
          setError(`Error consultando estado: ${error.message}`);
          setProcesando(false);
          clearInterval(interval);
        }
      }, 3000);

      return () => clearInterval(interval);
    }
  }, [taskId, procesando]);

  // Validar formato de centros de costos
  const validarFormatoCentrosCostos = (mapeo) => {
    const patron = CAPTURA_CONFIG.mapeoCC.formatPattern;
    const errores = [];
    
    Object.entries(mapeo).forEach(([key, valor]) => {
      if (valor.trim() !== '' && !patron.test(valor.trim())) {
        const numCol = key === 'col10' ? '10' : key === 'col11' ? '11' : '12';
        errores.push(`Columna ${numCol}: formato inválido (debe ser XX-XXX, ej: ${CAPTURA_CONFIG.mapeoCC.formatExample})`);
      }
    });
    
    return errores;
  };

  // Manejar selección de archivo
  const handleArchivoSeleccionado = async (event) => {
    const archivoSeleccionado = event.target.files[0];
    setArchivo(archivoSeleccionado);
    setError(null);
    setResultados(null);
    setMostrarMapeoCC(false);
    
    if (!archivoSeleccionado) return;
    
    // Leer headers del Excel para configurar mapeo de centros de costos
    try {
      const formData = new FormData();
      formData.append('archivo', archivoSeleccionado);
      
      const token = localStorage.getItem('token');
      const response = await fetch('http://172.17.11.18:8000/api/gastos/leer-headers/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setHeadersExcel(data.headers);
      setMostrarMapeoCC(true);
    } catch (error) {
      console.error('Error leyendo headers:', error);
      setError(`Error leyendo headers: ${error.message}`);
    }
  };

  // Procesar archivo
  const procesarArchivo = async () => {
    if (!archivo) {
      setError(UI_MESSAGES.errors.noFile);
      return;
    }
    
    // Validar que se hayan configurado los códigos de centro de costos
    const ccConfigured = Object.values(mapeoCC).some(cc => cc.trim() !== '');
    if (!ccConfigured && mostrarMapeoCC) {
      setError(UI_MESSAGES.errors.noCCConfig);
      return;
    }
    
    // Validar formato de códigos de centros de costos
    const erroresFormato = validarFormatoCentrosCostos(mapeoCC);
    if (erroresFormato.length > 0) {
      setError(`${UI_MESSAGES.errors.invalidFormat}\n${erroresFormato.join('\n')}`);
      return;
    }
    
    setProcesando(true);
    setError(null);
    
    try {
      const respuesta = await subirArchivoGastos(archivo, mapeoCC);
      setTaskId(respuesta.task_id);
      console.log('Archivo enviado, task_id:', respuesta.task_id);
    } catch (error) {
      console.error("Error procesando archivo:", error);
      setError(`${UI_MESSAGES.errors.processing} ${error.message}`);
      setProcesando(false);
    }
  };

  // Descargar archivo de resultados
  const descargarArchivo = async () => {
    if (!taskId) return;
    
    try {
      await descargarResultadoGastos(taskId);
    } catch (error) {
      console.error("Error descargando archivo:", error);
      setError(`${UI_MESSAGES.errors.download} ${error.message}`);
    }
  };

  // Descargar plantilla
  const descargarPlantilla = () => {
    // Simular descarga de plantilla Excel
    const link = document.createElement('a');
    link.href = '#';
    link.download = 'plantilla_rinde_gastos.xlsx';
    alert('Descargando plantilla Excel... (funcionalidad simulada)');
  };

  // Limpiar archivo seleccionado
  const limpiarArchivo = () => {
    setArchivo(null);
    setError(null);
    setResultados(null);
    setMostrarMapeoCC(false);
    setHeadersExcel(null);
    setMapeoCC({ col10: '', col11: '', col12: '' });
  };

  return {
    // Estado
    archivo,
    procesando,
    resultados,
    taskId,
    error,
    headersExcel,
    mapeoCC,
    mostrarMapeoCC,
    
    // Acciones
    handleArchivoSeleccionado,
    procesarArchivo,
    descargarArchivo,
    descargarPlantilla,
    limpiarArchivo,
    setMapeoCC,
    setError
  };
};
