import { Upload } from "lucide-react";
import { descargarPlantillaIngresos } from "../../../api/nomina";
import ArchivoAnalistaBase from "./ArchivoAnalistaBase";

const IngresosCard = ({ 
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
      tipo="ingresos"
      titulo="Ingresos"
      icono={Upload}
      descripcion="Nuevos empleados que ingresan"
      plantilla={descargarPlantillaIngresos}
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

export default IngresosCard;
