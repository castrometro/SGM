import { LogOut } from "lucide-react";
import { descargarPlantillaFiniquitos } from "../../../api/nomina";
import ArchivoAnalistaBase from "./ArchivoAnalistaBase";

const FiniquitosCard = ({ 
  estado, 
  archivo, 
  error, 
  subiendo, 
  disabled, 
  onSubirArchivo, 
  onReprocesar,
  onEliminarArchivo
}) => {
  return (
    <ArchivoAnalistaBase
      tipo="finiquitos"
      titulo="Finiquitos"
      icono={LogOut}
      descripcion="Datos de empleados con finiquito"
      plantilla={descargarPlantillaFiniquitos}
      estado={estado}
      archivo={archivo}
      error={error}
      subiendo={subiendo}
      disabled={disabled}
      onSubirArchivo={onSubirArchivo}
      onReprocesar={onReprocesar}
      onEliminarArchivo={onEliminarArchivo}
    />
  );
};

export default FiniquitosCard;
