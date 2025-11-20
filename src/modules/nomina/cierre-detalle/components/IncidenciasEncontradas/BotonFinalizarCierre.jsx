import React, { useState } from 'react';
import { CheckCircle, FileText, AlertTriangle, Loader2 } from 'lucide-react';
import { finalizarCierre } from '../../../api/nomina';

const BotonFinalizarCierre = ({ cierre, onCierreFinalizado }) => {
  const [procesando, setProcesando] = useState(false);
  const [error, setError] = useState('');
  const [confirmacion, setConfirmacion] = useState(false);

  const puedeFinalizarse = cierre?.estado === 'incidencias_resueltas' && 
                          (cierre?.estado_incidencias === 'resueltas' || 
                           cierre?.estado_incidencias === 'pendiente');

  const manejarFinalizacion = async () => {
    if (!confirmacion) {
      setConfirmacion(true);
      return;
    }

    setProcesando(true);
    setError('');

    try {
      const resultado = await finalizarCierre(cierre.id);
      
      if (resultado.success) {
        // Notificar al componente padre
        if (onCierreFinalizado) {
          onCierreFinalizado(resultado);
        }
        
        // Mostrar mensaje de éxito
        alert(`🎉 ${resultado.message}\n\n` + 
              `Estado: ${resultado.estado_final}\n` +
              `Empleados consolidados: ${resultado.resumen?.empleados_consolidados || 0}\n` +
              `Periodo: ${resultado.resumen?.periodo}\n` +
              `Cliente: ${resultado.resumen?.cliente}`);
        
        // Resetear confirmación
        setConfirmacion(false);
      } else {
        setError(resultado.message || 'Error al finalizar cierre');
      }
    } catch (err) {
      console.error('Error finalizando cierre:', err);
      setError(err.response?.data?.message || err.message || 'Error al finalizar cierre');
    } finally {
      setProcesando(false);
    }
  };

  const cancelarConfirmacion = () => {
    setConfirmacion(false);
    setError('');
  };

  if (!puedeFinalizarse) {
    return (
      <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
        <div className="flex items-center text-gray-400">
          <AlertTriangle className="h-5 w-5 mr-2" />
          <div>
            <p className="text-sm font-medium">Finalización no disponible</p>
            <p className="text-xs">
              Estado: {cierre?.estado} | Estado Incidencias: {cierre?.estado_incidencias} | Total: {cierre?.total_incidencias || 0}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-end">
      <div className="flex gap-2">
        {confirmacion ? (
          <>
            <button
              onClick={cancelarConfirmacion}
              className="px-3 py-1 text-xs bg-gray-600 hover:bg-gray-700 text-white rounded"
              disabled={procesando}
            >
              Cancelar
            </button>
            <button
              onClick={manejarFinalizacion}
              disabled={procesando}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-800 disabled:cursor-not-allowed text-white rounded-lg font-medium flex items-center"
            >
              {procesando ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Finalizando...
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Confirmar Finalización
                </>
              )}
            </button>
          </>
        ) : (
          <button
            onClick={manejarFinalizacion}
            disabled={procesando}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white rounded-lg font-medium flex items-center"
          >
            <FileText className="h-4 w-4 mr-2" />
            Generar Informes y Finalizar Cierre
          </button>
        )}
      </div>
      
      {error && (
        <div className="mt-3 p-3 bg-red-900/20 border border-red-700 rounded text-red-400 text-sm">
          <div className="flex items-center">
            <AlertTriangle className="h-4 w-4 mr-2 flex-shrink-0" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {confirmacion && !error && (
        <div className="mt-3 p-3 bg-yellow-900/20 border border-yellow-700 rounded">
          <div className="flex items-center text-yellow-400 text-sm">
            <AlertTriangle className="h-4 w-4 mr-2 flex-shrink-0" />
            <div>
              <p className="font-medium">¿Confirmar finalización del cierre?</p>
              <p className="text-xs text-yellow-300">
                Esta acción cambiará el estado a "finalizado" y generará los informes correspondientes.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BotonFinalizarCierre;
