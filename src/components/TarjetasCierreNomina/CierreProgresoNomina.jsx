import { useEffect, useState } from "react";
import LibroRemuneracionesCard from "./LibroRemuneracionesCard";
import ModalClasificacionHeaders from "../ModalClasificacionHeaders";
import {
  obtenerEstadoLibroRemuneraciones,
  subirLibroRemuneraciones,
  guardarConceptosRemuneracion,
  obtenerClasificacionesCliente,
} from "../../api/nomina";

const CierreProgresoNomina = ({ cierre, cliente }) => {
  const [libro, setLibro] = useState(null);
  const [subiendo, setSubiendo] = useState(false);
  const [modalAbierto, setModalAbierto] = useState(false);

  const handleGuardarClasificaciones = async (clasificaciones) => {
    try {
      await guardarConceptosRemuneracion(cliente.id, clasificaciones);
      await obtenerEstadoLibroRemuneraciones(cierre.id).then(setLibro);
    } catch (error) {
      console.error("Error al guardar clasificaciones:", error);
    }
  };

  if (!cierre || !cliente) {
    return (
      <div className="text-white text-center py-6">
        Cargando datos de cierre de nómina...
      </div>
    );
  }

  useEffect(() => {
    if (cierre?.id) {
      obtenerEstadoLibroRemuneraciones(cierre.id).then(setLibro);
    }
  }, [cierre]);

  const handleSubirArchivo = async (archivo) => {
    setSubiendo(true);
    try {
      await subirLibroRemuneraciones(cierre.id, archivo);
      setTimeout(() => {
        obtenerEstadoLibroRemuneraciones(cierre.id).then(setLibro);
      }, 1200);
    } finally {
      setSubiendo(false);
    }
  };

  const headersSinClasificar = Array.isArray(libro?.header_json?.headers_sin_clasificar)
    ? libro.header_json.headers_sin_clasificar
    : [];

  const headersClasificados =
    Array.isArray(libro?.header_json?.headers_clasificados)
      ? libro.header_json.headers_clasificados.reduce((acc, header) => {
          acc[header] = {
            clasificacion: "haber", // por defecto si no tienes info real
            hashtags: [],
          };
          return acc;
        }, {})
      : {};

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <LibroRemuneracionesCard
        estado={libro?.estado || "no_subido"}
        archivoNombre={libro?.archivo_nombre}
        subiendo={subiendo}
        onSubirArchivo={handleSubirArchivo}
        onVerClasificacion={() => setModalAbierto(true)}
        headersSinClasificar={headersSinClasificar}
        headerClasificados={Object.keys(headersClasificados)}
        disabled={false}
      />
      <ModalClasificacionHeaders
        isOpen={modalAbierto}
        onClose={() => setModalAbierto(false)}
        clienteId={cliente.id}
        headersSinClasificar={headersSinClasificar}
        onGuardarClasificaciones={handleGuardarClasificaciones}
      />
    </div>
  );
};

export default CierreProgresoNomina;
