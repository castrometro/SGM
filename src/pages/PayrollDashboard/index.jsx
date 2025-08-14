import React from 'react';
import { usePayrollDashboard } from './hooks/usePayrollDashboard';
import MetricCard from './components/MetricCard';
import QuickActions from './components/QuickActions';
import { MESSAGES } from './config/dashboardConfig';

/**
 * Dashboard principal de Payroll
 * Muestra métricas, estadísticas y acciones rápidas según el tipo de usuario
 */
const PayrollDashboard = () => {
  const {
    usuario,
    areaActiva,
    dashboardData,
    userConfig,
    widgets,
    cargando,
    error
  } = usePayrollDashboard();

  if (cargando) {
    return (
      <div className="text-white flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
          {MESSAGES.loading}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-400 flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-lg font-semibold mb-2">⚠️ Error</p>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!usuario || !userConfig) {
    return (
      <div className="text-white flex items-center justify-center h-64">
        {MESSAGES.noAccess}
      </div>
    );
  }

  return (
    <div className="text-white space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2 animate-fade-in">
            {MESSAGES.welcome}
          </h1>
          <p className="text-gray-400">
            {MESSAGES.subtitle}
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          <span className="px-3 py-1 rounded-full bg-purple-600/30 text-purple-300 text-sm font-semibold border border-purple-500/30">
            {userConfig.title}
          </span>
          <span className="px-3 py-1 rounded-full bg-blue-600/30 text-blue-300 text-sm font-semibold border border-blue-500/30">
            {areaActiva}
          </span>
        </div>
      </div>

      {/* Métricas */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Métricas Principales</h2>
        
        {widgets.length === 0 ? (
          <div className="bg-gray-800/50 rounded-lg p-8 text-center">
            <p className="text-gray-400">
              No hay métricas disponibles para tu nivel de acceso.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {widgets.map((widgetKey) => (
              <MetricCard
                key={widgetKey}
                cardKey={widgetKey}
                data={dashboardData}
                userType={usuario.tipo_usuario}
              />
            ))}
          </div>
        )}
      </div>

      {/* Acciones Rápidas */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <QuickActions 
            userType={usuario.tipo_usuario}
            areaActiva={areaActiva}
          />
        </div>
        
        {/* Información del usuario */}
        <div className="bg-gray-800/50 rounded-lg p-6">
          <h3 className="text-white font-semibold text-lg mb-4">
            Tu Perfil
          </h3>
          
          <div className="space-y-3">
            <div>
              <p className="text-gray-400 text-sm">Usuario</p>
              <p className="text-white font-medium">
                {usuario.nombre} {usuario.apellido}
              </p>
            </div>
            
            <div>
              <p className="text-gray-400 text-sm">Rol</p>
              <p className="text-white font-medium">
                {userConfig.title}
              </p>
            </div>
            
            <div>
              <p className="text-gray-400 text-sm">Área Activa</p>
              <p className="text-white font-medium">
                {areaActiva}
              </p>
            </div>
            
            <div>
              <p className="text-gray-400 text-sm">Descripción</p>
              <p className="text-gray-300 text-sm">
                {userConfig.description}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PayrollDashboard;
