import React from 'react';
import { TIPOS_ARCHIVO_PAYROLL } from '../../../../../../api/payroll';
import useArchivoUploadReal from '../hooks/useArchivoUploadReal';
import useProcesamientoStatus from '../hooks/useProcesamientoStatus';

const MovimientosDelMes = ({ activa, cierreId, onArchivoSubido }) => {
  const {
    estado,
    subirArchivo,
    validarArchivo,
    limpiarError,
    tieneArchivo,
    estaSubiendo,
    tieneError,
    estaVerificando
  } = useArchivoUploadReal(TIPOS_ARCHIVO_PAYROLL.MOVIMIENTOS_MES, cierreId);

  // Hook para monitorear procesamiento (solo si hay archivo)
  const {
    esProcesando,
    esProcesado,
    tieneError: tieneErrorProcesamiento,
    obtenerMensajeProgreso,
    calcularPorcentaje,
    refrescar,
    cargando: consultandoEstado
  } = useProcesamientoStatus(estado.archivo?.id, cierreId, TIPOS_ARCHIVO_PAYROLL.MOVIMIENTOS_MES);

  const handleFileChange = async (e) => {
    const archivo = e.target.files[0];
    if (!archivo) return;

    // Limpiar errores previos
    limpiarError();

    // Solo subir si la tarjeta está activa
    if (!activa) {
      console.warn('Intento de subir archivo en tarjeta inactiva');
      return;
    }

    try {
      // El hook se encarga de validar el archivo internamente
      const exito = await subirArchivo(archivo);
      if (exito && onArchivoSubido) {
        onArchivoSubido(estado.archivo);
      }
    } catch (error) {
      console.error('Error en handleFileChange:', error);
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatFecha = (fechaISO) => {
    if (!fechaISO) return 'Fecha no disponible';
    try {
      return new Date(fechaISO).toLocaleString('es-CL', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      return 'Fecha inválida';
    }
  };

  // Mostrar loading mientras verifica existencia
  if (estaVerificando) {
    return (
      <div className="bg-gray-700 p-4 rounded-lg">
        <div className="flex justify-between items-center mb-3">
          <h5 className="font-medium text-white">📈 Movimientos del Mes</h5>
          <span className="text-gray-400 text-sm">Verificando...</span>
        </div>
        <div className="text-gray-400 text-xs">
          🔍 Verificando si existe archivo...
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-700 p-4 rounded-lg">
      <div className="flex justify-between items-center mb-3">
        <h5 className="font-medium text-white">📈 Movimientos del Mes</h5>
        
        <div className="flex items-center space-x-2">
          {tieneArchivo && (
            <div className="flex items-center space-x-2">
              {/* Estado de subida */}
              <span className="text-green-400 text-sm">✅ Subido</span>
              
              {/* Estado de procesamiento */}
              {esProcesando && (
                <span className="text-blue-400 text-sm animate-pulse font-bold">🔄 Procesando</span>
              )}
              {esProcesado && (
                <span className="text-green-400 text-sm">🎉 Procesado</span>
              )}
              {tieneErrorProcesamiento && (
                <span className="text-red-400 text-sm animate-pulse">❌ Error</span>
              )}
              
              {/* Badge del estado de procesamiento */}
              {estado.archivo?.estado_procesamiento && estado.archivo.estado_procesamiento !== 'pendiente' && (
                <span className={`text-xs px-2 py-1 rounded font-medium ${
                  estado.archivo.estado_procesamiento === 'completado' ? 'bg-green-600 text-white' :
                  estado.archivo.estado_procesamiento === 'parseando' ? 'bg-blue-600 text-white animate-pulse' :
                  estado.archivo.estado_procesamiento === 'error' ? 'bg-red-600 text-white animate-pulse' :
                  'bg-gray-600 text-gray-300'
                }`}>
                  {estado.archivo.estado_procesamiento === 'completado' ? 'completado' : estado.archivo.estado_procesamiento}
                </span>
              )}

              {/* Ruedita de procesamiento automático */}
              {esProcesando && (
                <div className="flex items-center space-x-1 text-blue-400">
                  <div className="animate-spin">⚙️</div>
                  <span className="text-xs">Procesando...</span>
                </div>
              )}
            </div>
          )}
          
          <label className={`cursor-pointer px-3 py-1 rounded text-sm font-medium transition-colors ${
            !activa ? 'bg-gray-600 text-gray-400 cursor-not-allowed' :
            estaSubiendo ? 'bg-gray-600 text-gray-300 cursor-not-allowed' :
            tieneArchivo ? 'bg-orange-600 hover:bg-orange-700 text-white' :
            'bg-blue-600 hover:bg-blue-700 text-white'
          }`}>
            {estaSubiendo ? 'Subiendo...' : 
             tieneArchivo ? 'Resubir Archivo' : 
             'Subir Archivo'}
            <input
              type="file"
              className="hidden"
              accept=".xlsx,.xls"
              onChange={handleFileChange}
              disabled={!activa || estaSubiendo}
            />
          </label>
        </div>
      </div>
      
      {estaSubiendo && (
        <div className="mb-3">
          <div className="w-full bg-gray-600 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${estado.progreso}%` }}
            />
          </div>
          <div className="text-xs text-gray-400 mt-1">
            {estado.progreso}% - Subiendo archivo...
          </div>
        </div>
      )}
      
      {/* Barra de progreso de procesamiento automático */}
      {esProcesando && (
        <div className="mb-3 bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg border-2 border-blue-300 dark:border-blue-600 shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-3">
              <div className="animate-spin text-2xl">🔄</div>
              <div>
                <div className="text-sm font-bold text-blue-700 dark:text-blue-300">
                  🚀 Procesando automáticamente
                </div>
                <div className="text-xs text-blue-600 dark:text-blue-400">
                  El sistema está analizando movimientos del mes...
                </div>
              </div>
            </div>
            {consultandoEstado && (
              <div className="text-xs text-blue-500 animate-pulse">🔄 Actualizando...</div>
            )}
          </div>
          
          <div className="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-3 mb-2 shadow-inner">
            <div 
              className="bg-gradient-to-r from-blue-400 to-blue-600 h-3 rounded-full transition-all duration-700 ease-in-out shadow-sm"
              style={{ width: `${calcularPorcentaje()}%` }}
            />
          </div>
          
          <div className="flex justify-between items-center text-xs">
            <span className="text-blue-600 dark:text-blue-400 font-medium">
              {obtenerMensajeProgreso() || '⏳ Iniciando procesamiento...'}
            </span>
            <span className="text-blue-500 font-bold">
              {calcularPorcentaje()}%
            </span>
          </div>
        </div>
      )}

      {/* Notificación de completado */}
      {esProcesado && !estaSubiendo && (
        <div className="mb-3 bg-green-50 dark:bg-green-900/20 p-3 rounded-lg border border-green-200 dark:border-green-800">
          <div className="flex items-center space-x-2">
            <span className="text-green-500">✅</span>
            <span className="text-sm font-medium text-green-700 dark:text-green-300">
              Procesamiento completado exitosamente
            </span>
          </div>
        </div>
      )}

      {/* Notificación de error */}
      {tieneErrorProcesamiento && (
        <div className="mb-3 bg-red-50 dark:bg-red-900/20 p-3 rounded-lg border border-red-200 dark:border-red-800">
          <div className="flex items-center space-x-2">
            <span className="text-red-500">❌</span>
            <span className="text-sm font-medium text-red-700 dark:text-red-300">
              Error durante el procesamiento
            </span>
          </div>
        </div>
      )}
      
      {tieneArchivo && estado.archivo && (
        <div className="text-xs text-gray-300 space-y-1">
          <div>📄 {estado.archivo.nombre_original}</div>
          <div>💾 {formatBytes(estado.archivo.tamaño)}</div>
          <div>📅 {formatFecha(estado.archivo.fecha_subida)}</div>
          {estado.archivo.registros_procesados > 0 && (
            <div>📊 {estado.archivo.registros_procesados} registros procesados</div>
          )}
          {estado.archivo.errores_detectados > 0 && (
            <div className="text-yellow-400">
              ⚠️ {estado.archivo.errores_detectados} errores detectados
            </div>
          )}
          
          {/* Información de procesamiento detallada */}
          {esProcesado && obtenerMensajeProgreso() && (
            <div className="text-green-400">
              {obtenerMensajeProgreso()}
            </div>
          )}
        </div>
      )}
      
      {tieneError && (
        <div className="text-red-400 text-xs mt-2">
          ⚠️ {estado.error}
        </div>
      )}
      
      {!activa && !tieneArchivo && (
        <div className="text-gray-500 text-xs mt-2">
          Tarjeta inactiva - Subida deshabilitada
        </div>
      )}
      
      {!cierreId && (
        <div className="text-yellow-400 text-xs mt-2">
          ⚠️ ID de cierre no disponible
        </div>
      )}
    </div>
  );
};

export default MovimientosDelMes;
