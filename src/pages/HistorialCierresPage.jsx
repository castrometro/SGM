import { useParams } from "react-router-dom";
import HistorialCierres from "../components/HistorialCierres";

const HistorialCierresPage = () => {
  const { clienteId } = useParams();
  const areaActiva = localStorage.getItem("area_activa") || "Contabilidad";
  return <HistorialCierres clienteId={clienteId} areaActiva={areaActiva} />;
};

export default HistorialCierresPage;
