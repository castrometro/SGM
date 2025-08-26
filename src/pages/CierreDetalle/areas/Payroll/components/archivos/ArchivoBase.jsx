import React from 'react';
import useArchivoUpload from '../hooks/useArchivoUpload';

/**
 * Componente base para subida de archivos en el módulo payroll
 * @param {Object} props - Props del componente
 * @param {string} props.tipo - Tipo de archivo
 * @param {string} props.titulo - Título a mostrar
 * @param {Object} props.cierre - Objeto del cierre
 * @param {Function} props.onEstadoChange - Callback para cambios de estado
 * @param {Object} props.configuracion - Configuración específica del archivo
 */
const ArchivoBase = ({ 
  tipo, 
  titulo, 
  cierre, 
  onEstadoChange,
  configuracion = {}
}) => {
  const {
    formatosPermitidos = ['.xlsx', '.xls', '.csv'],
    tamaanoMaximo = 50 * 1024 * 1024,
    validacionesEspeciales = []
  } = configuracion;

  const {
    archivo,
    estado,
    error,
    progreso,
    abrirSelectorArchivos,
    eliminarArchivo,
    estaSubido,
    estaProcesando,
    tieneError
  } = useArchivoUpload({
    tipo,
    cierre,
    onEstadoChange,
    formatosPermitidos,
    tamaanoMaximo
  });

  // Obtener icono según estado
  const obtenerIcono = () => {
    if (estaProcesando) {
      return (
        <div className="w-5 h-5 flex items-center justify-center">
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      );
    }

    if (estaSubido) {
      return (
        <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
      );
    }

    if (tieneError) {
      return (
        <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
      );
    }

    return (
      <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
      </svg>
    );
  };

  // Obtener texto del botón
  const obtenerTextoBoton = () => {
    if (estaProcesando) {
      return estado === 'subiendo' ? 'Subiendo...' : 
             estado === 'eliminando' ? 'Eliminando...' : 'Procesando...';
    }
    
    if (estaSubido) {
      return 'Cambiar';
    }
    
    return 'Subir';
  };

  // Obtener clase CSS del botón
  const obtenerClaseBoton = () => {
    const baseClass = "text-xs px-2 py-1 rounded font-medium transition-colors";
    
    if (estaProcesando) {
      return `${baseClass} bg-gray-600 text-gray-400 cursor-not-allowed`;
    }
    
    if (tieneError) {
      return `${baseClass} bg-red-600 hover:bg-red-700 text-white`;
    }
    
    if (estaSubido) {
      return `${baseClass} bg-orange-600 hover:bg-orange-700 text-white`;
    }
    
    return `${baseClass} bg-blue-600 hover:bg-blue-700 text-white`;
  };

  // Manejar click del botón
  const manejarClickBoton = async () => {
    if (estaProcesando) return;

    try {
      if (estaSubido) {
        // Si ya está subido, eliminar primero
        await eliminarArchivo();
        // Luego abrir selector para nuevo archivo
        setTimeout(() => {
          abrirSelectorArchivos().catch(console.error);
        }, 100);
      } else {
        // Si no está subido, abrir selector directamente
        await abrirSelectorArchivos();
      }
    } catch (err) {
      console.error(`Error manejando archivo ${tipo}:`, err);
    }
  };

  // Obtener información del archivo
  const obtenerInfoArchivo = () => {
    if (!archivo) return null;

    const tamaanoMB = (archivo.tamaño / (1024 * 1024)).toFixed(2);
    return (
      <div className="text-xs text-gray-400 mt-1">
        {archivo.nombre_original} ({tamaanoMB} MB)
      </div>
    );
  };

  return (
    <div className={`bg-gray-700 p-3 rounded transition-all duration-200 ${
      tieneError ? 'border border-red-500' : 
      estaSubido ? 'border border-green-500' : 
      'border border-transparent'
    }`}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <span className="text-sm text-gray-300 font-medium">{titulo}</span>
          {obtenerInfoArchivo()}
          
          {/* Mostrar error si existe */}
          {tieneError && error && (
            <div className="text-xs text-red-400 mt-1">
              ⚠️ {error}
            </div>
          )}
          
          {/* Mostrar progreso si está subiendo */}
          {estaProcesando && progreso > 0 && (
            <div className="mt-2">
              <div className="w-full bg-gray-600 rounded-full h-1">
                <div 
                  className="bg-blue-500 h-1 rounded-full transition-all duration-300"
                  style={{ width: `${progreso}%` }}
                ></div>
              </div>
              <div className="text-xs text-gray-400 mt-1">{progreso}%</div>
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-2 ml-3">
          {obtenerIcono()}
          <button
            onClick={manejarClickBoton}
            disabled={estaProcesando}
            className={obtenerClaseBoton()}
            title={tieneError ? error : undefined}
          >
            {obtenerTextoBoton()}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ArchivoBase;
