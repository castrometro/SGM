import EstadoBadge from "../../../../components/EstadoBadge";
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { finalizarCierre, actualizarEstadoCierre, obtenerProgresoTarea } from '../../../../api/contabilidad';
import { actualizarEstadoCierreNomina } from '../api/cierreDetalle.api';

const CierreInfoBar = ({ cierre, cliente, onCierreActualizado, tipoModulo = "contabilidad" }) => {
  const navigate = useNavigate();
  const [actualizandoEstado, setActualizandoEstado] = useState(false);
  const [finalizando, setFinalizando] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [progreso, setProgreso] = useState(null);
  const intervalRef = useRef(null);

  const manejarActualizarEstado = async () => {
    setActualizandoEstado(true);
    try {
      let data;
      if (tipoModulo === "nomina") {
        data = await actualizarEstadoCierreNomina(cierre.id);
      } else {
        data = await actualizarEstadoCierre(cierre.id);
      }
      
      if (onCierreActualizado) {
        onCierreActualizado(data.cierre);
      }
      // Refresh de la página como fallback
      window.location.reload();
    } catch (error) {
      console.error('Error al actualizar estado del cierre:', error);
    } finally {
      setActualizandoEstado(false);
    }
  };

  const consultarProgreso = async (taskId) => {
    try {
      const data = await obtenerProgresoTarea(taskId);
      setProgreso(data);
      
      // Si la tarea terminó (éxito o error), detener el polling
      if (data.estado === 'SUCCESS' || data.estado === 'FAILURE') {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        
        if (data.estado === 'SUCCESS') {
          // Actualizar el estado del cierre
          if (onCierreActualizado) {
            onCierreActualizado({ ...cierre, estado: 'finalizado' });
          }
          alert('¡Cierre finalizado exitosamente! Los reportes han sido generados.');
          setTimeout(() => window.location.reload(), 1500);
        } else {
          alert(`Error en la finalización: ${data.error || 'Error desconocido'}`);
          // Revertir estado
          if (onCierreActualizado) {
            onCierreActualizado({ ...cierre, estado: 'sin_incidencias' });
          }
        }
        
        setFinalizando(false);
        setTaskId(null);
      }
    } catch (error) {
      console.error('Error consultando progreso:', error);
    }
  };

  const iniciarFinalizacion = async () => {
    if (!window.confirm('¿Está seguro de que desea finalizar este cierre y generar los reportes? Este proceso puede tomar varios minutos.')) {
      return;
    }

    setFinalizando(true);
    setProgreso(null);
    
    try {
      const data = await finalizarCierre(cierre.id);
      
      if (data.success) {
        console.log('🚀 Finalización iniciada:', data);
        
        // Guardar el task_id y actualizar estado del cierre
        setTaskId(data.task_id);
        if (onCierreActualizado) {
          onCierreActualizado({ ...cierre, estado: 'generando_reportes' });
        }
        
        // Iniciar polling del progreso cada 2 segundos
        intervalRef.current = setInterval(() => {
          consultarProgreso(data.task_id);
        }, 2000);
        
        // Primera consulta inmediata
        setTimeout(() => consultarProgreso(data.task_id), 500);
        
      } else {
        alert(`Error: ${data.error}`);
        setFinalizando(false);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error de conexión al servidor');
      setFinalizando(false);
    }
  };

  // Limpiar el interval al desmontar el componente
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return (
    <div className="bg-gray-800 px-8 py-6 rounded-xl shadow flex flex-wrap items-center gap-6 mb-10 w-full">
      {/* Nombre + bilingüe */}
      <div className="flex items-center gap-2">
        <span className="text-2xl font-bold text-white">{cliente?.nombre || "Cliente desconocido"}</span>
        {cliente?.bilingue && (
          <span className="bg-blue-600 text-white text-xs px-2 py-1 rounded-full shadow font-semibold flex items-center gap-1">
            <svg className="inline-block w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2m0 4v2m0 4v2m0 4v2m8-10h-2m-4 0H8m-4 0H2m18 0c0 4.418-3.582 8-8 8s-8-3.582-8-8 3.582-8 8-8 8 3.582 8 8z" />
            </svg>
            Bilingüe
          </span>
        )}
      </div>
      {/* RUT */}
      <div className="text-gray-300 text-base">
        <span className="font-bold">RUT:</span> {cliente?.rut}
      </div>
      {/* Industria */}
      <div className="text-gray-300 text-base">
        <span className="font-bold">Industria:</span> {cliente?.industria_nombre || "—"}
      </div>
      {/* Periodo */}
      <div className="text-gray-300 text-base">
        <span className="font-bold">Periodo:</span> <span className="text-white font-bold">{cierre?.periodo || "—"}</span>
      </div>
      {/* Estado */}
      <div className="flex items-center gap-2">
        <span className="font-bold text-gray-300">Estado:</span>
        <EstadoBadge estado={cierre?.estado} size="md" />
        {/* Indicador técnico de consolidación (solo nómina) */}
        {tipoModulo === "nomina" && cierre?.estado_consolidacion === 'consolidando' && (
          <span className="ml-2 inline-flex items-center gap-2 text-yellow-300 text-sm bg-yellow-900/40 border border-yellow-700 px-2 py-1 rounded-full">
            <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
            </svg>
            Consolidando datos...
          </span>
        )}
      </div>

      {/* Botón Actualizar Estado */}
      <div className="flex items-center gap-3">
        

        {/* Botones para estados permitidos del libro - Solo para contabilidad */}
        {tipoModulo === "contabilidad" && ['sin_incidencias', 'generando_reportes', 'finalizado'].includes(cierre?.estado) && (
          <>
            {/* Botón Ver Libro */}
            <button
              onClick={() => navigate(`/menu/cierres/${cierre.id}/libro`)}
              className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-semibold text-sm transition-colors flex items-center gap-2"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Ver Libro
            </button>
          </>
        )}

        {/* Botones para visualización de datos - Solo para nómina */}
        {tipoModulo === "nomina" && ['datos_consolidados', 'con_incidencias', 'sin_incidencias', 'incidencias_resueltas', 'finalizado'].includes(cierre?.estado) && (
          <>
            {/* Botón Ver Libro de Remuneraciones */}
            <button
              onClick={() => navigate(`/menu/cierres-nomina/${cierre.id}/libro-remuneraciones`)}
              className="bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded-lg font-semibold text-sm transition-colors flex items-center gap-2"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Ver Libro de Remuneraciones
            </button>

            {/* Botón Ver Movimientos del Mes */}
            <button
              onClick={() => navigate(`/menu/cierres-nomina/${cierre.id}/movimientos`)}
              className="bg-amber-600 hover:bg-amber-700 text-white px-4 py-2 rounded-lg font-semibold text-sm transition-colors flex items-center gap-2"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
              Ver Movimientos del Mes
            </button>
          </>
        )}

        {/* Botón Finalizar Cierre solo para sin_incidencias en contabilidad */}
        {tipoModulo === "contabilidad" && cierre?.estado === 'sin_incidencias' && (
          <>
            {/* Botón Finalizar Cierre */}
            <button
              onClick={iniciarFinalizacion}
              disabled={finalizando}
              className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-6 py-2 rounded-lg font-bold text-sm transition-colors flex items-center gap-2 shadow-lg"
            >
              {finalizando ? (
                <>
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Finalizando...
                </>
              ) : (
                <>
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Finalizar Cierre y Generar Reportes
                </>
              )}
            </button>
          </>
        )}

        {/* Indicador de estado generando reportes con progreso - Solo para contabilidad */}
        {tipoModulo === "contabilidad" && (cierre?.estado === 'generando_reportes' || finalizando) && (
          <div className="bg-yellow-600 text-white px-4 py-2 rounded-lg font-semibold text-sm flex items-center gap-2 min-w-[300px]">
            <svg className="animate-spin h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <div className="flex flex-col">
              <span>Generando Reportes...</span>
              {progreso && (
                <div className="text-xs opacity-90 mt-1">
                  {progreso.estado === 'PENDING' && 'Iniciando proceso...'}
                  {progreso.estado === 'PROGRESS' && progreso.progreso && (
                    <>
                      <div>{progreso.progreso.descripcion || 'Procesando...'}</div>
                      {progreso.progreso.porcentaje && (
                        <div className="flex items-center gap-2 mt-1">
                          <div className="bg-yellow-800 rounded-full h-1 flex-1">
                            <div 
                              className="bg-white h-1 rounded-full transition-all duration-300"
                              style={{ width: `${progreso.progreso.porcentaje}%` }}
                            ></div>
                          </div>
                          <span className="text-xs">{progreso.progreso.porcentaje}%</span>
                        </div>
                      )}
                    </>
                  )}
                  {taskId && (
                    <div className="text-xs opacity-75 mt-1">
                      Task ID: {taskId.substring(0, 8)}...
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Indicador de cierre finalizado - Solo para contabilidad */}
        {tipoModulo === "contabilidad" && cierre?.estado === 'finalizado' && (
          <>
            <div className="bg-green-600 text-white px-4 py-2 rounded-lg font-semibold text-sm flex items-center gap-2">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Cierre Finalizado
            </div>
            
            {/* Botón Ver Dashboard Contable */}
            <button
              onClick={() => {
                const streamlitUrl = `http://172.17.11.18:8502/?cliente_id=${cliente?.id || cierre?.cliente_id}`;
                window.open(streamlitUrl, '_blank');
              }}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg font-semibold text-sm transition-colors flex items-center gap-2"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Ver Dashboard Contable
            </button>
          </>
        )}
      </div>
      {/* Link ficha cliente */}
      {cliente && (
        <div>
          <a
            href={`/menu/clientes/${cliente.id}`}
            className="!text-white text-base underline font-semibold"
          >
            Ver ficha del cliente
          </a>
        </div>
      )}
    </div>
  );
};

export default CierreInfoBar;
