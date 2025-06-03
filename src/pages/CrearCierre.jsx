import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import ClienteInfoCard from "../components/InfoCards/ClienteInfoCard";
import CrearCierreCard from "../components/CrearCierre/CrearCierreCard";
import { obtenerCliente } from "../api/clientes";
import { obtenerResumenContable } from "../api/contabilidad";
import { obtenerResumenNomina } from "../api/nomina"; // <-- debes tener este endpoint

const CrearCierre = ({ areaActiva: propAreaActiva }) => {
  const { clienteId } = useParams();
  const areaActiva = propAreaActiva || localStorage.getItem("area_activa") || "Contabilidad";
  const [cliente, setCliente] = useState(null);
  const [resumen, setResumen] = useState(null);

  useEffect(() => {
    const fetchCliente = async () => {
      try {
        const c = await obtenerCliente(clienteId);
        let r;
        if (areaActiva === "Contabilidad") {
          r = await obtenerResumenContable(clienteId);
        } else if (areaActiva === "Nomina") {
          r = await obtenerResumenNomina(clienteId);
        }
        setCliente(c);
        setResumen(r);
      } catch (err) {
        // Puedes mostrar error si quieres
      }
    };
    fetchCliente();
  }, [clienteId, areaActiva]);

  if (!cliente || !resumen) {
    return <div className="text-white text-center mt-8">Cargando datos del cliente...</div>;
  }

  return (
    <div className="max-w-2xl mx-auto mt-8 space-y-8">
      <ClienteInfoCard cliente={cliente} resumen={resumen} />
      <CrearCierreCard clienteId={clienteId} areaActiva={areaActiva} />
    </div>
  );
};

export default CrearCierre;
