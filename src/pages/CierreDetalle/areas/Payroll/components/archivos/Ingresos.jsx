import React from 'react';
import useArchivoUploadReal from '../hooks/useArchivoUploadReal';

const Ingresos = ({ activa, cierreId, onArchivoSubido }) => {
  const {
    estado,
    subirArchivo,
    limpiarError
  } = useArchivoUploadReal('ingresos', cierreId);

  const handleFileChange = async (e) => {
    const archivo = e.target.files[0];
    if (archivo && activa) {
      const exito = await subirArchivo(archivo);
      if (exito && onArchivoSubido) {
        onArchivoSubido(estado.archivo);
      }
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
        <h5 className="font-medium text-white">💰 Ingresos</h5>
        
        <div className="flex items-center space-x-2">
          {estado.archivo && !estado.subiendo && (
            <span className="text-green-400 text-sm">✅ Subido</span>
          )}
          
          <label className={`cursor-pointer px-3 py-1 rounded text-sm font-medium transition-colors ${
            !activa ? 'bg-gray-600 text-gray-400 cursor-not-allowed' :
            estado.subiendo ? 'bg-gray-600 text-gray-300 cursor-not-allowed' :
            estado.archivo ? 'bg-orange-600 hover:bg-orange-700 text-white' :
            'bg-blue-600 hover:bg-blue-700 text-white'
          }`}>
            {estado.subiendo ? 'Subiendo...' : 
             estado.archivo ? 'Resubir Archivo' : 
             'Subir Archivo'}
            <input
              type="file"
              className="hidden"
              accept=".xlsx,.xls,.csv"
              onChange={handleFileChange}
              disabled={!activa || estado.subiendo}
            />
          </label>
        </div>
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
      
      {estado.verificando && (
        <div className="mb-3">
          <div className="flex items-center space-x-2 text-blue-400 text-xs">
            <div className="animate-spin w-3 h-3 border border-blue-400 border-t-transparent rounded-full"></div>
            <span>Verificando archivo existente...</span>
          </div>
        </div>
      )}
      
      {estado.archivo && (
        <div className="text-xs text-gray-300 space-y-1">
          <div>📄 {estado.archivo.nombre_original}</div>
          <div>💾 {formatBytes(estado.archivo.tamaño)}</div>
          <div>📅 {new Date(estado.archivo.fecha_subida).toLocaleString('es-CL')}</div>
        </div>
      )}
      
      {estado.error && (
        <div className="text-red-400 text-xs mt-2">
          <div className="flex justify-between items-start">
            <span>⚠️ {estado.error}</span>
            <button 
              onClick={limpiarError}
              className="text-red-300 hover:text-red-100 ml-2"
              title="Cerrar error"
            >
              ✕
            </button>
          </div>
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

export default Ingresos;
