import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { obtenerCliente } from "../api/clientes";
import { obtenerResumenContable } from "../api/contabilidad";
import { obtenerResumenNomina, obtenerKpisNominaCliente } from "../api/nomina";
import { obtenerUsuario } from "../api/auth";
import ClienteInfoCard from "../components/InfoCards/ClienteInfoCard";
// import ServiciosContratados from "../components/ServiciosContratados"; // (comentado) Bloque retirado temporalmente: poco aporte actual
import KpiResumenCliente from "../components/KpiResumenCliente";
import ClienteActionButtons from "../components/ClienteActionButtons";
import { getAreaColor } from "../constants/areaColors";

const ClienteDetalle = () => {
  const { id } = useParams();
  const [cliente, setCliente] = useState(null);
  const [resumen, setResumen] = useState(null);
  // const [servicios, setServicios] = useState([]); // Eliminado: ya no se consumen servicios
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
          // Usamos agregador de KPIs (si falla, fallback a resumen básico existente)
            let kpisData = null;
            try {
              kpisData = await obtenerKpisNominaCliente(id);
            } catch (e) {
              console.warn("Fallo obtenerKpisNominaCliente, fallback a obtenerResumenNomina", e);
            }
            if (kpisData?.tieneCierre && kpisData?.raw?.libro) {
              const libro = kpisData.raw.libro;
              // Normalizamos estructura esperada por KpiResumenCliente (campos plano + totales_categorias)
              r = {
                ...libro, // contiene cierre, totales_categorias, conceptos, meta
                ultimo_cierre: kpisData.periodo,
                estado_cierre_actual: kpisData.estado_cierre,
                empleados_activos: libro?.cierre?.total_empleados ?? kpisData.kpis?.total_empleados ?? null,
                // Alias para consistencia previa
                total_empleados: libro?.cierre?.total_empleados ?? kpisData.kpis?.total_empleados ?? null,
                kpis: kpisData.kpis,
              };
            } else {
              // Fallback minimal
              r = await obtenerResumenNomina(id);
            }
        }

        // Petición de servicios eliminada para ahorrar request innecesaria
        setCliente(c);
        setResumen(r);
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
      {/**
       * Bloque "Servicios Contratados" oculto a petición del usuario (no aporta mucho ahora).
       * Mantener el estado y la carga de 'servicios' arriba permite reactivarlo rápido si se decide volver a mostrar.
       * Para eliminar definitivamente: quitar estado 'servicios', llamada obtenerServiciosCliente y este comentario.
       */}
      {false && (
        // <ServiciosContratados servicios={servicios} areaActiva={areaActiva} />
        <div />
      )}
  <KpiResumenCliente resumen={resumen} areaActiva={areaActiva} />
      <ClienteActionButtons clienteId={cliente.id} areaActiva={areaActiva} />
    </div>
  );
};

export default ClienteDetalle;
