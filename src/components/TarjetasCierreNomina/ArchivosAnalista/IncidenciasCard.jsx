import { UserCheck } from "lucide-react";
import { descargarPlantillaIncidencias } from "../../../api/nomina";
import ArchivoAnalistaBase from "./ArchivoAnalistaBase";

const IncidenciasCard = ({ 
  estado, 
  archivo, 
  error, 
  subiendo, 
  disabled, 
  onSubirArchivo, 
  onReprocesar 
}) => {
  return (
    <ArchivoAnalistaBase
      tipo="incidencias"
      titulo="Incidencias/Ausentismos"
      icono={UserCheck}
      descripcion="Licencias médicas, permisos, etc."
      plantilla={descargarPlantillaIncidencias}
      estado={estado}
      archivo={archivo}
      error={error}
      subiendo={subiendo}
      disabled={disabled}
      onSubirArchivo={onSubirArchivo}
      onReprocesar={onReprocesar}
    />
  );
};

export default IncidenciasCard;
