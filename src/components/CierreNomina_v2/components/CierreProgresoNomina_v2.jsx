import React from "react";
import useCierreNomina from "../hooks/useCierreNomina";
import ArchivosTalanaSection_v2 from "./sections/ArchivosTalanaSection_v2";
import ArchivosAnalistaSection_v2 from "./sections/ArchivosAnalistaSection_v2";
import VerificadorDatosSection_v2 from "./sections/VerificadorDatosSection_v2";
import IncidenciasSection_v2 from "./sections/IncidenciasSection_v2";

const CierreProgresoNomina_v2 = ({ cierre, cliente }) => {
  // 🎯 HOOK PERSONALIZADO QUE CALCULA SECCIONES HABILITADAS
  const {
    seccionesHabilitadas,
    estaSeccionHabilitada
  } = useCierreNomina(cierre);

  if (!cierre || !cliente) {
    return (
      <div className="text-center text-gray-400 py-8">
        <p>No hay datos del cierre disponibles</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">

      {/* 📊 SECCIONES DEL CIERRE */}
      <div className="grid grid-cols-1 gap-6">
        
        {/* 🥇 SECCIÓN 1: ARCHIVOS TALANA */}
        <ArchivosTalanaSection_v2
          cierreId={cierre.id}
          enabled={estaSeccionHabilitada('archivosTalana')}
          titulo="1. Archivos de Talana"
          descripcion="Subir Libro de Remuneraciones y Movimientos del Mes"
        />

        {/* 🥈 SECCIÓN 2: ARCHIVOS ANALISTA */}
        <ArchivosAnalistaSection_v2
          cierreId={cierre.id}
          enabled={estaSeccionHabilitada('archivosAnalista')}
          titulo="2. Archivos del Analista"
          descripcion="Archivos adicionales proporcionados por el analista"
        />

        {/* 🥉 SECCIÓN 3: VERIFICADOR DE DATOS */}
        <VerificadorDatosSection_v2
          cierreId={cierre.id}
          enabled={estaSeccionHabilitada('verificadorDatos')}
          titulo="3. Verificación de Datos"
          descripcion="Verificar discrepancias y consolidar datos"
        />

        {/* � SECCIÓN 4: INCIDENCIAS */}
        <IncidenciasSection_v2
          cierreId={cierre.id}
          enabled={estaSeccionHabilitada('incidencias')}
          titulo="4. Gestión de Incidencias"
          descripcion="Resolver incidencias encontradas y finalizar cierre"
        />

      </div>

    </div>
  );
};

export default CierreProgresoNomina_v2;
