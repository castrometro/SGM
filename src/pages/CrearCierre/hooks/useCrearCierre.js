import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { obtenerCliente } from "../../../api/clientes";
import { 
  determinarAreaActiva, 
  getAreaConfig, 
  MESSAGES 
} from "../config/crearCierreConfig";

export const useCrearCierre = (propAreaActiva) => {
  const { clienteId } = useParams();
  const [cliente, setCliente] = useState(null);
  const [resumen, setResumen] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Determinar área activa
  const areaActiva = determinarAreaActiva(propAreaActiva);
  const areaConfig = getAreaConfig(areaActiva);

  useEffect(() => {
    const fetchCliente = async () => {
      try {
        setLoading(true);
        setError(null);

        // Cargar datos del cliente y resumen
        const [clienteData, resumenData] = await Promise.all([
          obtenerCliente(clienteId),
          areaConfig.apiFunction(clienteId)
        ]);

        setCliente(clienteData);
        setResumen(resumenData);
      } catch (err) {
        console.error("Error cargando datos del cliente:", err);
        setError(MESSAGES.error);
      } finally {
        setLoading(false);
      }
    };

    if (clienteId) {
      fetchCliente();
    }
  }, [clienteId, areaActiva, areaConfig.apiFunction]);

  return {
    clienteId,
    cliente,
    resumen,
    areaActiva,
    areaConfig,
    loading,
    error
  };
};
