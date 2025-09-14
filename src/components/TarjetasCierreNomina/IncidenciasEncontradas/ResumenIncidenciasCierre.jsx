import React, { useState, useEffect } from 'react';
import { CheckCircle, Clock, AlertTriangle, Users, FileText, RefreshCw } from 'lucide-react';
import { obtenerIncidenciasCierre } from '../../../api/nomina';
import { calcularProgresoIncidencias, calcularContadoresEstados, ESTADOS_INCIDENCIA } from '../../../utils/incidenciaUtils';
import IncidenciasKPIs from './IncidenciasKPIs';

const ResumenIncidenciasCierre = ({ cierreId, onEstadoActualizado }) => {
  const [resumen, setResumen] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [ejecutandoAccion, setEjecutandoAccion] = useState(false);
  const [error, setError] = useState('');
  const [incidencias, setIncidencias] = useState([]);

  useEffect(() => {
    if (cierreId) {
      cargarResumen();
    }
  }, [cierreId]);

  const cargarResumen = async () => {
    setCargando(true);
    setError('');
    try {
      // Cargar tanto el estado del cierre como las incidencias detalladas
      const [estadoResponse, incidenciasData] = await Promise.all([
        fetch(`/api/nomina/cierres/${cierreId}/estado-incidencias/`),
        obtenerIncidenciasCierre(cierreId, { page_size: 1000 })
      ]);
      
      if (!estadoResponse.ok) throw new Error('Error cargando estado');
      
      const estadoData = await estadoResponse.json();
  const incidencias = Array.isArray(incidenciasData.results) ? incidenciasData.results : incidenciasData;
      
      // Calcular estados reales basados en resoluciones
      const estadosReales = calcularContadoresEstados(incidencias);
      const progresoReal = calcularProgresoIncidencias(incidencias);
      
      // Combinar datos del servidor con cálculos reales
      const resumenActualizado = {
        ...estadoData,
        progreso: progresoReal,
        estados: estadosReales,
        total_incidencias: incidencias.length
      };
      
      setResumen(resumenActualizado);
      setIncidencias(incidencias);
    } catch (err) {
      console.error('Error:', err);
      setError('Error cargando el resumen de incidencias');
    } finally {
      setCargando(false);
    }
  };

  const manejarAprobacionMasiva = async () => {
    if (!window.confirm('¿Está seguro de aprobar todas las incidencias pendientes? Esta acción no se puede deshacer.')) {
      return;
    }

    const comentario = prompt('Comentario para la aprobación masiva (opcional):') || 'Aprobación masiva por supervisor';

    setEjecutandoAccion(true);
    setError('');
    try {
      const response = await fetch(`/api/nomina/cierres/${cierreId}/marcar-todas-como-justificadas/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ comentario }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Error en aprobación masiva');
      }

      const resultado = await response.json();
      
      // Recargar resumen
      await cargarResumen();
      
      // Notificar al componente padre
      if (onEstadoActualizado) {
        onEstadoActualizado(resultado);
      }

      alert(`✅ ${resultado.incidencias_aprobadas} incidencias aprobadas exitosamente`);

    } catch (err) {
      console.error('Error:', err);
      setError(err.message);
    } finally {
      setEjecutandoAccion(false);
    }
  };

  const solicitarRecargaArchivos = async () => {
    const motivo = prompt('Indique el motivo para recargar archivos (requerido):');
    if (!motivo || motivo.trim() === '') {
      alert('Debe proporcionar un motivo para la recarga');
      return;
    }

    if (!window.confirm('¿Confirma que desea solicitar la recarga de archivos? Esto permitirá resubir archivos corregidos desde Talana.')) {
      return;
    }

    setEjecutandoAccion(true);
    setError('');
    try {
      const response = await fetch(`/api/nomina/cierres/${cierreId}/solicitar-recarga-archivos/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ motivo: motivo.trim() }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Error solicitando recarga');
      }

      const resultado = await response.json();
      
      // Recargar resumen
      await cargarResumen();
      
      if (onEstadoActualizado) {
        onEstadoActualizado(resultado);
      }

      alert(`✅ Solicitud registrada. El cierre ahora permite recargar archivos.\\n\\nInstrucciones:\\n${resultado.instrucciones.join('\\n')}`);

    } catch (err) {
      console.error('Error:', err);
      setError(err.message);
    } finally {
      setEjecutandoAccion(false);
    }
  };

  if (cargando) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-center">
          <RefreshCw className="w-6 h-6 animate-spin text-blue-500 mr-2" />
          <span className="text-gray-300">Cargando resumen...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-500 rounded-lg p-4">
        <div className="flex items-center text-red-400">
          <AlertTriangle className="w-5 h-5 mr-2" />
          {error}
        </div>
      </div>
    );
  }

  if (!resumen) return null;

  const { progreso, estados, prioridades, puede_finalizar } = resumen;

  return (
    <div className="bg-gray-800 rounded-lg p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white flex items-center">
          <FileText className="w-5 h-5 mr-2" />
          Resumen de Incidencias
        </h3>
        <button
          onClick={cargarResumen}
          disabled={cargando}
          className="text-gray-400 hover:text-white transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${cargando ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* KPIs de incidencias */}
      {Array.isArray(incidencias) && incidencias.length > 0 && (
        <div>
          <IncidenciasKPIs incidencias={incidencias} />
        </div>
      )}

      {/* Progreso general */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-700/50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400 text-sm">Aprobadas</span>
            <CheckCircle className="w-4 h-4 text-green-500" />
          </div>
          <div className="text-2xl font-bold text-green-400">{progreso.aprobadas}</div>
        </div>
        
        <div className="bg-gray-700/50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400 text-sm">Pendientes</span>
            <Clock className="w-4 h-4 text-yellow-500" />
          </div>
          <div className="text-2xl font-bold text-yellow-400">{progreso.pendientes}</div>
        </div>
        
        <div className="bg-gray-700/50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400 text-sm">Rechazadas</span>
            <AlertTriangle className="w-4 h-4 text-red-500" />
          </div>
          <div className="text-2xl font-bold text-red-400">{progreso.rechazadas}</div>
        </div>
      </div>

      {/* Barra de progreso */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm text-gray-400">
          <span>Progreso de resolución</span>
          <span>
            {resumen.total_incidencias > 0 
              ? Math.round((progreso.aprobadas / resumen.total_incidencias) * 100)
              : 0
            }%
          </span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div 
            className="bg-green-500 h-2 rounded-full transition-all duration-300"
            style={{ 
              width: resumen.total_incidencias > 0 
                ? `${(progreso.aprobadas / resumen.total_incidencias) * 100}%`
                : '0%'
            }}
          />
        </div>
      </div>

      {/* Distribución por prioridad */}
      {Object.keys(prioridades).length > 0 && (
        <div className="space-y-2">
          <h4 className="text-white font-medium">Por Prioridad</h4>
          <div className="flex space-x-4 text-sm">
            {prioridades.alta > 0 && (
              <span className="text-red-400">Alta: {prioridades.alta}</span>
            )}
            {prioridades.media > 0 && (
              <span className="text-yellow-400">Media: {prioridades.media}</span>
            )}
            {prioridades.baja > 0 && (
              <span className="text-green-400">Baja: {prioridades.baja}</span>
            )}
          </div>
        </div>
      )}

      {/* Acciones para supervisor */}
      <div className="border-t border-gray-700 pt-4 space-y-3">
        <h4 className="text-white font-medium flex items-center">
          <Users className="w-4 h-4 mr-2" />
          Acciones de Supervisor
        </h4>
        
        <div className="flex flex-col sm:flex-row gap-3">
          {estados[ESTADOS_INCIDENCIA.RESUELTA_ANALISTA] > 0 && (
            <button
              onClick={manejarAprobacionMasiva}
              disabled={ejecutandoAccion}
              className="flex items-center justify-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {ejecutandoAccion ? (
                <RefreshCw className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <CheckCircle className="w-4 h-4 mr-2" />
              )}
              Aprobar Todas ({estados[ESTADOS_INCIDENCIA.RESUELTA_ANALISTA]})
            </button>
          )}

          {progreso.rechazadas > 0 && (
            <button
              onClick={solicitarRecargaArchivos}
              disabled={ejecutandoAccion}
              className="flex items-center justify-center px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50 transition-colors"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Solicitar Recarga de Archivos
            </button>
          )}
        </div>

        <div className="text-xs text-gray-500 space-y-1">
          <p>• <strong>Aprobar Todas:</strong> Marca todas las justificaciones pendientes como aprobadas</p>
          <p>• <strong>Recarga de Archivos:</strong> Permite resubir archivos corregidos desde Talana</p>
        </div>
      </div>

      {/* Estado final */}
      {puede_finalizar && (
        <div className="bg-green-900/20 border border-green-500 rounded-lg p-4">
          <div className="flex items-center text-green-400">
            <CheckCircle className="w-5 h-5 mr-2" />
            <span className="font-medium">¡Todas las incidencias están resueltas!</span>
          </div>
          <p className="text-green-300 text-sm mt-1">
            El cierre puede proceder a la finalización.
          </p>
        </div>
      )}
    </div>
  );
};

export default ResumenIncidenciasCierre;
