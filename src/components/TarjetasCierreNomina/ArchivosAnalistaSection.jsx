import { useState } from "react";
import { Users, ChevronDown, ChevronRight, Lock } from "lucide-react";
import IngresosCard from "./IngresosCard";
import FiniquitosCard from "./FiniquitosCard";
import AusentismosCard from "./AusentismosCard";
import NovedadesCard from "./NovedadesCard";

const ArchivosAnalistaSection = ({
  // Props para Ingresos
  ingresos,
  subiendoIngresos,
  onSubirIngresos,
  onActualizarEstadoIngresos,
  onEliminarIngresos,
  
  // Props para Finiquitos
  finiquitos,
  subiendoFiniquitos,
  onSubirFiniquitos,
  onActualizarEstadoFiniquitos,
  onEliminarFiniquitos,
  
  // Props para Ausentismos
  ausentismos,
  subiendoAusentismos,
  onSubirAusentismos,
  onActualizarEstadoAusentismos,
  onEliminarAusentismos,
  
  // Props para Novedades
  novedades,
  subiendoNovedades,
  onSubirNovedades,
  onVerClasificacionNovedades,
  onProcesarNovedades,
  onActualizarEstadoNovedades,
  onEliminarNovedades,
  headersSinClasificarNovedades,
  mensajeNovedades,
  novedadesListo,
  
  // Props de control
  disabled = false,
  deberiaDetenerPolling = false,
  cierreId,
  
  // Props para acordeón
  expandido = true,
  onToggleExpansion,
}) => {
  
  // Calcular estado general de la sección
  const estadoIngresos = ingresos?.estado || "no_subido";
  const estadoFiniquitos = finiquitos?.estado || "no_subido";
  const estadoAusentismos = ausentismos?.estado || "no_subido";
  
  const hayArchivoNovedades = Boolean(novedades?.id || novedades?.archivo_nombre);
  const estadoNovedades = (novedades?.estado === "procesando" || novedades?.estado === "procesado")
    ? novedades?.estado
    : (novedadesListo && hayArchivoNovedades)
    ? "clasificado"
    : (novedades?.estado || "no_subido");
  
  // Determinar el estado general: Procesado si TODOS están procesados, Pendiente en cualquier otro caso
  const todosArchivosProcessed = [estadoIngresos, estadoFiniquitos, estadoAusentismos, estadoNovedades]
    .every(estado => estado === "procesado");
  
  const estadoGeneral = todosArchivosProcessed ? "Procesado" : "Pendiente";
  const colorEstado = estadoGeneral === "Procesado" ? "text-green-400" : "text-yellow-400";

  return (
    <section className="space-y-6">
      {/* Header de la sección - clicable (solo si no está disabled) */}
      <div 
        className={`flex items-center justify-between p-3 -m-3 rounded-lg transition-colors ${
          disabled 
            ? 'opacity-60 cursor-not-allowed' 
            : 'cursor-pointer hover:bg-gray-800/50'
        }`}
        onClick={() => !disabled && onToggleExpansion && onToggleExpansion()}
      >
        <div className="flex items-center gap-3">
          <div className={`flex items-center justify-center w-10 h-10 rounded-lg ${
            disabled ? 'bg-gray-600' : 'bg-purple-600'
          }`}>
            {disabled ? (
              <Lock size={20} className="text-white" />
            ) : (
              <Users size={20} className="text-white" />
            )}
          </div>
          <div>
            <h2 className={`text-xl font-semibold ${disabled ? 'text-gray-400' : 'text-white'}`}>
              Archivos del Analista
              {disabled && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  (Bloqueado - Cierre Finalizado)
                </span>
              )}
            </h2>
            <p className="text-gray-400 text-sm">
              {disabled 
                ? 'Los archivos están bloqueados porque el cierre ha sido finalizado'
                : 'Archivos complementarios procesados por el analista'
              }
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {!expandido && !disabled && (
            <span className={`text-sm font-medium ${colorEstado}`}>
              {estadoGeneral}
            </span>
          )}
          {disabled ? (
            <span className="text-sm font-medium text-gray-500">Bloqueado</span>
          ) : (
            expandido ? (
              <ChevronDown size={20} className="text-gray-400" />
            ) : (
              <ChevronRight size={20} className="text-gray-400" />
            )
          )}
        </div>
      </div>
      
      {/* Grid de tarjetas - solo se muestra cuando está expandido y no disabled */}
      {expandido && !disabled && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Primera fila: Ingresos y Finiquitos */}
          <IngresosCard
            estado={estadoIngresos}
            archivoNombre={ingresos?.archivo ? ingresos.archivo.split('/').pop() : null}
            subiendo={subiendoIngresos}
            onSubirArchivo={onSubirIngresos}
            onActualizarEstado={onActualizarEstadoIngresos}
            onEliminarArchivo={onEliminarIngresos}
            disabled={disabled}
            deberiaDetenerPolling={deberiaDetenerPolling}
            cierreId={cierreId}
          />
          
          <FiniquitosCard
            estado={estadoFiniquitos}
            archivoNombre={finiquitos?.archivo ? finiquitos.archivo.split('/').pop() : null}
            subiendo={subiendoFiniquitos}
            onSubirArchivo={onSubirFiniquitos}
            onActualizarEstado={onActualizarEstadoFiniquitos}
            onEliminarArchivo={onEliminarFiniquitos}
            disabled={disabled}
            deberiaDetenerPolling={deberiaDetenerPolling}
            cierreId={cierreId}
          />
          
          {/* Segunda fila: Ausentismos y Novedades */}
          <AusentismosCard
            estado={estadoAusentismos}
            archivoNombre={ausentismos?.archivo ? ausentismos.archivo.split('/').pop() : null}
            subiendo={subiendoAusentismos}
            onSubirArchivo={onSubirAusentismos}
            onActualizarEstado={onActualizarEstadoAusentismos}
            onEliminarArchivo={onEliminarAusentismos}
            disabled={disabled}
            deberiaDetenerPolling={deberiaDetenerPolling}
            cierreId={cierreId}
          />
          
          <NovedadesCard
            estado={estadoNovedades}
            archivoNombre={novedades?.archivo_nombre}
            subiendo={subiendoNovedades}
            onSubirArchivo={onSubirNovedades}
            onVerClasificacion={onVerClasificacionNovedades}
            onProcesar={onProcesarNovedades}
            onActualizarEstado={onActualizarEstadoNovedades}
            onEliminarArchivo={onEliminarNovedades}
            novedadesId={novedades?.id}
            cierreId={cierreId}
            headersSinClasificar={headersSinClasificarNovedades}
            headerClasificados={novedades?.header_json?.headers_clasificados || []}
            mensaje={mensajeNovedades}
            disabled={disabled || novedades?.estado === "procesando"}
            deberiaDetenerPolling={deberiaDetenerPolling}
          />
        </div>
      )}
    </section>
  );
};

export default ArchivosAnalistaSection;
