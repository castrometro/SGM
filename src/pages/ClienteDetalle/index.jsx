import React from "react";
import { useClienteDetalle } from "./hooks/useClienteDetalle";
import ClienteDetalleHeader from "./components/ClienteDetalleHeader";
import ClienteInfoCard from "./components/ClienteInfoCard";
import ServiciosContratados from "./components/ServiciosContratados";
import KpiResumenCliente from "./components/KpiResumenCliente";
import ClienteActionButtons from "./components/ClienteActionButtons";
import { MESSAGES } from "./config/clienteDetalleConfig";

const ClienteDetalle = () => {
  const {
    cliente,
    resumen,
    servicios,
    areaActiva,
    areaConfig,
    loading,
    error,
    clienteId
  } = useClienteDetalle();

  if (loading) {
    return <p className="text-white">{MESSAGES.loading}</p>;
  }

  if (error) {
    return <p className="text-red-400">{error}</p>;
  }

  if (!cliente || !resumen) {
    return <p className="text-white">{MESSAGES.loading}</p>;
  }

  return (
    <div className="text-white space-y-6">
      <ClienteDetalleHeader 
        areaActiva={areaActiva} 
        areaConfig={areaConfig} 
      />
      
      <ClienteInfoCard 
        cliente={cliente} 
        resumen={resumen} 
        areaActiva={areaActiva} 
      />
      
      <ServiciosContratados 
        servicios={servicios} 
        areaActiva={areaActiva} 
      />
      
      {areaConfig?.showKpiResumen && (
        <KpiResumenCliente />
      )}
      
      <ClienteActionButtons 
        clienteId={clienteId} 
        areaActiva={areaActiva} 
      />
    </div>
  );
};

export default ClienteDetalle;
