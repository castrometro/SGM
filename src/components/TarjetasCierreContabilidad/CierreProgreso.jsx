import { useEffect, useState } from "react";
import TipoDocumentoCard from "./TipoDocumentoCard";
import LibroMayorCard from "./LibroMayorCard";
import ClasificacionResumenCard from "./ClasificacionResumenCard";
import NombresEnInglesCard from "./NombresEnInglesCard";
import {
  obtenerEstadoTipoDocumento,
  obtenerLibrosMayor,
  obtenerProgresoClasificacionTodosLosSets,
  obtenerEstadoNombresIngles,
} from "../../api/contabilidad";

const CierreProgreso = ({ cierre, cliente }) => {
  // Estados internos
  const [tipoDocumentoReady, setTipoDocumentoReady] = useState(false);
  const [libroMayorReady, setLibroMayorReady] = useState(false);
  const [clasificacionReady, setClasificacionReady] = useState(false);
  const [nombresInglesReady, setNombresInglesReady] = useState(false);

  // Fetch por etapas, solo cuando corresponde
  useEffect(() => {
    const fetchEstados = async () => {
      // 1. Tipo de Documento
      const estadoTipoDoc = await obtenerEstadoTipoDocumento(cliente.id);
      const tipoDocOk = estadoTipoDoc === "subido";
      setTipoDocumentoReady(tipoDocOk);

      // 2. Libro Mayor (solo si paso anterior está ok)
      let libroOk = false;
      let libroActual = null;
      if (tipoDocOk) {
        const libros = await obtenerLibrosMayor(cierre.id);
        libroActual = libros && libros.length > 0 ? libros[libros.length - 1] : null;
        libroOk = libroActual && libroActual.estado === "completado";
        setLibroMayorReady(libroOk);
      } else {
        setLibroMayorReady(false);
      }

      // 3. Clasificación (solo si paso anterior está ok)
      let clasificacionOk = false;
      if (libroOk) {
        const clasificacion = await obtenerProgresoClasificacionTodosLosSets(cierre.id);
        clasificacionOk =
          clasificacion &&
          clasificacion.sets_progreso.length > 0 &&
          clasificacion.sets_progreso.every((s) => s.estado === "Completo");
        setClasificacionReady(clasificacionOk);
      } else {
        setClasificacionReady(false);
      }

      // 4. Nombres en inglés (solo si paso anterior está ok)
      if (clasificacionOk) {
        const nombresIngles = await obtenerEstadoNombresIngles(cliente.id, cierre.id);
        setNombresInglesReady(nombresIngles && nombresIngles.estado === "subido");
      } else {
        setNombresInglesReady(false);
      }
    };

    if (cierre && cliente) fetchEstados();
  }, [cierre, cliente]);

  // Callbacks para actualizar pasos tras acción de usuario
  const handleTipoDocumentoCompletado = (ready) => setTipoDocumentoReady(ready);
  const handleLibroMayorCompletado = () => setLibroMayorReady(true);
  const handleClasificacionCompletado = (ready) => setClasificacionReady(ready);
  const handleTraduccionCompletada = () => setNombresInglesReady(true);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <TipoDocumentoCard
        clienteId={cliente.id}
        onCompletado={handleTipoDocumentoCompletado}
        disabled={false}
      />
      <LibroMayorCard
        cierreId={cierre.id}
        disabled={!tipoDocumentoReady}
        onCompletado={handleLibroMayorCompletado}
      />
      <ClasificacionResumenCard
        cierreId={cierre.id}
        libroMayorReady={libroMayorReady}
        onCompletado={handleClasificacionCompletado}
      />
      {cliente.bilingue && (
        <NombresEnInglesCard
          cierreId={cierre.id}
          clienteId={cliente.id}
          clasificacionReady={clasificacionReady}
          onCompletado={handleTraduccionCompletada}
        />
      )}
    </div>
  );
};

export default CierreProgreso;
