import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  obtenerCliente,
  obtenerServiciosCliente,
} from "../api/clientes";
import { obtenerResumenContable } from "../api/contabilidad";
import { obtenerResumenNomina } from "../api/nomina";
import ClienteInfoCard from "../components/InfoCards/ClienteInfoCard";
import ServiciosContratados from "../components/ServiciosContratados";
import KpiResumenCliente from "../components/KpiResumenCliente";
import ClienteActionButtons from "../components/ClienteActionButtons";

const areaColors = {
  "Contabilidad": "bg-blue-600",
  "Nomina": "bg-violet-600",
  // agrega más si tienes más áreas
};

const ClienteDetalle = () => {
  const { id } = useParams();
  const [cliente, setCliente] = useState(null);
  const [resumen, setResumen] = useState(null);
  const [servicios, setServicios] = useState([]);
  // Puedes obtener el área activa desde localStorage, contexto o prop global
  const areaActiva = localStorage.getItem("area_activa") || "Contabilidad";

  useEffect(() => {
    const fetchDatos = async () => {
      try {
        const c = await obtenerCliente(id);
        // Pivotea aquí
        let r;
        if (areaActiva === "Contabilidad") {
          r = await obtenerResumenContable(id);
        } else if (areaActiva === "Nomina") {
          r = await obtenerResumenNomina(id);
        }
        const s = await obtenerServiciosCliente(id);
        setCliente(c);
        setResumen(r);
        setServicios(s);
      } catch (error) {
        console.error("Error cargando datos del cliente:", error);
      }
    };

    fetchDatos();
  }, [id, areaActiva]);

  if (!cliente || !resumen) {
    return <p className="text-white">Cargando cliente...</p>;
  }

  return (
    <div className="text-white space-y-6">
      <div className="flex items-center gap-4 mb-4">
        <h1 className="text-2xl font-bold">Detalle de Cliente</h1>
        <span className={`px-3 py-1 rounded-full text-white text-sm font-semibold ${areaColors[areaActiva] || "bg-gray-600"}`}>
          {areaActiva}
        </span>
      </div>
      <ClienteInfoCard cliente={cliente} resumen={resumen} />
      <ServiciosContratados servicios={servicios} areaActiva={areaActiva} />
      <KpiResumenCliente />
      <ClienteActionButtons clienteId={cliente.id} areaActiva={areaActiva} />
    </div>
  );
};

export default ClienteDetalle;
