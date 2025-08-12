import React from "react";
import { useParams } from "react-router-dom";
import { useCierreDetalle } from "./hooks/useCierreDetalle";
import CierreInfoBar from "./components/CierreInfoBar";
import CierreAreaRouter from "./components/CierreAreaRouter";
import { determinarModuloCierre } from "./config/areas";

const CierreDetalle = () => {
  const { cierreId } = useParams();
  const { cierre, cliente, loading, error, actualizarCierre } = useCierreDetalle(cierreId);

  // Determinar el tipo de módulo basado en configuración
  const tipoModulo = determinarModuloCierre(
    cierre, 
    null, // TODO: Pasar usuario logueado
    window.location.pathname
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-white text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p>Cargando datos del cierre...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="bg-red-600 text-white p-4 rounded-lg">
            <h3 className="font-bold mb-2">Error al cargar el cierre</h3>
            <p>{error.message || 'Error desconocido'}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!cierre || !cliente) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-white text-center">
          <h3 className="text-lg font-semibold mb-2">Cierre no encontrado</h3>
          <p>No se pudo cargar la información del cierre solicitado.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Barra de información del cierre */}
      <CierreInfoBar 
        cierre={cierre} 
        cliente={cliente} 
        onCierreActualizado={actualizarCierre}
        tipoModulo={tipoModulo}
      />

      {/* Router de área específica */}
      <CierreAreaRouter 
        cierre={cierre} 
        cliente={cliente} 
        tipoModulo={tipoModulo}
      />
    </div>
  );
};

export default CierreDetalle;
