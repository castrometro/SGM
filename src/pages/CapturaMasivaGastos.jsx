import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { 
  Receipt, 
  Upload, 
  FileSpreadsheet, 
  Download, 
  ArrowLeft, 
  AlertCircle,
  CheckCircle,
  Info,
  X,
  Clock,
  Settings,
  MapPin
} from "lucide-react";
import { subirArchivoGastos, consultarEstadoGastos, descargarResultadoGastos } from "../api/capturaGastos";

const CapturaMasivaGastos = () => {
  const navigate = useNavigate();
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
            setError(estado.error || 'Error desconocido en el procesamiento');
            setProcesando(false);
            clearInterval(interval);
          }
        } catch (err) {
          console.error('Error consultando estado:', err);
          setError(`Error consultando estado: ${err.message}`);
          setProcesando(false);
          clearInterval(interval);
        }
      }, 2000); // Consultar cada 2 segundos

      return () => clearInterval(interval);
    }
  }, [taskId, procesando]);

  const handleArchivoSeleccionado = (e) => {
    const file = e.target.files[0];
    if (file) {
      setArchivo(file);
      setResultados(null);
      setError(null);
      setTaskId(null);
      setMostrarMapeoCC(false);
      // Leer headers del Excel
      leerHeadersExcel(file);
    }
  };

  const leerHeadersExcel = async (file) => {
    try {
      // Crear FormData para enviar al backend
      const formData = new FormData();
      formData.append('archivo', file);
      
      // Solicitar headers al backend
      const response = await fetch('http://172.17.11.18:8000/api/gastos/leer-headers/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Error leyendo headers del Excel');
      }
      
      const data = await response.json();
      setHeadersExcel(data.headers);
      setMostrarMapeoCC(true);
    } catch (error) {
      console.error('Error leyendo headers:', error);
      setError(`Error leyendo headers: ${error.message}`);
    }
  };

  const validarFormatoCentrosCostos = (mapeo) => {
    const patron = /^\d{2}-\d{3}$/; // Formato: XX-XXX
    const errores = [];
    
    Object.entries(mapeo).forEach(([key, valor]) => {
      if (valor.trim() !== '' && !patron.test(valor.trim())) {
        const numCol = key === 'col10' ? '10' : key === 'col11' ? '11' : '12';
        errores.push(`Columna ${numCol}: formato inválido (debe ser XX-XXX, ej: 01-003)`);
      }
    });
    
    return errores;
  };

  const procesarArchivo = async () => {
    if (!archivo) return;
    
    // Validar que se hayan configurado los códigos de centro de costos
    const ccConfigured = Object.values(mapeoCC).some(cc => cc.trim() !== '');
    if (!ccConfigured && mostrarMapeoCC) {
      setError('Por favor, configure al menos un código de centro de costos');
      return;
    }
    
    // Validar formato de códigos de centros de costos
    const erroresFormato = validarFormatoCentrosCostos(mapeoCC);
    if (erroresFormato.length > 0) {
      setError(`Errores de formato:\n${erroresFormato.join('\n')}`);
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
      setError(`Error: ${error.message}`);
      setProcesando(false);
    }
  };

  const descargarArchivo = async () => {
    if (!taskId) return;
    
    try {
      await descargarResultadoGastos(taskId);
    } catch (error) {
      console.error("Error descargando archivo:", error);
      setError(`Error descargando archivo: ${error.message}`);
    }
  };

  const descargarPlantilla = () => {
    // Simular descarga de plantilla Excel
    const link = document.createElement('a');
    link.href = '#';
    link.download = 'plantilla_rinde_gastos.xlsx';
    alert('Descargando plantilla Excel... (funcionalidad simulada)');
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate(-1)}
                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
              >
                <ArrowLeft size={20} />
              </button>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-emerald-600 rounded-lg">
                  <Receipt size={24} />
                </div>
                <div>
                  <h1 className="text-2xl font-bold">Captura Masiva RindeGastos</h1>
                  <p className="text-gray-400">Carga múltiples gastos desde archivo Excel</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
        {/* Instrucciones */}
        <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-400 mt-0.5" />
            <div>
              <h3 className="font-semibold text-blue-400 mb-2">Instrucciones de Uso</h3>
              <ul className="text-gray-300 text-sm space-y-1">
                <li>• Descarga la plantilla Excel con el formato requerido</li>
                <li>• Completa los datos de gastos en las columnas correspondientes</li>
                <li>• Sube el archivo completado para procesamiento automático</li>
                <li>• Revisa los resultados y corrige cualquier error reportado</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Descargar Plantilla */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Download className="w-5 h-5" />
            Paso 1: Descargar Plantilla
          </h2>
          <p className="text-gray-400 mb-4">
            Descarga la plantilla Excel con el formato correcto para la carga masiva de gastos.
          </p>
          <button
            onClick={descargarPlantilla}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg flex items-center gap-2 transition-colors"
          >
            <FileSpreadsheet className="w-4 h-4" />
            Descargar Plantilla Excel
          </button>
        </div>

        {/* Subir Archivo */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Upload className="w-5 h-5" />
            Paso 2: Cargar Archivo
          </h2>
          
          <div className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center">
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={handleArchivoSeleccionado}
              className="hidden"
              id="archivo-excel"
            />
            <label 
              htmlFor="archivo-excel" 
              className="cursor-pointer flex flex-col items-center gap-4"
            >
              <div className="p-4 bg-emerald-600/20 rounded-full">
                <FileSpreadsheet className="w-8 h-8 text-emerald-400" />
              </div>
              <div>
                <p className="text-lg font-medium">
                  {archivo ? archivo.name : "Seleccionar archivo Excel"}
                </p>
                <p className="text-gray-400 text-sm">
                  Formatos soportados: .xlsx, .xls
                </p>
              </div>
            </label>
          </div>

          {archivo && (
            <div className="mt-4 flex items-center justify-between bg-gray-700 p-4 rounded-lg">
              <div className="flex items-center gap-3">
                <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
                <div>
                  <p className="font-medium">{archivo.name}</p>
                  <p className="text-gray-400 text-sm">
                    {(archivo.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              <button
                onClick={() => setArchivo(null)}
                className="text-red-400 hover:text-red-300 p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Mapeo de Centros de Costos */}
          {mostrarMapeoCC && headersExcel && (
            <div className="mt-6 bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-6">
              <div className="flex items-center gap-2 mb-4">
                <Settings className="w-5 h-5 text-yellow-400" />
                <h3 className="font-semibold text-yellow-400">Configurar Códigos de Centros de Costos</h3>
              </div>
              <p className="text-gray-300 text-sm mb-4">
                Por favor, asigne los códigos de centro de costos para las columnas detectadas:
              </p>
              
              <div className="space-y-4">
                {/* Columna 10 */}
                <div className="flex items-center gap-4">
                  <div className="w-32">
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Columna 10:
                    </label>
                    <p className="text-xs text-gray-400 truncate">
                      {headersExcel[9] || 'Sin nombre'}
                    </p>
                  </div>
                  <div className="flex-1">
                    <input
                      type="text"
                      placeholder="Código CC (ej: 01-003)"
                      value={mapeoCC.col10}
                      onChange={(e) => setMapeoCC(prev => ({...prev, col10: e.target.value}))}
                      className="w-full bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded-lg focus:outline-none focus:border-yellow-500"
                    />
                  </div>
                </div>

                {/* Columna 11 */}
                <div className="flex items-center gap-4">
                  <div className="w-32">
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Columna 11:
                    </label>
                    <p className="text-xs text-gray-400 truncate">
                      {headersExcel[10] || 'Sin nombre'}
                    </p>
                  </div>
                  <div className="flex-1">
                    <input
                      type="text"
                      placeholder="Código CC (ej: 02-004)"
                      value={mapeoCC.col11}
                      onChange={(e) => setMapeoCC(prev => ({...prev, col11: e.target.value}))}
                      className="w-full bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded-lg focus:outline-none focus:border-yellow-500"
                    />
                  </div>
                </div>

                {/* Columna 12 */}
                <div className="flex items-center gap-4">
                  <div className="w-32">
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Columna 12:
                    </label>
                    <p className="text-xs text-gray-400 truncate">
                      {headersExcel[11] || 'Sin nombre'}
                    </p>
                  </div>
                  <div className="flex-1">
                    <input
                      type="text"
                      placeholder="Código CC (ej: 03-005)"
                      value={mapeoCC.col12}
                      onChange={(e) => setMapeoCC(prev => ({...prev, col12: e.target.value}))}
                      className="w-full bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded-lg focus:outline-none focus:border-yellow-500"
                    />
                  </div>
                </div>
              </div>

              <div className="mt-4 bg-blue-900/20 border border-blue-500/30 rounded-lg p-3">
                <div className="flex items-start gap-2">
                  <Info className="w-4 h-4 text-blue-400 mt-0.5" />
                  <div className="text-xs text-blue-300">
                    <p className="font-medium mb-1">Información importante:</p>
                    <ul className="space-y-1">
                      <li>• Use el formato XX-XXX para códigos de centro de costos (ej: 01-003)</li>
                      <li>• Deje vacío si la columna no corresponde a un centro de costos</li>
                      <li>• Los valores nulos, "-" o "0" en el Excel se consideran sin centro de costos</li>
                      <li>• Cualquier otro valor se considera como 1 centro de costos</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}

          {archivo && (
            <button
              onClick={procesarArchivo}
              disabled={procesando}
              className="mt-4 w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {procesando ? (
                <>
                  <Clock className="w-4 h-4 animate-spin" />
                  Procesando con Celery...
                </>
              ) : (
                "Procesar Archivo"
              )}
            </button>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle className="w-5 h-5 text-red-400" />
              <h3 className="font-semibold text-red-400">Error</h3>
            </div>
            <p className="text-gray-300 text-sm">{error}</p>
          </div>
        )}

        {/* Resultados */}
        {resultados && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <CheckCircle className="w-5 h-5" />
              Resultados del Procesamiento
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
                <p className="text-blue-400 text-sm">Total de Registros</p>
                <p className="text-2xl font-bold">{resultados.total}</p>
              </div>
              <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-4">
                <p className="text-green-400 text-sm">Procesados Exitosamente</p>
                <p className="text-2xl font-bold text-green-400">{resultados.exitosos}</p>
              </div>
              <div className="bg-purple-900/20 border border-purple-500/30 rounded-lg p-4">
                <p className="text-purple-400 text-sm">Grupos por Tipo Doc</p>
                <p className="text-2xl font-bold text-purple-400">{resultados.grupos?.length || 0}</p>
              </div>
            </div>

            {/* Grupos creados */}
            {resultados.grupos && resultados.grupos.length > 0 && (
              <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4 mb-4">
                <div className="flex items-center gap-2 mb-3">
                  <Info className="w-5 h-5 text-blue-400" />
                  <h3 className="font-semibold text-blue-400">Grupos Creados por Tipo de Documento</h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  {resultados.grupos.map((grupo, index) => (
                    <span key={index} className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm">
                      {grupo}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Botón de descarga */}
            {resultados.archivo_disponible && taskId && (
              <button
                onClick={descargarArchivo}
                className="w-full bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <Download className="w-4 h-4" />
                Descargar Excel Procesado
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default CapturaMasivaGastos;
