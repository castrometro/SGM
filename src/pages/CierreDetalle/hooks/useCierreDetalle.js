import { useState, useEffect } from "react";
import { obtenerCierrePorId } from "../../../api/contabilidad";
import { obtenerCliente } from "../../../api/clientes";

export const useCierreDetalle = (cierreId) => {
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
        
        const cierreObj = await obtenerCierrePorId(cierreId);
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
  }, [cierreId]);

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
