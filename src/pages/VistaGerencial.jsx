import { useState, useEffect } from "react";
// import ResumenProcesosNomina from "../components/VistaGerencial/ResumenProcesosNomina"; // REMOVIDO - Limpieza de nómina
import IndicadoresClave from "../components/VistaGerencial/IndicadoresClave";
import GestionAsignaciones from "../components/VistaGerencial/GestionAsignaciones";
import ReportesAuditoria from "../components/VistaGerencial/ReportesAuditoria";
import AlertasProcesos from "../components/VistaGerencial/AlertasProcesos";
// import { obtenerCierresNomina } from "../api/nomina"; // REMOVIDO - Limpieza de nómina

const VistaGerencial = () => {
  const [cierres, setCierres] = useState([]);
  const [cargando, setCargando] = useState(true);
  const usuario = JSON.parse(localStorage.getItem("usuario"));

  useEffect(() => {
    cargarDatos();
  }, []);

  const cargarDatos = async () => {
    try {
      setCargando(true);
      // Cargar todos los cierres de nómina para la vista gerencial
      const data = await obtenerCierresNomina();
      setCierres(Array.isArray(data) ? data : data.results || []);
    } catch (error) {
      console.error("Error cargando datos gerenciales:", error);
    } finally {
      setCargando(false);
    }
  };

  if (cargando) {
    return (
      <div className="text-white text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
        <p>Cargando vista gerencial...</p>
      </div>
    );
  }

  return (
    <div className="text-white space-y-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Vista Gerencial - Nómina</h1>
        <p className="text-gray-400">
          Control y supervisión integral de todos los procesos de nómina
        </p>
      </div>

      {/* Grid principal con las tarjetas modulares */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Tarjeta 1: Resumen de Procesos por Cliente y Estado */}
        <div className="lg:col-span-2">
          <ResumenProcesosNomina cierres={cierres} onActualizar={cargarDatos} />
        </div>

        {/* Tarjeta 2: Indicadores Clave */}
        <IndicadoresClave cierres={cierres} />

        {/* Tarjeta 3: Alertas y Procesos Detenidos */}
        <AlertasProcesos cierres={cierres} />

        {/* Tarjeta 4: Gestión de Asignaciones */}
        <GestionAsignaciones />

        {/* Tarjeta 5: Reportes y Auditoría */}
        <ReportesAuditoria cierres={cierres} />

      </div>
    </div>
  );
};

export default VistaGerencial;
