import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import HistorialCierres from "../components/HistorialCierres";
import { obtenerUsuario } from "../api/auth";

const HistorialCierresPage = () => {
  const { clienteId } = useParams();
  const [areaActiva, setAreaActiva] = useState(null);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    const determinarAreaActiva = async () => {
      try {
        // Primero intentar desde localStorage
        let area = localStorage.getItem("area_activa");
        
        if (!area) {
          // Si no hay área en localStorage, obtenerla del usuario
          const userData = await obtenerUsuario();
          if (userData.area_activa) {
            area = userData.area_activa;
          } else if (userData.areas && userData.areas.length > 0) {
            area = userData.areas[0].nombre || userData.areas[0];
          } else {
            area = "Contabilidad"; // fallback
          }
          localStorage.setItem("area_activa", area);
        }
        
        setAreaActiva(area);
      } catch (error) {
        console.error("Error determinando área activa:", error);
        setAreaActiva("Contabilidad"); // fallback
      } finally {
        setCargando(false);
      }
    };

    determinarAreaActiva();
  }, []);

  if (cargando) {
    return <div>Cargando...</div>;
  }

  return <HistorialCierres clienteId={clienteId} areaActiva={areaActiva} />;
};

export default HistorialCierresPage;
