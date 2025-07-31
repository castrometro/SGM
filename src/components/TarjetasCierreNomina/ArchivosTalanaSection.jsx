import { useState } from "react";
import { Database, ChevronDown, ChevronRight, Lock } from "lucide-react";
import LibroRemuneracionesCard from "./LibroRemuneracionesCard";
import MovimientosMesCard from "./MovimientosMesCard";

const ArchivosTalanaSection = ({
  // Props para Libro de Remuneraciones
  libro,
  subiendo,
  onSubirArchivo,
  onVerClasificacion,
  onProcesarLibro,
  onActualizarEstado,
  onEliminarLibro,
  headersSinClasificar,
  mensajeLibro,
  libroListo,
  
  // Props para Movimientos del Mes
  movimientos,
  subiendoMov,
  onSubirMovimientos,
  onActualizarEstadoMovimientos,
  onEliminarMovimientos,
  
  // Props de control
  disabled = false,
  deberiaDetenerPolling = false,
  cierreId,
}) => {
  const [expandido, setExpandido] = useState(true);
  
  // Calcular estado general de la sección
  const estadoLibro = libro?.estado === "procesando" || libro?.estado === "procesado"
    ? libro?.estado
    : libroListo
    ? "clasificado"
    : libro?.estado || "no_subido";
    
  const estadoMovimientos = movimientos?.estado || "pendiente";
  
  // Determinar el estado general: Procesado si ambos están procesados, Pendiente en cualquier otro caso
  const estadoGeneral = (estadoLibro === "procesado" && estadoMovimientos === "procesado") 
    ? "Procesado" 
    : "Pendiente";
  
  const colorEstado = estadoGeneral === "Procesado" ? "text-green-400" : "text-yellow-400";

  return (
    <section className="space-y-6">
      {/* Header de la sección - ahora clicable (solo si no está disabled) */}
      <div 
        className={`flex items-center justify-between p-3 -m-3 rounded-lg transition-colors ${
          disabled 
            ? 'opacity-60 cursor-not-allowed' 
            : 'cursor-pointer hover:bg-gray-800/50'
        }`}
        onClick={() => !disabled && setExpandido(!expandido)}
      >
        <div className="flex items-center gap-3">
          <div className={`flex items-center justify-center w-10 h-10 rounded-lg ${
            disabled ? 'bg-gray-600' : 'bg-blue-600'
          }`}>
            {disabled ? (
              <Lock size={20} className="text-white" />
            ) : (
              <Database size={20} className="text-white" />
            )}
          </div>
          <div>
            <h2 className={`text-xl font-semibold ${disabled ? 'text-gray-400' : 'text-white'}`}>
              Archivos Talana
              {disabled && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  (Bloqueado - Cierre Finalizado)
                </span>
              )}
            </h2>
            <p className="text-gray-400 text-sm">
              {disabled 
                ? 'Los archivos están bloqueados porque el cierre ha sido finalizado'
                : 'Archivos principales del sistema Talana'
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
          <LibroRemuneracionesCard
            estado={estadoLibro}
            archivoNombre={libro?.archivo_nombre}
            subiendo={subiendo}
            onSubirArchivo={onSubirArchivo}
            onVerClasificacion={onVerClasificacion}
            onProcesar={onProcesarLibro}
            onActualizarEstado={onActualizarEstado}
            onEliminarArchivo={onEliminarLibro}
            libroId={libro?.id}
            headersSinClasificar={headersSinClasificar}
            headerClasificados={libro?.header_json?.headers_clasificados || []}
            mensaje={mensajeLibro}
            disabled={disabled || libro?.estado === "procesando"}
            deberiaDetenerPolling={deberiaDetenerPolling}
          />
          
          <MovimientosMesCard
            estado={estadoMovimientos}
            archivoNombre={movimientos?.archivo_nombre}
            subiendo={subiendoMov}
            onSubirArchivo={onSubirMovimientos}
            onActualizarEstado={onActualizarEstadoMovimientos}
            onEliminarArchivo={onEliminarMovimientos}
            disabled={disabled}
            deberiaDetenerPolling={deberiaDetenerPolling}
            cierreId={cierreId}
          />
        </div>
      )}
    </section>
  );
};

export default ArchivosTalanaSection;
