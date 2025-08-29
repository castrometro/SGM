import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Hook estándar para polling con control avanzado
 * @param {Function} apiCall - Función de API a ejecutar
 * @param {number} interval - Intervalo en ms (default: 3000)
 * @param {boolean} shouldStop - Si debe parar el polling
 * @param {boolean} enabled - Si el polling está habilitado
 * @param {Array} dependencies - Dependencias adicionales para reiniciar polling
 */
const usePolling = (
  apiCall, 
  interval = 3000, 
  shouldStop = false, 
  enabled = true,
  dependencies = []
) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  
  const pollingRef = useRef(null);
  const isMountedRef = useRef(true);
  const attemptCountRef = useRef(0);

  // Función para ejecutar la llamada API
  const executeCall = useCallback(async () => {
    if (!apiCall || !isMountedRef.current) return;
    
    try {
      setLoading(true);
      setError(null);
      attemptCountRef.current++;
      
      console.log(`📡 [usePolling] Ejecutando llamada #${attemptCountRef.current}`);
      
      const result = await apiCall();
      
      if (isMountedRef.current) {
        setData(result);
        console.log(`✅ [usePolling] Llamada #${attemptCountRef.current} exitosa`);
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err);
        console.error(`❌ [usePolling] Error en llamada #${attemptCountRef.current}:`, err.message);
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, [apiCall]);

  // Función para iniciar polling
  const startPolling = useCallback(() => {
    if (pollingRef.current || !enabled || shouldStop) return;
    
    console.log(`🔄 [usePolling] Iniciando polling (intervalo: ${interval}ms)`);
    setIsPolling(true);
    attemptCountRef.current = 0;
    
    // Ejecutar inmediatamente
    executeCall();
    
    // Continuar con polling
    pollingRef.current = setInterval(() => {
      if (isMountedRef.current && !shouldStop) {
        executeCall();
      }
    }, interval);
  }, [executeCall, interval, enabled, shouldStop]);

  // Función para detener polling
  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      console.log(`🛑 [usePolling] Deteniendo polling`);
      clearInterval(pollingRef.current);
      pollingRef.current = null;
      setIsPolling(false);
    }
  }, []);

  // Función para ejecutar una vez sin polling
  const fetchOnce = useCallback(async () => {
    await executeCall();
  }, [executeCall]);

  // Efecto principal para controlar el polling
  useEffect(() => {
    if (shouldStop || !enabled) {
      stopPolling();
      return;
    }

    startPolling();

    return () => {
      stopPolling();
    };
  }, [startPolling, stopPolling, shouldStop, enabled, ...dependencies]);

  // Cleanup al desmontar
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  return {
    data,
    loading,
    error,
    isPolling,
    startPolling,
    stopPolling,
    fetchOnce,
    attemptCount: attemptCountRef.current
  };
};

export default usePolling;
