import React, { useState } from 'react';
import ArchivosTalanaSection_v2 from './ArchivosTalanaSection/ArchivosTalanaSection_v2';
import ArchivosAnalistaSection_v2 from './ArchivosAnalistaSection/ArchivosAnalistaSection_v2';

const CierreProgresoNomina_v2 = ({ cierre, cliente, onCierreActualizado, className }) => {
  // 🎯 Estados para manejar acordeón (solo una sección expandida a la vez)
  const [seccionExpandida, setSeccionExpandida] = useState('archivosTalana');
  
  // 🎯 Estados para tracking de progreso de las secciones
  const [estadosSeccion, setEstadosSeccion] = useState({
    archivosTalana: 'pendiente',
    archivosAnalista: 'pendiente', 
    verificadorDatos: 'pendiente',
    incidencias: 'pendiente'
  });

  // 🎯 Función para manejar expansión de acordeón
  const manejarExpansionSeccion = (nombreSeccion) => {
    setSeccionExpandida(prev => prev === nombreSeccion ? null : nombreSeccion);
  };

  // 🎯 Determinar qué secciones mostrar según el estado del cierre
  const deberiaRenderizarSeccion = (seccion) => {
    const estado = cierre?.estado;
    
    switch (seccion) {
      case 'archivosTalana':
        // Mostrar en estados iniciales hasta consolidación
        return ['pendiente', 'archivos_completos', 'verificacion_datos'].includes(estado);
        
      case 'archivosAnalista':
        // Mostrar junto con Talana en estados iniciales
        return ['pendiente', 'archivos_completos', 'verificacion_datos'].includes(estado);
        
      case 'verificadorDatos':
        // Mostrar cuando los archivos están listos
        return ['archivos_completos', 'verificacion_datos', 'con_discrepancias', 'verificado_sin_discrepancias'].includes(estado);
        
      case 'incidencias':
        // Mostrar desde consolidación en adelante
        return ['datos_consolidados', 'con_incidencias', 'incidencias_resueltas'].includes(estado);
        
      default:
        return false;
    }
  };

  // 🎯 Handlers de estado de las secciones
  const handleEstadoChange = (seccion, nuevoEstado) => {
    console.log(`📊 [CierreProgresoNomina_v2] ${seccion}: ${nuevoEstado}`);
    setEstadosSeccion(prev => ({
      ...prev,
      [seccion]: nuevoEstado
    }));
  };
  // Validación básica de props
  if (!cierre || !cliente) {
    return (
      <div className="text-white text-center py-6">
        Cargando datos de cierre de nómina...
      </div>
    );
  }

  return (
    <div className={`w-full max-w-none space-y-6 ${className || ''}`}>
      {/* 🎯 SECCIÓN 1: Archivos Talana - Solo si debe renderizarse */}
      {deberiaRenderizarSeccion('archivosTalana') && (
        <ArchivosTalanaSection_v2
          cierreId={cierre.id}
          cliente={cliente}
          disabled={false} // Por ahora siempre habilitado cuando se renderiza
          onEstadoChange={(estado) => handleEstadoChange('archivosTalana', estado)}
          expandido={seccionExpandida === 'archivosTalana'}
          onToggleExpansion={() => manejarExpansionSeccion('archivosTalana')}
        />
      )}

      {/* 🎯 SECCIÓN 2: Archivos del Analista - Solo si debe renderizarse */}
      {deberiaRenderizarSeccion('archivosAnalista') && (
        <ArchivosAnalistaSection_v2
          cierreId={cierre.id}
          cliente={cliente}
          disabled={false} // Por ahora siempre habilitado cuando se renderiza
          onEstadoChange={(estado) => handleEstadoChange('archivosAnalista', estado)}
          expandido={seccionExpandida === 'archivosAnalista'}
          onToggleExpansion={() => manejarExpansionSeccion('archivosAnalista')}
        />
      )}
    </div>
  );
};

export default CierreProgresoNomina_v2;