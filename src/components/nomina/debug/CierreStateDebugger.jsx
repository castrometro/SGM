import React, { useState, useEffect, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, PlayCircle, PauseCircle, RefreshCw, Trash2 } from 'lucide-react';
import { 
  obtenerCierreNominaPorId, 
  actualizarEstadoCierreNomina,
  consolidarDatosTalana 
} from '@/api/nomina';

const CierreStateDebugger = ({ cierreId }) => {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [currentState, setCurrentState] = useState(null);
  const [stateHistory, setStateHistory] = useState([]);
  const [logs, setLogs] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const intervalRef = useRef(null);
  const lastStateRef = useRef(null);

  // Función para añadir logs con timestamp
  const addLog = (message, type = 'info', data = null) => {
    const timestamp = new Date().toISOString();
    const logEntry = {
      id: Date.now(),
      timestamp,
      message,
      type, // 'info', 'warning', 'error', 'success'
      data
    };
    
    setLogs(prev => [logEntry, ...prev.slice(0, 49)]); // Mantener últimos 50 logs
    console.log(`🐛 [StateDebugger] ${message}`, data || '');
  };

  // Función para obtener el estado actual
  const fetchCurrentState = async () => {
    try {
      const cierre = await obtenerCierreNominaPorId(cierreId);
      const newState = {
        id: cierre.id,
        estado: cierre.estado,
        fecha_creacion: cierre.fecha_creacion,
        fecha_actualizacion: cierre.fecha_actualizacion,
        total_empleados: cierre.total_empleados || 0,
        errores_validacion: cierre.errores_validacion || 0,
        timestamp: new Date().toISOString()
      };

      // Detectar cambios de estado
      if (lastStateRef.current && lastStateRef.current.estado !== newState.estado) {
        addLog(
          `Estado cambió: ${lastStateRef.current.estado} → ${newState.estado}`,
          'warning',
          {
            anterior: lastStateRef.current,
            nuevo: newState
          }
        );
        
        // Añadir al historial
        setStateHistory(prev => [{
          id: Date.now(),
          timestamp: newState.timestamp,
          estado_anterior: lastStateRef.current.estado,
          estado_nuevo: newState.estado,
          duracion_anterior: lastStateRef.current.timestamp ? 
            new Date(newState.timestamp) - new Date(lastStateRef.current.timestamp) : 0
        }, ...prev.slice(0, 19)]); // Mantener últimos 20 cambios
      }

      setCurrentState(newState);
      lastStateRef.current = newState;
      
      if (isMonitoring) {
        addLog(`Estado actual: ${newState.estado}`, 'info');
      }

    } catch (error) {
      addLog(`Error obteniendo estado: ${error.message}`, 'error', error);
    }
  };

  // Iniciar/detener monitoreo
  const toggleMonitoring = () => {
    if (isMonitoring) {
      // Detener monitoreo
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setIsMonitoring(false);
      addLog('Monitoreo detenido', 'info');
    } else {
      // Iniciar monitoreo
      setIsMonitoring(true);
      addLog('Monitoreo iniciado - polling cada 5 segundos', 'success');
      
      // Primera consulta inmediata
      fetchCurrentState();
      
      // Configurar intervalo
      intervalRef.current = setInterval(fetchCurrentState, 5000);
    }
  };

  // Forzar actualización de estado
  const forceStateUpdate = async () => {
    setIsLoading(true);
    try {
      addLog('Forzando actualización de estado...', 'info');
      await actualizarEstadoCierreNomina(cierreId);
      await fetchCurrentState();
      addLog('Actualización de estado completada', 'success');
    } catch (error) {
      addLog(`Error forzando actualización: ${error.message}`, 'error', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Forzar consolidación
  const forceConsolidation = async () => {
    setIsLoading(true);
    try {
      addLog('Iniciando consolidación forzada...', 'info');
      await consolidarDatosTalana(cierreId);
      await fetchCurrentState();
      addLog('Consolidación completada', 'success');
    } catch (error) {
      addLog(`Error en consolidación: ${error.message}`, 'error', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Limpiar logs y historial
  const clearData = () => {
    setLogs([]);
    setStateHistory([]);
    addLog('Datos de debug limpiados', 'info');
  };

  // Obtener estado inicial
  useEffect(() => {
    fetchCurrentState();
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [cierreId]);

  // Formatear duración
  const formatDuration = (ms) => {
    if (!ms) return 'N/A';
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  // Obtener color del badge según tipo de log
  const getLogBadgeColor = (type) => {
    switch (type) {
      case 'error': return 'destructive';
      case 'warning': return 'secondary';
      case 'success': return 'default';
      default: return 'outline';
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            Debug Monitor - Estado del Cierre
          </span>
          <div className="flex items-center gap-2">
            <Badge variant={currentState ? "default" : "secondary"}>
              {currentState?.estado || 'Cargando...'}
            </Badge>
            {isMonitoring && (
              <Badge variant="outline" className="animate-pulse">
                Monitoreando
              </Badge>
            )}
          </div>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Controles */}
        <div className="flex flex-wrap gap-2">
          <Button
            onClick={toggleMonitoring}
            variant={isMonitoring ? "destructive" : "default"}
            size="sm"
          >
            {isMonitoring ? (
              <>
                <PauseCircle className="h-4 w-4 mr-1" />
                Detener Monitor
              </>
            ) : (
              <>
                <PlayCircle className="h-4 w-4 mr-1" />
                Iniciar Monitor
              </>
            )}
          </Button>
          
          <Button
            onClick={forceStateUpdate}
            disabled={isLoading}
            variant="outline"
            size="sm"
          >
            <RefreshCw className={`h-4 w-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
            Actualizar Estado
          </Button>
          
          <Button
            onClick={forceConsolidation}
            disabled={isLoading}
            variant="outline"
            size="sm"
          >
            <RefreshCw className={`h-4 w-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
            Forzar Consolidación
          </Button>
          
          <Button
            onClick={clearData}
            variant="outline"
            size="sm"
          >
            <Trash2 className="h-4 w-4 mr-1" />
            Limpiar
          </Button>
        </div>

        {/* Estado actual */}
        {currentState && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
            <div>
              <div className="text-sm font-medium text-gray-600">Estado</div>
              <div className="text-lg font-bold">{currentState.estado}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-600">Empleados</div>
              <div className="text-lg font-bold">{currentState.total_empleados}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-600">Errores</div>
              <div className="text-lg font-bold text-red-600">{currentState.errores_validacion}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-600">Última Actualización</div>
              <div className="text-sm">{new Date(currentState.timestamp).toLocaleTimeString()}</div>
            </div>
          </div>
        )}

        {/* Historial de cambios de estado */}
        {stateHistory.length > 0 && (
          <div>
            <h4 className="font-medium mb-2">Historial de Cambios de Estado</h4>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {stateHistory.map((change) => (
                <div key={change.id} className="flex items-center justify-between p-2 bg-yellow-50 rounded border-l-4 border-yellow-400">
                  <div>
                    <span className="font-medium">
                      {change.estado_anterior} → {change.estado_nuevo}
                    </span>
                    <div className="text-xs text-gray-600">
                      {new Date(change.timestamp).toLocaleString()}
                    </div>
                  </div>
                  <Badge variant="outline">
                    {formatDuration(change.duracion_anterior)}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Logs de debug */}
        <div>
          <h4 className="font-medium mb-2">Logs de Debug ({logs.length})</h4>
          <div className="space-y-1 max-h-60 overflow-y-auto border rounded p-2 bg-gray-50">
            {logs.length === 0 ? (
              <div className="text-sm text-gray-500 italic">No hay logs disponibles</div>
            ) : (
              logs.map((log) => (
                <div key={log.id} className="flex items-start gap-2 text-sm">
                  <Badge variant={getLogBadgeColor(log.type)} className="text-xs">
                    {log.type}
                  </Badge>
                  <div className="flex-1">
                    <div className="text-xs text-gray-500">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </div>
                    <div className="text-sm">{log.message}</div>
                    {log.data && (
                      <details className="text-xs text-gray-600 mt-1">
                        <summary className="cursor-pointer">Ver detalles</summary>
                        <pre className="mt-1 p-2 bg-gray-100 rounded overflow-x-auto">
                          {JSON.stringify(log.data, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default CierreStateDebugger;
