import React, { useState } from 'react';
import { TIPOS_ARCHIVO_PAYROLL } from '../../../../../../api/payroll';
import useArchivoUploadReal from '../hooks/useArchivoUploadReal';

const LibroRemuneraciones = ({ activa, cierreId, onArchivoSubido }) => {
  const {
    estado,
    subirArchivo,
    validarArchivo,
    limpiarError,
    tieneArchivo,
    estaSubiendo,
    tieneError,
    estaVerificando
  } = useArchivoUploadReal(TIPOS_ARCHIVO_PAYROLL.LIBRO_REMUNERACIONES, cierreId);

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
          <h5 className="font-medium text-white">📊 Libro de Remuneraciones</h5>
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
        <h5 className="font-medium text-white">📊 Libro de Remuneraciones</h5>
        
        <div className="flex items-center space-x-2">
          {tieneArchivo && (
            <div className="flex items-center space-x-2">
              <span className="text-green-400 text-sm">✅ Subido</span>
              {estado.archivo?.estado && estado.archivo.estado !== 'subido' && (
                <span className={`text-xs px-2 py-1 rounded ${
                  estado.archivo.estado === 'procesado' ? 'bg-green-600 text-white' :
                  estado.archivo.estado === 'procesando' ? 'bg-yellow-600 text-white' :
                  estado.archivo.estado === 'error' ? 'bg-red-600 text-white' :
                  'bg-gray-600 text-gray-300'
                }`}>
                  {estado.archivo.estado}
                </span>
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

export default LibroRemuneraciones;
