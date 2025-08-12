import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { obtenerUsuario } from "../../../api/auth";
import { determinarAreaActiva, MESSAGES } from "../config/historialCierresConfig";

export const useHistorialCierres = () => {
  const { clienteId } = useParams();
  const [areaActiva, setAreaActiva] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const cargarAreaActiva = async () => {
      try {
        setCargando(true);
        setError(null);
        
        const area = await determinarAreaActiva(obtenerUsuario);
        setAreaActiva(area);
      } catch (err) {
        console.error("Error cargando área activa:", err);
        setError(MESSAGES.error);
      } finally {
        setCargando(false);
      }
    };

    cargarAreaActiva();
  }, []);

  return {
    clienteId,
    areaActiva,
    cargando,
    error
  };
};
