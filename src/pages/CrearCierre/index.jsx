import React from "react";
import { useCrearCierre } from "./hooks/useCrearCierre";
import ClienteInfoCard from "./components/ClienteInfoCard";
import CrearCierreCard from "./components/CrearCierreCard";
import { MESSAGES, LAYOUT_STYLES } from "./config/crearCierreConfig";

const CrearCierre = ({ areaActiva: propAreaActiva }) => {
  const {
    clienteId,
    cliente,
    resumen,
    areaActiva,
    areaConfig,
    loading,
    error
  } = useCrearCierre(propAreaActiva);

  if (loading) {
    return (
      <div className={LAYOUT_STYLES.loadingContainer}>
        {MESSAGES.loading}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-400 text-center mt-8">
        {error}
      </div>
    );
  }

  if (!cliente || !resumen) {
    return (
      <div className={LAYOUT_STYLES.loadingContainer}>
        {MESSAGES.loading}
      </div>
    );
  }

  return (
    <div className={LAYOUT_STYLES.container}>
      <ClienteInfoCard 
        cliente={cliente} 
        resumen={resumen} 
        areaActiva={areaActiva}
      />
      <CrearCierreCard 
        clienteId={clienteId} 
        areaActiva={areaActiva} 
      />
    </div>
  );
};

export default CrearCierre;
