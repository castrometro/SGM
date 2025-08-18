import React from "react";

const CierreProgresoPayroll = ({ cierre, cliente }) => {
  
  // Estados del nuevo workflow de payroll
  const ESTADOS_WORKFLOW = {
    'pendiente': { progreso: 5, fase: 'Preparación', descripcion: 'Esperando inicio del proceso' },
    'subiendo_archivos': { progreso: 15, fase: 'Carga de Archivos', descripcion: 'Subiendo archivos Talana y Analista' },
    'verificando_discrepancias': { progreso: 25, fase: 'Verificación', descripcion: 'Comparando archivos y mapeando headers' },
    'discrepancias_pendientes': { progreso: 25, fase: 'Verificación', descripcion: 'Hay discrepancias que resolver', bloqueado: true },
    'consolidando_datos': { progreso: 45, fase: 'Consolidación', descripcion: 'Mapeando conceptos y consolidando información' },
    'detectando_incidencias': { progreso: 65, fase: 'Análisis', descripcion: 'Comparando con período anterior' },
    'incidencias_pendientes': { progreso: 65, fase: 'Análisis', descripcion: 'Incidencias en revisión con supervisor', bloqueado: true },
    'esperando_aprobacion': { progreso: 85, fase: 'Supervisión', descripcion: 'Esperando aprobación final del supervisor', bloqueado: true },
    'generando_informes': { progreso: 95, fase: 'Finalización', descripcion: 'Generando reportes en JSON' },
    'finalizado': { progreso: 100, fase: 'Completado', descripcion: 'Proceso completado exitosamente' }
  };

  // Función para obtener información del estado actual
  const getEstadoInfo = (estado) => {
    return ESTADOS_WORKFLOW[estado] || ESTADOS_WORKFLOW['pendiente'];
  };

  // Función para obtener color según la fase
  const getFaseColor = (estado) => {
    const estadoInfo = getEstadoInfo(estado);
    const colores = {
      'Preparación': 'bg-gray-500',
      'Carga de Archivos': 'bg-blue-500',
      'Verificación': 'bg-yellow-500',
      'Consolidación': 'bg-indigo-500',
      'Análisis': 'bg-orange-500',
      'Supervisión': 'bg-purple-500',
      'Finalización': 'bg-green-500',
      'Completado': 'bg-green-600'
    };
    return colores[estadoInfo.fase] || 'bg-gray-500';
  };

  // Mock data para demostrar el componente (esto vendría del backend)
  const mockData = {
    archivos_subidos: {
      talana: { libro_remuneraciones: true, ausentismos: true, finiquitos: false, ingresos: true, novedades: true },
      analista: { ingresos: true, finiquitos: false, ausentismos: true, novedades: true },
      total_esperados: 9,
      total_subidos: 7
    },
    discrepancias: {
      intentos: 3,
      ultimo_intento: { total: 2, resueltas: 2 },
      historial: [
        { intento: 1, discrepancias: 15, fecha: '2025-08-17 10:30' },
        { intento: 2, discrepancias: 5, fecha: '2025-08-17 14:20' },
        { intento: 3, discrepancias: 2, fecha: '2025-08-18 09:15' }
      ]
    },
    consolidacion: {
      conceptos_mapeados: 8,
      total_conceptos: 8,
      empleados_procesados: 150,
      total_empleados: 150
    },
    incidencias: {
      detectadas: 15,
      resueltas: 8,
      pendientes: 7,
      tolerancia_configurada: 5.5,
      aprobacion_supervisor: false
    },
    logs_recientes: [
      { tipo: 'info', mensaje: 'Archivos Talana subidos correctamente', timestamp: '09:15' },
      { tipo: 'warning', mensaje: '2 discrepancias detectadas en headers', timestamp: '09:20' },
      { tipo: 'success', mensaje: 'Discrepancias resueltas exitosamente', timestamp: '09:25' }
    ]
  };

  const estadoActual = cierre?.estado || 'pendiente';
  const estadoInfo = getEstadoInfo(estadoActual);

  return (
    <div className="space-y-6">
      {/* Header con estado actual */}
      <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-white">Workflow de Cierre Payroll</h3>
          <div className="flex items-center gap-3">
            {estadoInfo.bloqueado && (
              <div className="flex items-center gap-1 bg-red-900 px-2 py-1 rounded text-red-300 text-xs">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                </svg>
                Bloqueado
              </div>
            )}
            <div className={`w-3 h-3 rounded-full ${getFaseColor(estadoActual)}`}></div>
            <span className="text-sm text-gray-300">{estadoInfo.fase}</span>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="bg-gray-700 p-4 rounded">
            <h4 className="text-sm text-gray-400 mb-1">Período</h4>
            <p className="text-lg font-semibold text-white">{cierre?.periodo || 'Agosto 2025'}</p>
          </div>
          <div className="bg-gray-700 p-4 rounded">
            <h4 className="text-sm text-gray-400 mb-1">Total Empleados</h4>
            <p className="text-lg font-semibold text-white">{mockData.consolidacion.total_empleados}</p>
          </div>
          <div className="bg-gray-700 p-4 rounded">
            <h4 className="text-sm text-gray-400 mb-1">Estado Actual</h4>
            <p className="text-lg font-semibold text-white capitalize">{estadoActual.replace('_', ' ')}</p>
          </div>
        </div>

        {/* Descripción del estado actual */}
        <div className="p-3 bg-gray-700 rounded-lg">
          <p className="text-gray-300 text-sm">
            <span className="font-semibold">Descripción:</span> {estadoInfo.descripcion}
          </p>
        </div>
      </div>

      {/* Barra de progreso principal */}
      <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
        <h3 className="text-lg font-bold text-white mb-4">Progreso General del Workflow</h3>
        
        <div className="relative">
          <div className="flex justify-between text-xs text-gray-400 mb-2">
            <span>Preparación</span>
            <span>Verificación</span>
            <span>Consolidación</span>
            <span>Análisis</span>
            <span>Finalización</span>
          </div>
          
          <div className="w-full bg-gray-700 rounded-full h-4">
            <div 
              className={`h-4 rounded-full transition-all duration-500 ${getFaseColor(estadoActual)} ${estadoInfo.bloqueado ? 'animate-pulse' : ''}`}
              style={{ width: `${estadoInfo.progreso}%` }}
            ></div>
          </div>
          
          <div className="mt-2 text-center">
            <span className="text-sm text-gray-400">
              {estadoInfo.progreso}% completado
            </span>
          </div>
        </div>
      </div>

      {/* Fases detalladas del workflow */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* FASE 1: Detector de Discrepancias */}
        <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
          <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <div className={`w-4 h-4 rounded-full ${
              ['subiendo_archivos', 'verificando_discrepancias', 'discrepancias_pendientes'].includes(estadoActual) 
                ? 'bg-blue-500' 
                : estadoInfo.progreso > 25 
                  ? 'bg-green-500' 
                  : 'bg-gray-500'
            }`}></div>
            Fase 1: Detector de Discrepancias
          </h4>
          
          {/* Estado de archivos */}
          <div className="space-y-3">
            <div>
              <h5 className="text-sm font-semibold text-gray-300 mb-2">Archivos Subidos</h5>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-gray-700 p-2 rounded">
                  <span className="text-gray-400">Talana:</span>
                  <span className="text-white ml-1">4/5</span>
                </div>
                <div className="bg-gray-700 p-2 rounded">
                  <span className="text-gray-400">Analista:</span>
                  <span className="text-white ml-1">3/4</span>
                </div>
              </div>
            </div>
            
            <div>
              <h5 className="text-sm font-semibold text-gray-300 mb-2">Historial de Discrepancias</h5>
              <div className="space-y-1">
                {mockData.discrepancias.historial.slice(-2).map((intento, idx) => (
                  <div key={idx} className="bg-gray-700 p-2 rounded text-xs flex justify-between">
                    <span className="text-gray-400">Intento {intento.intento}:</span>
                    <span className={`${intento.discrepancias === 0 ? 'text-green-400' : 'text-yellow-400'}`}>
                      {intento.discrepancias} discrepancias
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* FASE 2: Consolidación */}
        <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
          <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <div className={`w-4 h-4 rounded-full ${
              estadoActual === 'consolidando_datos' 
                ? 'bg-indigo-500' 
                : estadoInfo.progreso > 45 
                  ? 'bg-green-500' 
                  : 'bg-gray-500'
            }`}></div>
            Fase 2: Consolidación de Datos
          </h4>
          
          <div className="space-y-3">
            <div>
              <h5 className="text-sm font-semibold text-gray-300 mb-2">Mapeo de Conceptos</h5>
              <div className="bg-gray-700 p-3 rounded">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Conceptos Mapeados:</span>
                  <span className="text-white">{mockData.consolidacion.conceptos_mapeados}/{mockData.consolidacion.total_conceptos}</span>
                </div>
                <div className="w-full bg-gray-600 rounded-full h-2 mt-2">
                  <div 
                    className="bg-indigo-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${(mockData.consolidacion.conceptos_mapeados / mockData.consolidacion.total_conceptos) * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
            
            <div>
              <h5 className="text-sm font-semibold text-gray-300 mb-2">Empleados Procesados</h5>
              <div className="bg-gray-700 p-2 rounded text-sm">
                <span className="text-gray-400">Procesados:</span>
                <span className="text-white ml-1">{mockData.consolidacion.empleados_procesados}/{mockData.consolidacion.total_empleados}</span>
              </div>
            </div>
          </div>
        </div>

        {/* FASE 3: Detección de Incidencias */}
        <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
          <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <div className={`w-4 h-4 rounded-full ${
              ['detectando_incidencias', 'incidencias_pendientes'].includes(estadoActual)
                ? 'bg-orange-500' 
                : estadoInfo.progreso > 65 
                  ? 'bg-green-500' 
                  : 'bg-gray-500'
            }`}></div>
            Fase 3: Gestión de Incidencias
          </h4>
          
          <div className="space-y-3">
            <div>
              <h5 className="text-sm font-semibold text-gray-300 mb-2">Configuración</h5>
              <div className="bg-gray-700 p-2 rounded text-sm">
                <span className="text-gray-400">Tolerancia:</span>
                <span className="text-white ml-1">{mockData.incidencias.tolerancia_configurada}%</span>
              </div>
            </div>
            
            <div>
              <h5 className="text-sm font-semibold text-gray-300 mb-2">Estado de Incidencias</h5>
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div className="bg-red-900 p-2 rounded text-center">
                  <div className="text-red-300 font-semibold">{mockData.incidencias.detectadas}</div>
                  <div className="text-red-400">Detectadas</div>
                </div>
                <div className="bg-green-900 p-2 rounded text-center">
                  <div className="text-green-300 font-semibold">{mockData.incidencias.resueltas}</div>
                  <div className="text-green-400">Resueltas</div>
                </div>
                <div className="bg-yellow-900 p-2 rounded text-center">
                  <div className="text-yellow-300 font-semibold">{mockData.incidencias.pendientes}</div>
                  <div className="text-yellow-400">Pendientes</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* FASE 4: Supervisión y Finalización */}
        <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
          <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <div className={`w-4 h-4 rounded-full ${
              ['esperando_aprobacion', 'generando_informes'].includes(estadoActual)
                ? 'bg-purple-500' 
                : estadoActual === 'finalizado'
                  ? 'bg-green-500' 
                  : 'bg-gray-500'
            }`}></div>
            Fase 4: Supervisión y Finalización
          </h4>
          
          <div className="space-y-3">
            <div>
              <h5 className="text-sm font-semibold text-gray-300 mb-2">Estado de Aprobación</h5>
              <div className={`p-3 rounded ${mockData.incidencias.aprobacion_supervisor ? 'bg-green-900' : 'bg-yellow-900'}`}>
                <div className="flex items-center gap-2">
                  {mockData.incidencias.aprobacion_supervisor ? (
                    <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  )}
                  <span className={`text-sm ${mockData.incidencias.aprobacion_supervisor ? 'text-green-300' : 'text-yellow-300'}`}>
                    {mockData.incidencias.aprobacion_supervisor ? 'Aprobado por Supervisor' : 'Esperando Aprobación'}
                  </span>
                </div>
              </div>
            </div>
            
            <div>
              <h5 className="text-sm font-semibold text-gray-300 mb-2">Generación de Informes</h5>
              <div className="bg-gray-700 p-2 rounded text-sm">
                <span className="text-gray-400">Estado:</span>
                <span className="text-white ml-1">
                  {estadoActual === 'finalizado' ? 'Completado' : 
                   estadoActual === 'generando_informes' ? 'En progreso' : 
                   'Pendiente'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Log de actividades recientes */}
      <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
        <h4 className="text-lg font-bold text-white mb-4">Actividades Recientes</h4>
        <div className="space-y-2">
          {mockData.logs_recientes.map((log, idx) => (
            <div key={idx} className="flex items-center gap-3 p-3 bg-gray-700 rounded">
              <div className={`w-2 h-2 rounded-full ${
                log.tipo === 'success' ? 'bg-green-500' :
                log.tipo === 'warning' ? 'bg-yellow-500' :
                'bg-blue-500'
              }`}></div>
              <span className="text-gray-300 text-sm flex-1">{log.mensaje}</span>
              <span className="text-gray-500 text-xs">{log.timestamp}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Panel de información del workflow */}
      <div className="bg-blue-900 p-4 rounded-lg border border-blue-700">
        <div className="flex items-center gap-2 mb-2">
          <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h4 className="text-blue-400 font-semibold">Información del Workflow</h4>
        </div>
        <p className="text-blue-200 text-sm">
          El workflow de cierre de payroll incluye: verificación de discrepancias entre archivos Talana y Analista, 
          consolidación de datos con mapeo de conceptos, detección de incidencias comparando con período anterior, 
          y supervisión con aprobación final antes de generar los informes en formato JSON.
        </p>
      </div>
    </div>
  );
};

export default CierreProgresoPayroll;
