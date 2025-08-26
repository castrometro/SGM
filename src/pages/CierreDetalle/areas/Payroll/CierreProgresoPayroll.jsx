import React, { useState } from "react";
import TarjetaDetectorDiscrepancias from "./components/TarjetaDetectorDiscrepancias";

const CierreProgresoPayroll = ({ cierre, cliente }) => {
  
  // Estado simple: qué tarjeta está activa (expandida)
  const [tarjetaActiva, setTarjetaActiva] = useState('detectorDiscrepancias');
  
  // Estados de completitud de cada tarjeta
  const [estadosCompletitud, setEstadosCompletitud] = useState({
    detectorDiscrepancias: false,
    consolidacionDatos: false,
    gestionIncidencias: false,
    supervisionFinal: false
  });

  // Función para cambiar qué tarjeta está activa
  const activarTarjeta = (nombreTarjeta) => {
    // Solo permitir activar si no está bloqueada
    if (esTarjetaBloqueada(nombreTarjeta)) return;
    
    setTarjetaActiva(nombreTarjeta);
  };

  // Función para marcar una tarjeta como completada
  const marcarCompletada = (nombreTarjeta) => {
    setEstadosCompletitud(prev => ({
      ...prev,
      [nombreTarjeta]: true
    }));
    
    // Auto-activar la siguiente tarjeta no completada
    const siguienteTarjeta = obtenerSiguienteTarjeta(nombreTarjeta);
    if (siguienteTarjeta) {
      setTarjetaActiva(siguienteTarjeta);
    }
  };

  // Función para determinar si una tarjeta está bloqueada
  const esTarjetaBloqueada = (nombreTarjeta) => {
    const orden = ['detectorDiscrepancias', 'consolidacionDatos', 'gestionIncidencias', 'supervisionFinal'];
    const indice = orden.indexOf(nombreTarjeta);
    
    // La primera tarjeta nunca está bloqueada
    if (indice === 0) return false;
    
    // Las demás están bloqueadas si la anterior no está completada
    return !estadosCompletitud[orden[indice - 1]];
  };

  // Función para obtener la siguiente tarjeta en el flujo
  const obtenerSiguienteTarjeta = (tarjetaActual) => {
    const orden = ['detectorDiscrepancias', 'consolidacionDatos', 'gestionIncidencias', 'supervisionFinal'];
    const indiceActual = orden.indexOf(tarjetaActual);
    
    for (let i = indiceActual + 1; i < orden.length; i++) {
      if (!estadosCompletitud[orden[i]]) {
        return orden[i];
      }
    }
    
    return null; // Todas las siguientes están completadas
  };

  // Componente wrapper para tarjetas colapsables
  const TarjetaColapsable = ({ nombreTarjeta, titulo, children, icono }) => {
    const activa = tarjetaActiva === nombreTarjeta;
    const completada = estadosCompletitud[nombreTarjeta];
    const bloqueada = esTarjetaBloqueada(nombreTarjeta);

    return (
      <div className={`border-2 rounded-lg transition-all duration-300 ${
        completada ? 'border-green-500' : 
        bloqueada ? 'border-gray-600' : 
        activa ? 'border-blue-500' : 'border-gray-700'
      }`}>
        
        {/* Header siempre visible */}
        <div 
          className={`p-4 cursor-pointer flex items-center justify-between ${
            bloqueada ? 'bg-gray-800' : 
            activa ? 'bg-gray-700' : 'bg-gray-800 hover:bg-gray-700'
          }`}
          onClick={() => !bloqueada && activarTarjeta(nombreTarjeta)}
        >
          <div className="flex items-center gap-3">
            <div className={`text-xl ${
              completada ? 'text-green-500' : 
              bloqueada ? 'text-gray-500' : 
              activa ? 'text-blue-500' : 'text-gray-400'
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
                {completada && <span className="text-green-400">✅ Completada</span>}
                {bloqueada && <span className="text-gray-500">🔒 Bloqueada</span>}
                {activa && !completada && <span className="text-blue-400">⚡ Activa</span>}
              </div>
            </div>
          </div>
          
          {/* Indicador de expansión */}
          {!bloqueada && (
            <div className={`transform transition-transform duration-200 ${
              activa ? 'rotate-180' : ''
            }`}>
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          )}
        </div>

        {/* Contenido colapsable */}
        <div className={`overflow-hidden transition-all duration-300 ${
          activa ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'
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
      {/* Tarjetas del workflow con sistema acordeón */}
      <div className="space-y-3">
        
        {/* Tarjeta 1: Detector de Discrepancias */}
        <TarjetaColapsable 
          nombreTarjeta="detectorDiscrepancias"
          titulo="1. Detector de Discrepancias"
          icono="🔍"
        >
          <TarjetaDetectorDiscrepancias
            activa={tarjetaActiva === 'detectorDiscrepancias'}
            onCompletada={() => marcarCompletada('detectorDiscrepancias')}
            cierre={cierre}
            cliente={cliente}
          />
        </TarjetaColapsable>
        
        {/* Tarjeta 2: Consolidación de Datos */}
        <TarjetaColapsable 
          nombreTarjeta="consolidacionDatos"
          titulo="2. Consolidación de Datos"
          icono="📊"
        >
          <div className="p-4 text-center text-gray-400">
            <div className="text-4xl mb-2">🚧</div>
            <h4 className="font-semibold">En desarrollo</h4>
            <p className="text-sm">Se activará cuando se complete la fase anterior</p>
          </div>
        </TarjetaColapsable>
        
        {/* Tarjeta 3: Gestión de Incidencias */}
        <TarjetaColapsable 
          nombreTarjeta="gestionIncidencias"
          titulo="3. Gestión de Incidencias"
          icono="⚠️"
        >
          <div className="p-4 text-center text-gray-400">
            <div className="text-4xl mb-2">🚧</div>
            <h4 className="font-semibold">En desarrollo</h4>
            <p className="text-sm">Se activará cuando se complete la fase anterior</p>
          </div>
        </TarjetaColapsable>
        
        {/* Tarjeta 4: Supervisión Final */}
        <TarjetaColapsable 
          nombreTarjeta="supervisionFinal"
          titulo="4. Supervisión Final"
          icono="✅"
        >
          <div className="p-4 text-center text-gray-400">
            <div className="text-4xl mb-2">🚧</div>
            <h4 className="font-semibold">En desarrollo</h4>
            <p className="text-sm">Se activará cuando se complete la fase anterior</p>
          </div>
        </TarjetaColapsable>

      </div>

      {/* Estado del workflow (simplificado) */}
      <div className="bg-gray-900 p-4 rounded-lg">
        <h4 className="text-white font-semibold mb-2">Estado del Workflow</h4>
        <div className="flex flex-wrap gap-2">
          {Object.entries(estadosCompletitud).map(([nombre, completada]) => {
            const activa = tarjetaActiva === nombre;
            const bloqueada = esTarjetaBloqueada(nombre);
            
            return (
              <div 
                key={nombre} 
                className={`px-3 py-1 rounded-full text-xs font-medium ${
                  completada ? 'bg-green-600 text-white' :
                  bloqueada ? 'bg-gray-600 text-gray-400' :
                  activa ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300'
                }`}
              >
                {completada ? '✅' : bloqueada ? '🔒' : activa ? '⚡' : '⏳'} 
                {nombre.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
              </div>
            );
          })}
        </div>
      </div>

    </div>
  );
};

export default CierreProgresoPayroll;
