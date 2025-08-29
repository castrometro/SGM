import React, { useState, useEffect, useRef } from "react";
import { BarChart3, Upload, Trash2, Eye, Download } from "lucide-react";
import CardBase from "./CardBase";
import usePolling from "../../hooks/usePolling";
import { 
  obtenerEstadoMovimientosMes,
  subirMovimientosMes,
  eliminarMovimientosMes
} from "../../../../api/nomina";

const MovimientosMesCard_v2 = ({
  cierreId,
  enabled = false
}) => {
  const [movimientos, setMovimientos] = useState(null);
  const [subiendo, setSubiendo] = useState(false);
  const [error, setError] = useState(null);
  const [eliminando, setEliminando] = useState(false);
  
  const fileInputRef = useRef();

  // 🎯 DETERMINAR ESTADO ACTUAL
  const estadoActual = movimientos?.estado || 'pendiente';
  const deberiaHacerPolling = estadoActual === 'procesando';

  // 🎯 POLLING ESTANDARIZADO
  const { 
    data: datosMovimientos, 
    loading: cargandoEstado, 
    error: errorPolling 
  } = usePolling(
    () => obtenerEstadoMovimientosMes(cierreId),
    3000,
    !deberiaHacerPolling || !enabled,
    enabled,
    [cierreId]
  );

  // 🎯 ACTUALIZAR ESTADO LOCAL CUANDO LLEGAN DATOS
  useEffect(() => {
    if (datosMovimientos) {
      console.log('📊 [MovimientosCard_v2] Datos actualizados:', datosMovimientos);
      setMovimientos(datosMovimientos);
    }
  }, [datosMovimientos]);

  // 🎯 CARGAR ESTADO INICIAL
  useEffect(() => {
    if (cierreId && enabled && !movimientos) {
      const cargarEstadoInicial = async () => {
        try {
          const data = await obtenerEstadoMovimientosMes(cierreId);
          setMovimientos(data);
        } catch (err) {
          console.error('❌ [MovimientosCard_v2] Error cargando estado inicial:', err);
          setError(err);
        }
      };
      cargarEstadoInicial();
    }
  }, [cierreId, enabled, movimientos]);

  // 🎯 MANEJAR SUBIDA DE ARCHIVO
  const handleSubirArchivo = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      setSubiendo(true);
      setError(null);
      
      const resultado = await subirMovimientosMes(cierreId, file);
      console.log('✅ [MovimientosCard_v2] Archivo subido:', resultado);
      
      // Recargar estado después de subir
      const nuevoEstado = await obtenerEstadoMovimientosMes(cierreId);
      setMovimientos(nuevoEstado);
      
    } catch (err) {
      console.error('❌ [MovimientosCard_v2] Error subiendo archivo:', err);
      setError(err);
    } finally {
      setSubiendo(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // 🎯 MANEJAR ELIMINACIÓN
  const handleEliminar = async () => {
    try {
      setEliminando(true);
      setError(null);
      
      await eliminarMovimientosMes(cierreId);
      console.log('✅ [MovimientosCard_v2] Archivo eliminado');
      
      // Recargar estado después de eliminar
      const nuevoEstado = await obtenerEstadoMovimientosMes(cierreId);
      setMovimientos(nuevoEstado);
      
    } catch (err) {
      console.error('❌ [MovimientosCard_v2] Error eliminando archivo:', err);
      setError(err);
    } finally {
      setEliminando(false);
    }
  };

  // 🎯 OBTENER DESCRIPCIÓN DEL ESTADO
  const obtenerDescripcionEstado = () => {
    switch(estadoActual) {
      case 'pendiente':
        return 'Listo para cargar archivo de movimientos del mes';
      case 'subido':
        return '📁 Archivo de movimientos cargado correctamente';
      case 'procesando':
        return '⏳ Procesando archivo de movimientos...';
      case 'completado':
        return '✅ Movimientos procesados correctamente';
      case 'error':
        return '❌ Error en el procesamiento de movimientos';
      default:
        return 'Estado desconocido';
    }
  };

  // 🎯 OBTENER BOTONES SEGÚN ESTADO
  const obtenerBotones = () => {
    const isDisabled = !enabled;
    
    if (isDisabled) {
      return [
        {
          icon: Upload,
          text: "Subir Movimientos",
          variant: "secondary",
          disabled: true
        }
      ];
    }

    switch(estadoActual) {
      case 'pendiente':
        return [
          {
            icon: Upload,
            text: "Subir Movimientos",
            variant: "primary",
            onClick: () => fileInputRef.current?.click(),
            loading: subiendo,
            disabled: subiendo
          }
        ];
        
      case 'subido':
      case 'procesando':
        return [
          {
            icon: Eye,
            text: "Ver Detalles",
            variant: "secondary",
            onClick: () => console.log('Ver detalles movimientos')
          },
          {
            icon: Trash2,
            text: "Eliminar",
            variant: "danger",
            onClick: handleEliminar,
            loading: eliminando,
            disabled: eliminando || estadoActual === 'procesando'
          }
        ];
        
      case 'completado':
        return [
          {
            icon: Eye,
            text: "Ver Detalles",
            variant: "secondary",
            onClick: () => console.log('Ver detalles movimientos')
          },
          {
            icon: Download,
            text: "Descargar",
            variant: "secondary",
            onClick: () => console.log('Descargar movimientos')
          },
          {
            icon: Trash2,
            text: "Eliminar",
            variant: "danger",
            onClick: handleEliminar,
            loading: eliminando,
            disabled: eliminando
          }
        ];
        
      case 'error':
        return [
          {
            icon: Upload,
            text: "Reintentar",
            variant: "primary",
            onClick: () => fileInputRef.current?.click(),
            loading: subiendo,
            disabled: subiendo
          },
          {
            icon: Trash2,
            text: "Eliminar",
            variant: "danger",
            onClick: handleEliminar,
            loading: eliminando,
            disabled: eliminando
          }
        ];
        
      default:
        return [];
    }
  };

  // 🎯 OBTENER INFORMACIÓN ADICIONAL
  const obtenerInfoAdicional = () => {
    if (!movimientos) return null;
    
    const info = [];
    
    if (movimientos.nombre_archivo) {
      info.push(`📄 ${movimientos.nombre_archivo}`);
    }
    
    if (movimientos.fecha_subida) {
      info.push(`📅 Subido: ${new Date(movimientos.fecha_subida).toLocaleString()}`);
    }
    
    if (movimientos.total_registros) {
      info.push(`📊 ${movimientos.total_registros} registros`);
    }
    
    if (movimientos.errores && movimientos.errores.length > 0) {
      info.push(`⚠️ ${movimientos.errores.length} errores detectados`);
    }
    
    return info.length > 0 ? info : null;
  };

  return (
    <>
      <CardBase
        title="Subir Movimientos del Mes"
        icon={BarChart3}
        isDisabled={!enabled}
        status={estadoActual}
        description={obtenerDescripcionEstado()}
        buttons={obtenerBotones()}
        loading={cargandoEstado}
        error={error || errorPolling}
        additionalInfo={obtenerInfoAdicional()}
      />
      
      {/* Input oculto para seleccionar archivo */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".xlsx,.xls,.csv"
        onChange={handleSubirArchivo}
        style={{ display: 'none' }}
      />
    </>
  );
};

export default MovimientosMesCard_v2;
