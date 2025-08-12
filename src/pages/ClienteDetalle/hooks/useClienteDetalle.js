import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  obtenerCliente,
  obtenerServiciosCliente,
} from "../../../api/clientes";
import { obtenerUsuario } from "../../../api/auth";
import { 
  getAreaConfig, 
  determinarAreaActiva, 
  MESSAGES 
} from "../config/clienteDetalleConfig";

export const useClienteDetalle = () => {
  const { id } = useParams();
  const [cliente, setCliente] = useState(null);
  const [resumen, setResumen] = useState(null);
  const [servicios, setServicios] = useState([]);
  const [areaActiva, setAreaActiva] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDatos = async () => {
      try {
        setLoading(true);
        setError(null);

        // Cargar datos básicos
        const [clienteData, usuario] = await Promise.all([
          obtenerCliente(id),
          obtenerUsuario()
        ]);

        // Determinar área activa
        const area = determinarAreaActiva(usuario);
        setAreaActiva(area);

        // Obtener configuración del área
        const areaConfig = getAreaConfig(area);
        
        // Cargar resumen según el área (si tiene API configurada)
        let resumenData = null;
        if (areaConfig.apiFunction) {
          resumenData = await areaConfig.apiFunction(id);
        }

        // Cargar servicios
        const serviciosData = await obtenerServiciosCliente(id);

        // Actualizar estados
        setCliente(clienteData);
        setResumen(resumenData);
        setServicios(serviciosData);
      } catch (err) {
        console.error("Error cargando datos del cliente:", err);
        setError(MESSAGES.error);
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchDatos();
    }
  }, [id]);

  // Obtener configuración del área actual
  const areaConfig = getAreaConfig(areaActiva);

  return {
    // Datos
    cliente,
    resumen,
    servicios,
    areaActiva,
    areaConfig,
    
    // Estados
    loading,
    error,
    
    // Utilidades
    clienteId: cliente?.id
  };
};
