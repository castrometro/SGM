import { useState } from "react";
import { AlertCircle, Settings } from "lucide-react";
import { 
  descargarPlantillaNovedades,
  obtenerHeadersNovedades,
  mapearHeadersNovedades,
  procesarFinalNovedades
} from "../../../api/nomina";
import ArchivoAnalistaBase from "./ArchivoAnalistaBase";
import ModalMapeoNovedades from "../../ModalMapeoNovedades";

const NovedadesCard = ({ 
  estado, 
  archivo, 
  error, 
  subiendo, 
  disabled, 
  onSubirArchivo, 
  onReprocesar,
  onEliminarArchivo,
  onActualizarEstado,
  cierreId,
  cliente
}) => {
  const [modalMapeoAbierto, setModalMapeoAbierto] = useState(false);
  const [headersNovedades, setHeadersNovedades] = useState({ 
    headers_sin_clasificar: [], 
    headers_clasificados: [] 
  });
  const [errorLocal, setErrorLocal] = useState("");

  const handleMapearHeaders = async () => {
    if (!archivo?.id) return;
    
    try {
      setErrorLocal("");
      const headers = await obtenerHeadersNovedades(archivo.id);
      setHeadersNovedades(headers);
      setModalMapeoAbierto(true);
    } catch (error) {
      console.error("Error obteniendo headers de novedades:", error);
      setErrorLocal("Error al obtener headers para mapeo");
    }
  };

  const handleVerMapeos = async () => {
    if (!archivo?.id) return;
    
    try {
      setErrorLocal("");
      const headers = await obtenerHeadersNovedades(archivo.id);
      setHeadersNovedades(headers);
      setModalMapeoAbierto(true);
    } catch (error) {
      console.error("Error obteniendo headers de novedades:", error);
      setErrorLocal("Error al cargar mapeos existentes");
    }
  };

  const handleGuardarMapeos = async (mapeos) => {
    try {
      setErrorLocal("");
      await mapearHeadersNovedades(archivo.id, mapeos);
      
      // Actualizar estado después de guardar mapeos
      if (onActualizarEstado) {
        await onActualizarEstado();
      }
      
      // Recargar headers actualizados
      const headersActualizados = await obtenerHeadersNovedades(archivo.id);
      setHeadersNovedades(headersActualizados);
      
    } catch (error) {
      console.error("Error guardando mapeos:", error);
      setErrorLocal("Error al guardar mapeos");
      throw error; // Para que el modal maneje el error
    }
  };

  const handleProcesarFinal = async () => {
    if (!archivo?.id) return;
    
    try {
      setErrorLocal("");
      await procesarFinalNovedades(archivo.id);
      
      // Actualizar estado después de iniciar procesamiento
      if (onActualizarEstado) {
        await onActualizarEstado();
      }
    } catch (error) {
      console.error("Error procesando novedades:", error);
      setErrorLocal("Error al procesar archivo final");
    }
  };

  // Determinar qué botones mostrar según el estado
  const renderBotonesEspeciales = () => {
    if (!archivo?.id) return null;

    return (
      <div className="flex flex-col gap-2 mt-2">
        {/* Botón único para mapear/ver headers según el estado */}
        <button
          type="button"
          onClick={estado === 'procesado' ? handleVerMapeos : handleMapearHeaders}
          className={`px-3 py-1 rounded text-sm font-medium transition flex items-center gap-1 ${
            estado === 'procesado' 
              ? 'bg-blue-700 hover:bg-blue-600'
              : (estado === 'clasif_pendiente' || estado === 'hdrs_analizados')
                ? 'bg-orange-600 hover:bg-orange-500'
                : 'bg-blue-700 hover:bg-blue-600'
          }`}
        >
          <Settings size={14} />
          {estado === 'procesado' ? 'Ver Mapeos' : estado === 'clasif_pendiente' ? 'Mapear Headers Pendientes' : 'Administrar Mapeos'}
        </button>
        
        {/* Botón Procesar Final - aparece cuando está completamente mapeado */}
        {estado === 'clasificado' && (
          <button
            type="button"
            onClick={handleProcesarFinal}
            className="bg-green-600 hover:bg-green-500 px-3 py-1 rounded text-sm font-medium transition"
          >
            Procesar Final
          </button>
        )}
        
        {/* Mensajes informativos según el estado */}
        {estado === 'hdrs_analizados' && (
          <div className="text-sm text-blue-400 bg-blue-900/20 p-2 rounded">
            ℹ️ Headers analizados, necesita mapeo...
          </div>
        )}
        
        {estado === 'clasif_pendiente' && (
          <div className="text-sm text-orange-400 bg-orange-900/20 p-2 rounded">
            ⚠️ Mapeo de headers pendiente
          </div>
        )}
        
        {estado === 'clasificado' && (
          <div className="text-sm text-green-400 bg-green-900/20 p-2 rounded">
            ✅ Headers mapeados - Listo para procesar
          </div>
        )}
      </div>
    );
  };

  return (
    <>
      <ArchivoAnalistaBase
        tipo="novedades"
        titulo="Novedades"
        icono={AlertCircle}
        descripcion="Cambios y actualizaciones de empleados"
        plantilla={descargarPlantillaNovedades}
        estado={estado}
        archivo={archivo}
        error={error || errorLocal}
        subiendo={subiendo}
        disabled={disabled}
        onSubirArchivo={onSubirArchivo}
        onReprocesar={onReprocesar}
        onEliminarArchivo={onEliminarArchivo}
      >
        {renderBotonesEspeciales()}
      </ArchivoAnalistaBase>

      <ModalMapeoNovedades
        isOpen={modalMapeoAbierto}
        onClose={() => setModalMapeoAbierto(false)}
        cierreId={cierreId}
        headersSinClasificar={headersNovedades.headers_sin_clasificar || []}
        headersClasificados={headersNovedades.headers_clasificados || []}
        mapeosExistentes={headersNovedades.mapeos_existentes || {}}
        onGuardarMapeos={handleGuardarMapeos}
        soloLectura={estado === 'procesado'}
      />
    </>
  );
};

export default NovedadesCard;
