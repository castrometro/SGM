import React, { useState, useEffect, useRef } from "react";
import { FileText, Upload, Trash2, Eye, Play, Download } from "lucide-react";
import CardBase from "./CardBase";
import usePolling from "../../hooks/usePolling";
import { 
  obtenerEstadoLibroRemuneraciones,
  subirLibroRemuneraciones,
  procesarLibroRemuneraciones,
  eliminarLibroRemuneraciones
} from "../../../../api/nomina";

const LibroRemuneracionesCard_v2 = ({
  cierreId,
  enabled = false
}) => {
  const [libro, setLibro] = useState(null);
  const [subiendo, setSubiendo] = useState(false);
  const [error, setError] = useState(null);
  const [eliminando, setEliminando] = useState(false);
  
  const fileInputRef = useRef();

  // 🎯 DETERMINAR ESTADO ACTUAL
  const estadoActual = libro?.estado || 'pendiente';
  const deberiaHacerPolling = estadoActual === 'procesando' && enabled;

  // 🎯 POLLING ESTANDARIZADO
  const { 
    data: datosLibro, 
    loading: cargandoEstado, 
    error: errorPolling 
  } = usePolling(
    () => obtenerEstadoLibroRemuneraciones(cierreId),
    3000,
    !deberiaHacerPolling || !enabled,
    cierreId ? true : false,
    [cierreId]
  );

  // 🎯 ACTUALIZAR ESTADO LOCAL CUANDO LLEGAN DATOS
  useEffect(() => {
    if (datosLibro) {
      console.log('📊 [LibroCard_v2] Datos actualizados:', datosLibro);
      setLibro(datosLibro);
    }
  }, [datosLibro]);

  // 🎯 COMUNICAR CAMBIOS AL PADRE
  useEffect(() => {
    // Ya no necesitamos comunicar cambios a un padre
    // El polling del cierre principal detectará los cambios
    console.log('📊 [LibroCard_v2] Estado actual:', estadoActual);
  }, [estadoActual]);

  // 🎯 CARGAR ESTADO INICIAL
  useEffect(() => {
    if (cierreId && !libro && enabled) {
      const cargarEstadoInicial = async () => {
        try {
          const data = await obtenerEstadoLibroRemuneraciones(cierreId);
          setLibro(data);
        } catch (err) {
          console.error('❌ [LibroCard_v2] Error cargando estado inicial:', err);
          setError(err);
        }
      };
      cargarEstadoInicial();
    }
  }, [cierreId, libro, enabled]);

  // 🎯 MANEJAR SUBIDA DE ARCHIVO
  const handleSubirArchivo = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      setSubiendo(true);
      setError(null);
      
      console.log('📤 [LibroCard_v2] Subiendo archivo:', file.name);
      
      const formData = new FormData();
      formData.append('archivo', file);
      
      const resultado = await subirLibroRemuneraciones(cierreId, formData);
      setLibro(resultado);
      
      console.log('✅ [LibroCard_v2] Archivo subido exitosamente');
      
    } catch (err) {
      console.error('❌ [LibroCard_v2] Error subiendo archivo:', err);
      setError(err);
    } finally {
      setSubiendo(false);
      // Resetear input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // 🎯 MANEJAR PROCESAMIENTO
  const handleProcesar = async () => {
    try {
      console.log('⚙️ [LibroCard_v2] Iniciando procesamiento');
      
      await procesarLibroRemuneraciones(cierreId);
      
      // Actualizar estado a procesando
      setLibro(prev => ({ ...prev, estado: 'procesando' }));
      
      console.log('✅ [LibroCard_v2] Procesamiento iniciado');
      
    } catch (err) {
      console.error('❌ [LibroCard_v2] Error procesando:', err);
      setError(err);
    }
  };

  // 🎯 MANEJAR ELIMINACIÓN
  const handleEliminar = async () => {
    if (!confirm('¿Estás seguro de que quieres eliminar este archivo?')) return;

    try {
      setEliminando(true);
      console.log('🗑️ [LibroCard_v2] Eliminando archivo');
      
      await eliminarLibroRemuneraciones(cierreId);
      setLibro(null);
      
      console.log('✅ [LibroCard_v2] Archivo eliminado');
      
    } catch (err) {
      console.error('❌ [LibroCard_v2] Error eliminando:', err);
      setError(err);
    } finally {
      setEliminando(false);
    }
  };

  // 🎯 CONTENIDO SEGÚN ESTADO
  const renderContenido = () => {
    if (!libro || estadoActual === 'pendiente') {
      return (
        <div className="text-center py-6">
          <FileText className="mx-auto mb-3 text-gray-400" size={48} />
          <p className="text-gray-400 mb-4">No hay libro de remuneraciones subido</p>
          <p className="text-sm text-gray-500">
            Sube un archivo Excel (.xlsx) con el libro de remuneraciones del período.
          </p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg">
          <div className="flex items-center gap-3">
            <FileText className="text-blue-400" size={20} />
            <div>
              <p className="font-medium text-white">{libro.nombre_archivo}</p>
              <p className="text-sm text-gray-400">
                {libro.total_registros || 0} registros
              </p>
            </div>
          </div>
          
          {estadoActual === 'procesado' && (
            <div className="flex gap-2">
              <button
                className="p-2 text-blue-400 hover:bg-blue-600/20 rounded transition-colors"
                title="Ver detalles"
              >
                <Eye size={16} />
              </button>
              <button
                className="p-2 text-green-400 hover:bg-green-600/20 rounded transition-colors"
                title="Descargar"
              >
                <Download size={16} />
              </button>
            </div>
          )}
        </div>

        {estadoActual === 'subido' && (
          <div className="text-center">
            <p className="text-gray-400 mb-3">Archivo listo para procesar</p>
          </div>
        )}

        {estadoActual === 'procesando' && (
          <div className="text-center py-4">
            <div className="inline-flex items-center gap-2 text-yellow-400">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-400"></div>
              Procesando archivo...
            </div>
            <p className="text-sm text-gray-400 mt-2">
              Esto puede tomar varios minutos
            </p>
          </div>
        )}
      </div>
    );
  };

  // 🎯 ACCIONES SEGÚN ESTADO
  const renderAcciones = () => {
    if (!enabled) return null;

    return (
      <div className="flex gap-2">
        {(!libro || estadoActual === 'pendiente') && (
          <>
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls"
              onChange={handleSubirArchivo}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={subiendo}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors disabled:opacity-50"
            >
              <Upload size={16} />
              {subiendo ? 'Subiendo...' : 'Subir Archivo'}
            </button>
          </>
        )}

        {estadoActual === 'subido' && (
          <>
            <button
              onClick={handleProcesar}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded transition-colors"
            >
              <Play size={16} />
              Procesar
            </button>
            <button
              onClick={handleEliminar}
              disabled={eliminando}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded transition-colors disabled:opacity-50"
            >
              <Trash2 size={16} />
            </button>
          </>
        )}

        {(estadoActual === 'procesado' || estadoActual === 'procesando') && libro && (
          <button
            onClick={handleEliminar}
            disabled={eliminando || estadoActual === 'procesando'}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded transition-colors disabled:opacity-50"
          >
            <Trash2 size={16} />
          </button>
        )}
      </div>
    );
  };

  return (
    <CardBase
      title="Libro de Remuneraciones"
      estado={estadoActual}
      loading={subiendo || cargandoEstado || eliminando}
      error={error || errorPolling}
      disabled={!enabled}
      icon={FileText}
      actions={renderAcciones()}
    >
      {renderContenido()}
    </CardBase>
  );
};

export default LibroRemuneracionesCard_v2;
