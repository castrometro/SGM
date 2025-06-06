import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import PaginaClasificacion from "./PaginaClasificacion";
import { obtenerCierrePorId } from "../api/contabilidad";

const ClasificacionCierre = () => {
  const { cierreId } = useParams();
  const [clienteId, setClienteId] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!cierreId) return;
      try {
        const cierre = await obtenerCierrePorId(cierreId);
        setClienteId(cierre.cliente);
      } catch {
        setClienteId(null);
      }
    };
    fetchData();
  }, [cierreId]);

  if (!clienteId) {
    return (
      <div className="text-white text-center mt-8">Cargando clasificación...</div>
    );
  }

  return <PaginaClasificacion clienteId={clienteId} />;
};

export default ClasificacionCierre;
