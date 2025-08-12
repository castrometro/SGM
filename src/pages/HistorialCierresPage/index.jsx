import React from "react";
import { useHistorialCierres } from "./hooks/useHistorialCierres";
import HistorialCierres from "./components/HistorialCierres";
import { MESSAGES } from "./config/historialCierresConfig";

const HistorialCierresPage = () => {
  const {
    clienteId,
    areaActiva,
    cargando,
    error
  } = useHistorialCierres();

  if (cargando) {
    return <div className="text-white">{MESSAGES.loading}</div>;
  }

  if (error) {
    return <div className="text-red-400">{error}</div>;
  }

  return (
    <div className="text-white">
      <HistorialCierres 
        clienteId={clienteId} 
        areaActiva={areaActiva} 
      />
    </div>
  );
};

export default HistorialCierresPage;
