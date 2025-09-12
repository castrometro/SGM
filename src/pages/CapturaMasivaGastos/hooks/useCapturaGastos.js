import { useState, useEffect } from "react";
import { subirArchivoGastos, consultarEstadoGastos, descargarResultadoGastos, leerHeadersExcel } from "../../../api/capturaGastos";
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
  const [centrosCostoDetectados, setCentrosCostoDetectados] = useState({});
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

  // Validar formato de códigos CC
  const validarFormatoCC = (mapeo) => {
    const errores = [];
    const patron = CAPTURA_CONFIG.mapeoCC.formatPattern;
    
    Object.entries(mapeo).forEach(([key, valor]) => {
      if (valor.trim() !== '' && !patron.test(valor.trim())) {
        // Obtener el nombre real de la columna en lugar de posición fija
        let nombreColumna = 'Desconocida';
        if (key === 'col10' && centrosCostoDetectados.PyC) {
          nombreColumna = `${centrosCostoDetectados.PyC.nombre} (columna ${centrosCostoDetectados.PyC.posicion + 1})`;
        } else if (key === 'col11' && centrosCostoDetectados.PS) {
          nombreColumna = `${centrosCostoDetectados.PS.nombre} (columna ${centrosCostoDetectados.PS.posicion + 1})`;
        } else if (key === 'col12' && centrosCostoDetectados.CO) {
          nombreColumna = `${centrosCostoDetectados.CO.nombre} (columna ${centrosCostoDetectados.CO.posicion + 1})`;
        }
        
        errores.push(`${nombreColumna}: formato inválido (debe ser XX-XXX, ej: ${CAPTURA_CONFIG.mapeoCC.formatExample})`);
      }
    });
    
    return errores;
  };  // Manejar selección de archivo
  const handleArchivoSeleccionado = async (event) => {
    const archivoSeleccionado = event.target.files[0];
    setArchivo(archivoSeleccionado);
    setError(null);
    setResultados(null);
    setMostrarMapeoCC(false);
    
    if (!archivoSeleccionado) return;
    
    // Leer headers del Excel para configurar mapeo de centros de costos
    try {
      const data = await leerHeadersExcel(archivoSeleccionado);
      console.log('📡 Respuesta del API leer-headers:', data);

      // Backend devuelve { headers: [], centros_costos_detectados: { col10: 'PyC', ... } }
      // Compatibilidad: algunos backups usaban 'centros_costo'
      const ccDetectadosRaw = data.centros_costos_detectados || data.centros_costo || {};

      // Transformar a estructura esperada por el frontend: { PyC: {nombre, posicion}, PS: {...}, CO: {...} }
      const transformarCC = (ccMap) => {
        const resultado = {};
        Object.entries(ccMap).forEach(([colKey, headerName]) => {
          const idx = parseInt(String(colKey).replace('col', ''), 10);
          const lower = String(headerName || '').toLowerCase();
          const tokens = lower.split(/[^a-z0-9]+/).filter(Boolean);
          const tokenSet = new Set(tokens);

          const esPyC = tokenSet.has('pyc');
          const esPsEb = tokenSet.has('ps') || tokenSet.has('eb') || lower.includes('ps/eb');
          const esCO = tokenSet.has('co');

          if (esPyC) {
            resultado.PyC = { nombre: headerName, posicion: idx };
          } else if (esPsEb) {
            resultado.PS = { nombre: headerName, posicion: idx };
          } else if (esCO) {
            resultado.CO = { nombre: headerName, posicion: idx };
          }
        });
        return resultado;
      };

      setHeadersExcel(data.headers);
      setCentrosCostoDetectados(transformarCC(ccDetectadosRaw));
      setMostrarMapeoCC(true);
      console.log('✅ Headers y centros de costo establecidos');
    } catch (error) {
      console.error('Error leyendo headers:', error);
      setError(`Error leyendo headers: ${error.message}`);
    }
  };

  // Procesar archivo
  const procesarArchivo = async () => {
    console.log('🚀 procesarArchivo llamado');
    console.log('📁 archivo:', archivo);
    console.log('🗺️ mapeoCC:', mapeoCC);
    console.log('👀 mostrarMapeoCC:', mostrarMapeoCC);
    
    if (!archivo) {
      console.log('❌ Sin archivo');
      setError(UI_MESSAGES.errors.noFile);
      return;
    }
    
    // Validar que se hayan configurado los códigos de centro de costos
    const ccConfigured = Object.values(mapeoCC).some(cc => cc.trim() !== '');
    console.log('🔧 ccConfigured:', ccConfigured);
    console.log('🔧 mapeoCC values:', Object.values(mapeoCC));
    console.log('🔧 centrosCostoDetectados tiene datos:', Object.keys(centrosCostoDetectados).length > 0);
    
    // Solo validar si realmente hay centros de costo detectados en el archivo
    const hayCC = Object.keys(centrosCostoDetectados).length > 0;
    console.log('🔧 hayCC:', hayCC);
    
    if (!ccConfigured && mostrarMapeoCC && hayCC) {
      console.log('❌ Sin configuración de CC');
      setError(UI_MESSAGES.errors.noCCConfig);
      return;
    }
    
    // Validar formato de códigos de centros de costos
    const erroresFormato = validarFormatoCC(mapeoCC);
    console.log('✅ erroresFormato:', erroresFormato);
    
    if (erroresFormato.length > 0) {
      console.log('❌ Errores de formato:', erroresFormato);
      setError(`${UI_MESSAGES.errors.invalidFormat}\n${erroresFormato.join('\n')}`);
      return;
    }
    
    console.log('📤 Iniciando procesamiento...');
    setProcesando(true);
    setError(null);
    
    try {
      const respuesta = await subirArchivoGastos(archivo, mapeoCC);
      setTaskId(respuesta.task_id);
      console.log('✅ Archivo enviado, task_id:', respuesta.task_id);
    } catch (error) {
      console.error("❌ Error procesando archivo:", error);
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
    centrosCostoDetectados,
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
