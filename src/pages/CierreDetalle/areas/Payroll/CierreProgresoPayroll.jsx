import React, { useState } from "react";
import TarjetaDetectorDiscrepancias from "./components/TarjetaDetectorDiscrepancias";

const CierreProgresoPayroll = ({ cierre, cliente }) => {
  
  // Estado del orquestador - controla qué tarjetas están completadas
  const [estadoTarjetas, setEstadoTarjetas] = useState({
    detectorDiscrepancias: { 
      completada: false, 
      progreso: 0, 
      bloqueada: false,
      expandida: true,    // Primera tarjeta siempre expandida al inicio
      polling: true       // Polling activo para tarjeta expandida
    }
  });

  // Función para actualizar el estado de una tarjeta
  const actualizarEstadoTarjeta = (nombreTarjeta, nuevoEstado) => {
    console.log(`[ORQUESTADOR] Actualizando tarjeta ${nombreTarjeta}:`, nuevoEstado);
    
    setEstadoTarjetas(prev => ({
      ...prev,
      [nombreTarjeta]: { ...prev[nombreTarjeta], ...nuevoEstado }
    }));
    
    // Lógica para desbloquear siguientes tarjetas
    actualizarBloqueos(nombreTarjeta, nuevoEstado);
  };

  // Función para expandir/colapsar tarjetas
  const toggleTarjeta = (nombreTarjeta) => {
    setEstadoTarjetas(prev => {
      const nuevosEstados = { ...prev };
      const tarjetaActual = nuevosEstados[nombreTarjeta];
      
      // Si la tarjeta está bloqueada, no permitir expansión
      if (tarjetaActual.bloqueada) return prev;
      
      const nuevaExpansion = !tarjetaActual.expandida;
      
      // Actualizar estado de expansión y polling
      nuevosEstados[nombreTarjeta] = {
        ...tarjetaActual,
        expandida: nuevaExpansion,
        polling: nuevaExpansion // Polling solo cuando está expandida
      };
      
      console.log(`[ORQUESTADOR] Toggle ${nombreTarjeta}: expandida=${nuevaExpansion}, polling=${nuevaExpansion}`);
      
      return nuevosEstados;
    });
  };

  // Función para auto-colapsar tarjetas completadas y expandir la siguiente
  const gestionarFlujoAcordeon = (tarjetaCompletada) => {
    console.log(`[ORQUESTADOR] Tarjeta ${tarjetaCompletada} completada - No hay más tarjetas por expandir`);
    // Por ahora solo tenemos una tarjeta, así que no hay flujo adicional
  };

  // Función para manejar los bloqueos entre tarjetas
  const actualizarBloqueos = (tarjetaActualizada, nuevoEstado) => {
    console.log(`[ORQUESTADOR] Verificando bloqueos para ${tarjetaActualizada}:`, nuevoEstado);
    
    if (nuevoEstado.completada) {
      console.log(`[ORQUESTADOR] Tarjeta ${tarjetaActualizada} completada!`);
      
      // Por ahora solo tenemos una tarjeta, así que solo registramos la completación
      // En el futuro aquí se desbloquearían las siguientes tarjetas
      
      // Gestionar flujo acordeón
      gestionarFlujoAcordeon(tarjetaActualizada);
    }
  };

  // Calcular progreso general (solo una tarjeta por ahora)
  const calcularProgresoGeneral = () => {
    return estadoTarjetas.detectorDiscrepancias.progreso;
  };

  // Componente wrapper para tarjetas colapsables
  const TarjetaColapsable = ({ nombreTarjeta, titulo, children, icono }) => {
    const estado = estadoTarjetas[nombreTarjeta];
    const { expandida, completada, bloqueada, progreso } = estado;

    return (
      <div className={`border-2 rounded-lg transition-all duration-300 ${
        completada ? 'border-green-500' : 
        bloqueada ? 'border-gray-600' : 'border-blue-500'
      }`}>
        
        {/* Header siempre visible */}
        <div 
          className={`p-4 cursor-pointer flex items-center justify-between ${
            bloqueada ? 'bg-gray-800' : 'bg-gray-700 hover:bg-gray-600'
          }`}
          onClick={() => !bloqueada && toggleTarjeta(nombreTarjeta)}
        >
          <div className="flex items-center gap-3">
            <div className={`text-xl ${
              completada ? 'text-green-500' : 
              bloqueada ? 'text-gray-500' : 'text-blue-500'
            }`}>
              {icono}
            </div>
            <div>
              <h3 className={`text-lg font-bold ${
                bloqueada ? 'text-gray-500' : 'text-white'
              }`}>
                {titulo}
              </h3>
              <div className="flex items-center gap-2 text-sm">
                <span className={`${
                  completada ? 'text-green-400' : 
                  bloqueada ? 'text-gray-500' : 'text-blue-400'
                }`}>
                  {progreso}% completado
                </span>
                {completada && <span className="text-green-400">✅ Completada</span>}
                {bloqueada && <span className="text-gray-500">🔒 Bloqueada</span>}
              </div>
            </div>
          </div>
          
          {/* Indicador de expansión */}
          {!bloqueada && (
            <div className={`transform transition-transform duration-200 ${
              expandida ? 'rotate-180' : ''
            }`}>
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          )}
        </div>

        {/* Contenido colapsable */}
        <div className={`overflow-hidden transition-all duration-300 ${
          expandida ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'
        }`}>
          <div className="border-t border-gray-600">
            {children}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      
      {/* Header con progreso general */}
      <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-white">Cierre Payroll - {cierre?.periodo || 'Agosto 2025'}</h3>
          <div className="text-right">
            <div className="text-2xl font-bold text-white">{calcularProgresoGeneral()}%</div>
            <div className="text-sm text-gray-400">Progreso General</div>
          </div>
        </div>
        
        <div className="w-full bg-gray-700 rounded-full h-3">
          <div 
            className="bg-blue-500 h-3 rounded-full transition-all duration-500"
            style={{ width: `${calcularProgresoGeneral()}%` }}
          ></div>
        </div>
      </div>

      {/* Tarjetas del workflow con sistema acordeón */}
      <div className="space-y-3">
        
        {/* Tarjeta 1: Detector de Discrepancias */}
        <TarjetaColapsable 
          nombreTarjeta="detectorDiscrepancias"
          titulo="1. Detector de Discrepancias"
          icono="🔍"
        >
          <TarjetaDetectorDiscrepancias
            onEstadoChange={(nuevoEstado) => actualizarEstadoTarjeta('detectorDiscrepancias', nuevoEstado)}
            bloqueada={estadoTarjetas.detectorDiscrepancias.bloqueada}
            completada={estadoTarjetas.detectorDiscrepancias.completada}
            pollingActivo={estadoTarjetas.detectorDiscrepancias.polling}
          />
        </TarjetaColapsable>
        
        {/* Placeholder para futuras tarjetas */}
        <div className="text-center py-8 bg-gray-800 rounded-lg border-2 border-dashed border-gray-600">
          <h4 className="text-lg text-gray-400 mb-2">🚧 Próximas Fases del Workflow</h4>
          <div className="space-y-1 text-sm text-gray-500">
            <div>2. Consolidación de Datos</div>
            <div>3. Gestión de Incidencias</div>
            <div>4. Supervisión Final</div>
          </div>
          <p className="text-xs text-gray-600 mt-3">
            Se implementarán progresivamente según las necesidades del flujo
          </p>
        </div>

      </div>

      {/* Debug info - estado de tarjetas */}
      <div className="bg-gray-900 p-4 rounded-lg">
        <h4 className="text-white font-semibold mb-2">Estado del Workflow (Debug)</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-800 p-3 rounded">
            <div className="text-sm text-gray-300 mb-1">Detector de Discrepancias</div>
            <div className="text-xs space-y-1">
              <div className={`${estadoTarjetas.detectorDiscrepancias.completada ? 'text-green-400' : 'text-gray-500'}`}>
                ✓ Completada: {estadoTarjetas.detectorDiscrepancias.completada ? 'Sí' : 'No'}
              </div>
              <div className="text-blue-400">
                📊 Progreso: {estadoTarjetas.detectorDiscrepancias.progreso}%
              </div>
              <div className={`${estadoTarjetas.detectorDiscrepancias.expandida ? 'text-green-400' : 'text-yellow-400'}`}>
                �️ Expandida: {estadoTarjetas.detectorDiscrepancias.expandida ? 'Sí' : 'No'}
              </div>
              <div className={`${estadoTarjetas.detectorDiscrepancias.polling ? 'text-green-400' : 'text-orange-400'}`}>
                🔄 Polling: {estadoTarjetas.detectorDiscrepancias.polling ? 'Activo' : 'Pausado'}
              </div>
            </div>
          </div>
          <div className="bg-gray-800 p-3 rounded">
            <div className="text-sm text-gray-300 mb-1">Progreso General</div>
            <div className="text-xs space-y-1">
              <div className="text-blue-400">
                📈 Total: {calcularProgresoGeneral()}%
              </div>
              <div className="text-gray-400">
                🏗️ Sistema: Acordeón con Polling Inteligente
              </div>
              <div className="text-gray-400">
                🎯 Estado: Una tarjeta activa
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
};

export default CierreProgresoPayroll;
