import React, { useState } from 'react';

const Finiquitos = ({ activa, onArchivoSubido }) => {
  const [estado, setEstado] = useState({
    archivo: null,
    subiendo: false,
    progreso: 0,
    error: null
  });

  const subirArchivo = async (archivo) => {
    if (!activa) return;
    
    setEstado(prev => ({ ...prev, subiendo: true, progreso: 0, error: null }));
    
    try {
      // Simular progreso
      const intervalos = [25, 50, 75, 100];
      for (const progreso of intervalos) {
        await new Promise(resolve => setTimeout(resolve, 250));
        setEstado(prev => ({ ...prev, progreso }));
      }
      
      const nuevoArchivo = {
        id: Math.random().toString(36).substr(2, 9),
        nombre: archivo.name,
        tamaño: archivo.size,
        fechaSubida: new Date().toISOString()
      };
      
      setEstado({
        archivo: nuevoArchivo,
        subiendo: false,
        progreso: 100,
        error: null
      });
      
      onArchivoSubido && onArchivoSubido(nuevoArchivo);
      
    } catch (error) {
      setEstado(prev => ({
        ...prev,
        subiendo: false,
        error: 'Error al subir el archivo'
      }));
    }
  };

  const handleFileChange = (e) => {
    const archivo = e.target.files[0];
    if (archivo) {
      subirArchivo(archivo);
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="bg-gray-700 p-4 rounded-lg">
      <div className="flex justify-between items-center mb-3">
        <h5 className="font-medium text-white">🚪 Finiquitos</h5>
        {estado.archivo ? (
          <span className="text-green-400 text-sm">✅ Subido</span>
        ) : (
          <label className={`cursor-pointer px-3 py-1 rounded text-sm font-medium transition-colors ${
            !activa ? 'bg-gray-600 text-gray-400 cursor-not-allowed' :
            estado.subiendo ? 'bg-gray-600 text-gray-300 cursor-not-allowed' :
            'bg-blue-600 hover:bg-blue-700 text-white'
          }`}>
            {estado.subiendo ? 'Subiendo...' : 'Subir Archivo'}
            <input
              type="file"
              className="hidden"
              accept=".xlsx,.xls,.csv"
              onChange={handleFileChange}
              disabled={!activa || estado.subiendo || estado.archivo}
            />
          </label>
        )}
      </div>
      
      {estado.subiendo && (
        <div className="mb-3">
          <div className="w-full bg-gray-600 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${estado.progreso}%` }}
            />
          </div>
          <div className="text-xs text-gray-400 mt-1">{estado.progreso}%</div>
        </div>
      )}
      
      {estado.archivo && (
        <div className="text-xs text-gray-300 space-y-1">
          <div>📄 {estado.archivo.nombre}</div>
          <div>💾 {formatBytes(estado.archivo.tamaño)}</div>
          <div>📅 {new Date(estado.archivo.fechaSubida).toLocaleString('es-CL')}</div>
        </div>
      )}
      
      {estado.error && (
        <div className="text-red-400 text-xs mt-2">
          ⚠️ {estado.error}
        </div>
      )}
      
      {!activa && (
        <div className="text-gray-500 text-xs mt-2">
          Tarjeta inactiva - Subida deshabilitada
        </div>
      )}
    </div>
  );
};

export default Finiquitos;
