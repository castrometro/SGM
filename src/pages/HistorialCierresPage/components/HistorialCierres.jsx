import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { obtenerCierresCliente as obtenerCierresContabilidad } from "../../../api/contabilidad";
import { obtenerCierresPayrollCliente } from "../../../api/payroll";
// import { obtenerCierresCliente as obtenerCierresNomina } from "../../../api/nomina"; // REMOVIDO - Limpieza de nómina
import EstadoBadge from "../../../components/EstadoBadge";

const HistorialCierres = ({ clienteId, areaActiva }) => {
  const [cierres, setCierres] = useState([]);
  const navigate = useNavigate();

  // Helper para determinar si un cierre puede ser finalizado
  const puedeFinalizarse = (cierre) => {
    return cierre.estado === 'sin_incidencias';
  };

  // Helper para determinar acciones adicionales según el estado
  const getAccionesAdicionales = (cierre) => {
    if (areaActiva !== "Contabilidad") return null;
    
    if (puedeFinalizarse(cierre)) {
      return (
        <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
          ✓ Listo para finalizar
        </span>
      );
    }
    
    if (cierre.estado === 'generando_reportes') {
      return (
        <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full">
          ⏳ Generando reportes...
        </span>
      );
    }
    
    if (cierre.estado === 'completado') {
      return (
        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
          📊 Reportes disponibles
        </span>
      );
    }
    
    return null;
  };

  useEffect(() => {
    const fetchCierres = async () => {
      let res = [];
      if (areaActiva === "Contabilidad") {
        res = await obtenerCierresContabilidad(clienteId);
      } else if (areaActiva === "Payroll" || areaActiva === "Nomina") {
        res = await obtenerCierresPayrollCliente(clienteId);
        // Ajustar la estructura si es necesario para que coincida con la tabla
        if (res.results) {
          res = res.results; // La API de payroll devuelve {count, results}
        }
      } else {
        // Fallback para otras áreas
        res = await obtenerCierresContabilidad(clienteId);
      }
      setCierres(res);
    };
    if (clienteId) fetchCierres();
  }, [clienteId, areaActiva]);

  // Auto-refresh para cierres en proceso
  useEffect(() => {
    const cierresEnProceso = cierres.filter(cierre => 
      cierre.estado === 'generando_reportes' || cierre.estado === 'procesando'
    );
    
    if (cierresEnProceso.length > 0) {
      const interval = setInterval(async () => {
        // Refrescar datos cada 30 segundos si hay cierres en proceso
        let res = [];
        if (areaActiva === "Contabilidad") {
          res = await obtenerCierresContabilidad(clienteId);
        } else if (areaActiva === "Payroll" || areaActiva === "Nomina") {
          res = await obtenerCierresPayrollCliente(clienteId);
          if (res.results) {
            res = res.results; // La API de payroll devuelve {count, results}
          }
        } else {
          // Fallback para otras áreas
          res = await obtenerCierresContabilidad(clienteId);
        }
        setCierres(res);
      }, 30000); // 30 segundos
      
      return () => clearInterval(interval);
    }
  }, [cierres, clienteId, areaActiva]);

  if (!cierres.length) return <p>No hay cierres registrados aún.</p>;

  return (
    <div className="mt-4">
      <h4 className="text-md font-bold mb-2">Historial de Cierres ({areaActiva})</h4>
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-separate border-spacing-y-1">
          <thead>
            <tr className="bg-gray-700">
              <th className="px-4 py-2 text-left">Periodo</th>
              <th className="px-4 py-2 text-left">Estado</th>
              <th className="px-4 py-2 text-left">Fecha creación</th>
              <th className="px-4 py-2 text-left" colSpan={2}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {cierres.map(cierre => (
              <tr key={cierre.id} className="border-b border-gray-700 hover:bg-gray-600">
                <td className="px-4 py-2">{cierre.periodo}</td>
                <td className="px-4 py-2">
                  <EstadoBadge estado={cierre.estado} size="sm" />
                </td>
                <td className="px-4 py-2">{new Date(cierre.fecha_creacion).toLocaleDateString()}</td>
                <td className="px-4 py-2">
                  <button
                    className="text-blue-500 underline font-medium"
                    onClick={() => {
                      if (areaActiva === "Contabilidad") {
                        navigate(`/menu/cierres/${cierre.id}`);
                      } else if (areaActiva === "Payroll" || areaActiva === "Nomina") {
                        navigate(`/menu/clientes/${clienteId}/cierres-payroll/${cierre.id}`);
                      } else {
                        // Fallback para otras áreas
                        navigate(`/menu/cierres/${cierre.id}`);
                      }
                    }}
                  >
                    Ver detalles
                  </button>
                </td>
                <td className="px-4 py-2">
                  {(cierre.estado === "completo" || 
                    cierre.estado === "sin_incidencias" || 
                    cierre.estado === "finalizado") && 
                   areaActiva === "Contabilidad" && (
                    <button
                      className="text-green-500 underline font-medium"
                      onClick={() => navigate(`/menu/cierres/${cierre.id}/libro`)}
                    >
                      Visualizar libro
                    </button>
                  )}
                  {/* Aquí puedes poner otras acciones para Nómina */}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default HistorialCierres;
