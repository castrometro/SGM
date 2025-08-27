import { useState, useEffect } from "react";
import { obtenerCierrePorId } from "../../../api/contabilidad";
import { obtenerCliente } from "../../../api/clientes";
import { obtenerCierrePayrollDetalle } from "../../../api/payroll/clientes_payroll";

export const useCierreDetalle = (cierreId, tipoModulo = null) => {
  const [cierre, setCierre] = useState(null);
  const [cliente, setCliente] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!cierreId) return;
      
      try {
        setLoading(true);
        setError(null);
        
        // Detectar el tipo de cierre basado en la URL o parámetro
        const esPayroll = window.location.pathname.includes('/cierres-payroll/') || 
                         tipoModulo === 'payroll' || 
                         tipoModulo === 'nomina';
        
        let cierreObj;
        if (esPayroll) {
          // Para payroll, necesitamos extraer clienteId de la URL
          const pathSegments = window.location.pathname.split('/');
          const clientesIndex = pathSegments.indexOf('clientes');
          const clienteId = clientesIndex !== -1 ? pathSegments[clientesIndex + 1] : null;
          
          if (!clienteId) {
            throw new Error('No se pudo determinar el ID del cliente desde la URL');
          }
          
          // Obtener cierre real de payroll desde la API
          cierreObj = await obtenerCierrePayrollDetalle(clienteId, cierreId);
        } else {
          // Usar API de contabilidad
          cierreObj = await obtenerCierrePorId(cierreId);
        }
        
        setCierre(cierreObj);
        
        const clienteObj = await obtenerCliente(cierreObj.cliente);
        setCliente(clienteObj);
      } catch (err) {
        setError(err);
        console.error('Error al cargar datos del cierre:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [cierreId, tipoModulo]);

  const actualizarCierre = (nuevoCierre) => {
    setCierre(nuevoCierre);
  };

  return {
    cierre,
    cliente,
    loading,
    error,
    actualizarCierre
  };
};
