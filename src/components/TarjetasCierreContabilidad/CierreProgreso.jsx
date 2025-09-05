import { useEffect, useState } from "react";
import TipoDocumentoCard from "./TipoDocumentoCard";
import LibroMayorCard from "./LibroMayorCard";
import ClasificacionBulkCard from "./ClasificacionBulkCard";
import NombresEnInglesCard from "./NombresEnInglesCard";
import {
  obtenerEstadoTipoDocumento,
  obtenerLibrosMayor,
  obtenerProgresoClasificacionTodosLosSets,
  obtenerEstadoNombresIngles,
} from "../../api/contabilidad";

const CierreProgreso = ({ cierre, cliente }) => {
  // Estados internos - nuevo orden
  const [tipoDocumentoReady, setTipoDocumentoReady] = useState(false);
  const [clasificacionReady, setClasificacionReady] = useState(false);
  const [nombresInglesReady, setNombresInglesReady] = useState(false);
  const [libroMayorReady, setLibroMayorReady] = useState(false);

  // Fetch por etapas, solo cuando corresponde
  useEffect(() => {
    const fetchEstados = async () => {
      // 1. Tipo de Documento
      const estadoTipoDoc = await obtenerEstadoTipoDocumento(cliente.id);
      const tipoDocOk = estadoTipoDoc === "subido";
      setTipoDocumentoReady(tipoDocOk);

      // 2. Clasificación de Cuentas (solo si paso anterior está ok)
      // La lógica de clasificacionReady se maneja directamente en el componente ClasificacionBulkCard
      // a través del callback handleClasificacionCompletado
      if (!tipoDocOk) {
        setClasificacionReady(false);
      }

      // 3. Nombres en inglés (solo si clasificación está ok y cliente es bilingüe)
      let nombresOk = false;
      if (clasificacionReady && cliente.bilingue) {
        const estadoNI = await obtenerEstadoNombresIngles(cliente.id);
        // El backend expone un objeto; considerar ready true si indica listo o si total_pendientes == 0
        if (estadoNI) {
          const readyFlag = estadoNI.ready ?? (estadoNI.pendientes === 0);
          nombresOk = Boolean(readyFlag);
        }
        setNombresInglesReady(nombresOk);
      } else {
        // Si no es bilingüe, este paso no aplica y se considera listo
        setNombresInglesReady(!cliente.bilingue);
      }

      // 4. Libro Mayor (solo si pasos anteriores están ok)
  const prerequisitosLibro = clasificacionReady && (cliente.bilingue ? nombresOk : true);
      if (prerequisitosLibro) {
        const libros = await obtenerLibrosMayor(cierre.id);
        const libroActual =
          libros && libros.length > 0 ? libros[libros.length - 1] : null;
        const libroOk = libroActual && libroActual.estado === "completado";
        setLibroMayorReady(libroOk);
      } else {
        setLibroMayorReady(false);
      }
    };

    if (cierre && cliente) fetchEstados();
  }, [cierre, cliente, clasificacionReady]); // Agregamos clasificacionReady como dependencia

  // Callbacks para actualizar pasos tras acción de usuario
  const handleTipoDocumentoCompletado = (ready) => setTipoDocumentoReady(ready);
  const handleClasificacionCompletado = (ready) => setClasificacionReady(ready);
  const handleTraduccionCompletada = () => setNombresInglesReady(true);
  const handleLibroMayorCompletado = () => setLibroMayorReady(true);

  let paso = 1;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Paso 1: Tipos de Documento */}
      <TipoDocumentoCard
        clienteId={cliente.id}
        cierreId={cierre.id}
        cliente={cliente}
        onCompletado={handleTipoDocumentoCompletado}
        disabled={false}
        numeroPaso={paso++}
      />

      {/* Paso 2: Clasificación de Cuentas */}
      <ClasificacionBulkCard
        clienteId={cliente.id}
        cierreId={cierre.id}
        cliente={cliente}
        onCompletado={handleClasificacionCompletado}
        disabled={!tipoDocumentoReady}
        numeroPaso={paso++}
      />

      {/* Paso 3: Nombres en Inglés (solo si cliente es bilingüe) */}
      {cliente.bilingue && (
        <NombresEnInglesCard
          clienteId={cliente.id}
          cierreId={cierre.id}
          cliente={cliente}
          onCompletado={handleTraduccionCompletada}
          disabled={!clasificacionReady}
          numeroPaso={paso++}
        />
      )}

      {/* Paso 4: Libro Mayor (procesamiento final) */}
      <LibroMayorCard
        cierreId={cierre.id}
        clienteId={cliente.id}
        cliente={cliente}
        disabled={
          !clasificacionReady || (cliente.bilingue && !nombresInglesReady)
        }
        onCompletado={handleLibroMayorCompletado}
        tipoDocumentoReady={tipoDocumentoReady}
        clasificacionReady={clasificacionReady}
        nombresInglesReady={nombresInglesReady}
        numeroPaso={paso++}
      />
    </div>
  );
};

export default CierreProgreso;
