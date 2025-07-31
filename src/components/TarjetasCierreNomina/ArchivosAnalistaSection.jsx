import { useState, useEffect, useRef } from "react";
import { UserCheck, ChevronDown, ChevronRight, Lock } from "lucide-react";
import ArchivosAnalistaContainer from "./ArchivosAnalista/ArchivosAnalistaContainer";
import { actualizarEstadoCierreNomina } from "../../api/nomina";

const ArchivosAnalistaSection = ({
  cierreId,
  cliente,
  cierre, // Agregar el objeto cierre para verificar su estado
  disabled = false,
  onCierreActualizado,
  onEstadoChange, // 🎯 Nuevo callback para reportar estado
  deberiaDetenerPolling = false,
}) => {
  const [expandido, setExpandido] = useState(true);
  const [estadoArchivos, setEstadoArchivos] = useState({});
  const [estadoCompletadoAnteriormente, setEstadoCompletadoAnteriormente] = useState(false);
  const procesandoCambioEstado = useRef(false);

  // Lista de archivos requeridos
  const archivosRequeridos = ['finiquitos', 'incidencias', 'ingresos', 'novedades'];

  // Función para determinar el estado general de la sección
  const calcularEstadoGeneral = () => {
    const estados = Object.values(estadoArchivos);
    if (estados.length === 0) return "Pendiente";
    
    // Si todos están procesados, la sección está procesada
    const todosProcessados = estados.every(estado => estado === "procesado");
    return todosProcessados ? "Procesado" : "Pendiente";
  };

  // Función para verificar si todos los archivos están procesados
  const verificarArchivosCompletos = () => {
    // Verificar que tenemos todos los archivos requeridos
    const tieneEstadosTodos = archivosRequeridos.every(tipo => 
      tipo in estadoArchivos
    );
    
    if (!tieneEstadosTodos) return false;

    // Verificar que todos están procesados
    const todosProcessados = archivosRequeridos.every(tipo => 
      estadoArchivos[tipo] === "procesado"
    );

    return todosProcessados;
  };

  // Función para verificar si el cierre está en un estado anterior a "archivos_completos"
  const estaEnEstadoAnteriorAArchivosCompletos = () => {
    // Estados anteriores a "archivos_completos" donde SÍ se debe hacer la verificación automática
    const estadosAnteriores = [
      'creado',
      'libro_subido',
      'movimientos_subidos',
      'archivos_en_proceso'
    ];
    
    return estadosAnteriores.includes(cierre?.estado);
  };

  // Efecto para detectar cuando todos los archivos están procesados
  useEffect(() => {
    const archivosCompletos = verificarArchivosCompletos();
    const estaEnEstadoAnterior = estaEnEstadoAnteriorAArchivosCompletos();
    
    console.log('🔍 [ArchivosAnalistaSection] Verificando condiciones:', {
      archivosCompletos,
      estadoCierre: cierre?.estado,
      estaEnEstadoAnterior,
      estadoCompletadoAnteriormente,
      procesandoCambioEstado: procesandoCambioEstado.current
    });
    
    // Solo proceder si:
    // 1. Todos los archivos están completos
    // 2. El cierre está en un estado anterior a "archivos_completos" 
    // 3. No se ha completado anteriormente
    // 4. No se está procesando actualmente
    if (archivosCompletos && estaEnEstadoAnterior && !estadoCompletadoAnteriormente && !procesandoCambioEstado.current) {
      console.log('🎯 [ArchivosAnalistaSection] Condiciones cumplidas - Actualizando estado del cierre a archivos_completos...');
      
      procesandoCambioEstado.current = true;
      setEstadoCompletadoAnteriormente(true);
      
      const actualizarEstado = async () => {
        try {
          await actualizarEstadoCierreNomina(cierreId);
          console.log('✅ [ArchivosAnalistaSection] Estado del cierre actualizado por archivos completos');
          
          // Refrescar los datos del cierre en el componente padre
          if (onCierreActualizado) {
            await onCierreActualizado();
          }
        } catch (error) {
          console.error('❌ [ArchivosAnalistaSection] Error actualizando estado del cierre:', error);
          // Revertir el flag en caso de error para permitir retry
          setEstadoCompletadoAnteriormente(false);
        } finally {
          procesandoCambioEstado.current = false;
        }
      };
      
      actualizarEstado();
    } else if (archivosCompletos && !estaEnEstadoAnterior) {
      console.log('ℹ️ [ArchivosAnalistaSection] Archivos completos pero cierre ya está en estado posterior - No se actualiza automáticamente');
    }
  }, [estadoArchivos, cierreId, cierre?.estado, onCierreActualizado, estadoCompletadoAnteriormente]);

  // 🎯 Efecto para reportar el estado de la sección al componente padre
  useEffect(() => {
    const estadoGeneral = calcularEstadoGeneral();
    const estadoFinal = estadoGeneral === "Procesado" ? "procesado" : "pendiente";
    
    console.log('📊 [ArchivosAnalistaSection] Reportando estado:', estadoFinal);
    
    if (onEstadoChange) {
      onEstadoChange(estadoFinal);
    }
  }, [
    // Solo las propiedades específicas que afectan el cálculo
    JSON.stringify(estadoArchivos), 
    onEstadoChange
  ]);

  const estadoGeneral = calcularEstadoGeneral();
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
            disabled ? 'bg-gray-600' : 'bg-green-600'
          }`}>
            {disabled ? (
              <Lock size={20} className="text-white" />
            ) : (
              <UserCheck size={20} className="text-white" />
            )}
          </div>
          <div>
            <h2 className={`text-xl font-semibold ${disabled ? 'text-gray-400' : 'text-white'}`}>
              Archivos del Analista
              {disabled && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  (Bloqueado - Datos Consolidados)
                </span>
              )}
            </h2>
            <p className="text-gray-400 text-sm">
              {disabled 
                ? 'Los archivos están bloqueados porque los datos ya han sido consolidados'
                : 'Archivos complementarios gestionados por el analista'
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
      
      {/* Contenedor de archivos del analista - solo se muestra cuando está expandido y no disabled */}
      {expandido && !disabled && (
        <ArchivosAnalistaContainer
          cierreId={cierreId}
          cliente={cliente}
          disabled={disabled}
          onEstadosChange={setEstadoArchivos}
          onCierreActualizado={onCierreActualizado}
          deberiaDetenerPolling={deberiaDetenerPolling}
        />
      )}
    </section>
  );
};

export default ArchivosAnalistaSection;
