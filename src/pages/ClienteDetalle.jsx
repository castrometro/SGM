import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  obtenerCliente,
  obtenerServiciosCliente,
} from "../api/clientes";
import { obtenerResumenContable } from "../api/contabilidad";
// import { obtenerResumenNomina } from "../api/nomina"; // REMOVIDO - Limpieza de nómina
import { obtenerUsuario } from "../api/auth";
import ClienteInfoCard from "../components/InfoCards/ClienteInfoCard";
import ServiciosContratados from "../components/ServiciosContratados";
import KpiResumenCliente from "../components/KpiResumenCliente";
import ClienteActionButtons from "../components/ClienteActionButtons";
import { getAreaColor } from "../constants/areaColors";

const ClienteDetalle = () => {
  const { id } = useParams();
  const [cliente, setCliente] = useState(null);
  const [resumen, setResumen] = useState(null);
  const [servicios, setServicios] = useState([]);
  const [areaActiva, setAreaActiva] = useState("Contabilidad");

  useEffect(() => {
    const fetchDatos = async () => {
      try {
        const c = await obtenerCliente(id);
        const u = await obtenerUsuario(); // Obtener usuario para determinar área activa
        let r;

        // Determinar área activa según el usuario
        let area = localStorage.getItem("area_activa");
        
        if (!area) {
          if (u.area_activa) {
            area = u.area_activa;
          } else if (u.areas && u.areas.length > 0) {
            area = u.areas[0].nombre || u.areas[0];
          } else if (u.area) {
            area = u.area; // fallback al campo area si existe
          } else {
            area = "Contabilidad"; // fallback final
          }
          localStorage.setItem("area_activa", area);
        }
        
        setAreaActiva(area);
        
        if (area === "Contabilidad") {
          r = await obtenerResumenContable(id);
        } else if (area === "Nomina") {
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
  }, [id]);

  if (!cliente || !resumen) {
    return <p className="text-white">Cargando cliente...</p>;
  }

  return (
    <div className="text-white space-y-6">
      <div className="flex items-center gap-4 mb-4">
        <h1 className="text-2xl font-bold">Detalle de Cliente</h1>
        <span className={`px-3 py-1 rounded-full text-white text-sm font-semibold ${getAreaColor(areaActiva)}`}>
          {areaActiva}
        </span>
      </div>
      <ClienteInfoCard cliente={cliente} resumen={resumen} areaActiva={areaActiva} />
      <ServiciosContratados servicios={servicios} areaActiva={areaActiva} />
      <KpiResumenCliente />
      <ClienteActionButtons clienteId={cliente.id} areaActiva={areaActiva} />
    </div>
  );
};

export default ClienteDetalle;
