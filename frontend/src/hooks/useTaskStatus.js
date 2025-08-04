// hooks/useTaskStatus.js
import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * 🚀 Hook React para monitorear estados de tareas Celery usando Flower
 * 
 * @param {string} taskId - ID de la tarea a monitorear
 * @param {number} cierreId - ID del cierre relacionado
 * @param {Object} options - Opciones de configuración
 * @returns {Object} Estado y funciones del hook
 */
export const useTaskStatus = (taskId, cierreId, options = {}) => {
  const {
    pollInterval = 2000,        // Intervalo de polling en ms
    maxRetries = 3,            // Máximo número de reintentos
    autoStop = true,           // Detener polling cuando termina
    onSuccess = null,          // Callback cuando termina exitosamente
    onError = null,            // Callback cuando falla
    onProgress = null,         // Callback en cada actualización
  } = options;

  // Estados
  const [taskData, setTaskData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);

  // Referencias para control
  const intervalRef = useRef(null);
  const mountedRef = useRef(true);

  // Función para consultar el estado
  const fetchTaskStatus = useCallback(async () => {
    if (!taskId || !cierreId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/nomina/cierres/${cierreId}/task-status-enhanced/${taskId}/`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (mountedRef.current) {
        setTaskData(data);
        setRetryCount(0);
        
        // Llamar callback de progreso
        if (onProgress) {
          onProgress(data);
        }

        // Manejar finalización
        if (data.is_finished) {
          if (autoStop) {
            stopPolling();
          }
          
          if (data.is_successful && onSuccess) {
            onSuccess(data);
          } else if (!data.is_successful && onError) {
            onError(data);
          }
        }
      }

    } catch (err) {
      console.error('Error fetching task status:', err);
      
      if (mountedRef.current) {
        setError(err.message);
        
        // Reintentar si no se ha alcanzado el máximo
        if (retryCount < maxRetries) {
          setRetryCount(prev => prev + 1);
          setTimeout(() => {
            if (mountedRef.current) {
              fetchTaskStatus();
            }
          }, pollInterval * 2); // Esperar más tiempo en reintentos
        } else {
          stopPolling();
          if (onError) {
            onError({ error: err.message, task_id: taskId });
          }
        }
      }
    } finally {
      if (mountedRef.current) {
        setIsLoading(false);
      }
    }
  }, [taskId, cierreId, retryCount, maxRetries, pollInterval, onSuccess, onError, onProgress, autoStop]);

  // Iniciar polling
  const startPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    // Ejecutar inmediatamente
    fetchTaskStatus();

    // Luego cada intervalo
    intervalRef.current = setInterval(fetchTaskStatus, pollInterval);
  }, [fetchTaskStatus, pollInterval]);

  // Detener polling
  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // Cancelar tarea
  const cancelTask = useCallback(async () => {
    if (!taskId || !cierreId) return;

    try {
      const response = await fetch(
        `/api/nomina/cierres/${cierreId}/cancel-task/${taskId}/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

      const data = await response.json();
      
      if (data.success) {
        stopPolling();
        setTaskData(prev => prev ? { ...prev, status: 'cancelada', message: 'Tarea cancelada' } : null);
      }
      
      return data;
    } catch (err) {
      console.error('Error cancelling task:', err);
      throw err;
    }
  }, [taskId, cierreId, stopPolling]);

  // Efecto para iniciar/detener polling
  useEffect(() => {
    if (taskId && cierreId) {
      startPolling();
    }

    return () => {
      stopPolling();
    };
  }, [taskId, cierreId, startPolling, stopPolling]);

  // Cleanup al desmontar
  useEffect(() => {
    return () => {
      mountedRef.current = false;
      stopPolling();
    };
  }, [stopPolling]);

  return {
    // Estados
    taskData,
    isLoading,
    error,
    retryCount,
    
    // Estados derivados
    isActive: taskData && !taskData.is_finished,
    isFinished: taskData?.is_finished || false,
    isSuccessful: taskData?.is_successful || false,
    progress: taskData?.progress_percentage || 0,
    message: taskData?.message || 'Inicializando...',
    status: taskData?.status || 'pendiente',
    
    // Funciones de control
    startPolling,
    stopPolling,
    cancelTask,
    refetch: fetchTaskStatus,
  };
};

export default useTaskStatus;
