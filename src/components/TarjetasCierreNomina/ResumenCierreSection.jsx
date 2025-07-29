import { useState, useEffect } from "react";
import { FileText, Users, Calendar, CheckCircle, Download, Eye, ChevronDown, ChevronRight, Database, UserCheck, ExternalLink } from "lucide-react";
import { 
  obtenerLibroRemuneraciones,
  obtenerEstadoLibroRemuneraciones,
  obtenerEstadoMovimientosMes,
  obtenerEstadoArchivoAnalista,
  obtenerEstadoArchivoNovedades
} from "../../api/nomina";

const ResumenCierreSection = ({ cierre, onIrDashboard }) => {
  const [expandido, setExpandido] = useState(true);
  const [archivosUsados, setArchivosUsados] = useState(null);
  const [cargando, setCargando] = useState(false);

  useEffect(() => {
    if (cierre?.id && cierre?.estado === 'finalizado') {
      cargarArchivosUsados();
    }
  }, [cierre?.id, cierre?.estado]);

  const cargarArchivosUsados = async () => {
    setCargando(true);
    try {
      // Usar el endpoint existente del libro de remuneraciones que ya tiene las estadísticas
      const libroData = await obtenerLibroRemuneraciones(cierre.id);
      
      // Transformar los datos del libro a la estructura esperada
      const estadisticas = {
        total_empleados: libroData.resumen?.total_empleados || 0,
        total_ingresos: libroData.empleados?.filter(emp => emp.estado_empleado === 'nueva_incorporacion').length || 0,
        total_finiquitos: libroData.empleados?.filter(emp => emp.estado_empleado === 'finiquito').length || 0,
        total_ausentismos: libroData.empleados?.filter(emp => 
          emp.estado_empleado === 'ausente_total' || emp.estado_empleado === 'ausente_parcial'
        ).length || 0
      };
      
      // ========== OBTENER DATOS REALES DE ARCHIVOS TALANA ==========
      const archivos_talana = [];
      
      // Verificar Libro de Remuneraciones
      try {
        const estadoLibro = await obtenerEstadoLibroRemuneraciones(cierre.id);
        if (estadoLibro && estadoLibro.estado === 'procesado') {
          archivos_talana.push({
            tipo: 'libro_remuneraciones',
            nombre: estadoLibro.archivo_nombre || 'libro_remuneraciones.xlsx',
            fecha_subida: estadoLibro.fecha_subida || libroData.cierre?.fecha_consolidacion,
            estado: 'procesado'
          });
        }
      } catch (err) {
        console.log('No se pudo obtener estado del libro de remuneraciones');
      }
      
      // Verificar Movimientos del Mes
      try {
        const estadoMovimientos = await obtenerEstadoMovimientosMes(cierre.id);
        if (estadoMovimientos && estadoMovimientos.estado === 'procesado') {
          archivos_talana.push({
            tipo: 'movimientos_mes',
            nombre: estadoMovimientos.archivo_nombre || 'movimientos_mes.xlsx',
            fecha_subida: estadoMovimientos.fecha_subida || libroData.cierre?.fecha_consolidacion,
            estado: 'procesado'
          });
        }
      } catch (err) {
        console.log('No se pudo obtener estado de movimientos del mes');
      }
      
      // ========== OBTENER DATOS REALES DE ARCHIVOS DEL ANALISTA ==========
      // Definir todos los tipos de archivos del analista (incluyendo novedades)
      const tiposAnalista = [
        { tipo: 'finiquitos', endpoint: 'obtenerEstadoArchivoAnalista' },
        { tipo: 'incidencias', endpoint: 'obtenerEstadoArchivoAnalista' },
        { tipo: 'ingresos', endpoint: 'obtenerEstadoArchivoAnalista' },
        { tipo: 'novedades', endpoint: 'obtenerEstadoArchivoNovedades' }
      ];
      
      const archivos_analista = [];
      
      // Procesar cada tipo de archivo
      for (const { tipo, endpoint } of tiposAnalista) {
        try {
          let estadoArchivo;
          
          if (endpoint === 'obtenerEstadoArchivoAnalista') {
            estadoArchivo = await obtenerEstadoArchivoAnalista(cierre.id, tipo);
            
            // 🐛 DEBUG: Log para ver qué devuelve la API
            console.log(`🔍 [DEBUG] Archivo ${tipo} - Respuesta completa:`, estadoArchivo);
            
            // Detectar diferentes estructuras de respuesta
            let archivo = null;
            
            // Caso 1: Respuesta con results array
            if (estadoArchivo && estadoArchivo.results && estadoArchivo.results.length > 0) {
              archivo = estadoArchivo.results[0];
              console.log(`✅ [DEBUG] Archivo ${tipo} - ENCONTRADO (structure: results):`, archivo);
            }
            // Caso 2: Respuesta directa como array
            else if (Array.isArray(estadoArchivo) && estadoArchivo.length > 0) {
              archivo = estadoArchivo[0];
              console.log(`✅ [DEBUG] Archivo ${tipo} - ENCONTRADO (structure: array):`, archivo);
            }
            // Caso 3: Respuesta directa como objeto
            else if (estadoArchivo && typeof estadoArchivo === 'object' && estadoArchivo.id) {
              archivo = estadoArchivo;
              console.log(`✅ [DEBUG] Archivo ${tipo} - ENCONTRADO (structure: object):`, archivo);
            }
            
            if (archivo) {
              archivos_analista.push({
                tipo: tipo,
                nombre: archivo.archivo_nombre || `${tipo}.xlsx`,
                fecha_subida: archivo.fecha_subida || new Date().toISOString(),
                estado: archivo.estado || 'procesado'
              });
            } else {
              // No se encontró archivo de este tipo
              console.log(`❌ [DEBUG] Archivo ${tipo} - NO ENCONTRADO, marcando como no_subido`);
              archivos_analista.push({
                tipo: tipo,
                nombre: `${tipo}.xlsx`,
                fecha_subida: null,
                estado: 'no_subido'
              });
            }
          } else if (endpoint === 'obtenerEstadoArchivoNovedades') {
            estadoArchivo = await obtenerEstadoArchivoNovedades(cierre.id);
            
            // 🐛 DEBUG: Log para novedades
            console.log(`🔍 [DEBUG] Novedades - Respuesta:`, estadoArchivo);
            console.log(`🔍 [DEBUG] Novedades - Estado:`, estadoArchivo?.estado);
            
            if (estadoArchivo && estadoArchivo.estado === 'procesado') {
              console.log(`✅ [DEBUG] Novedades - ENCONTRADO`);
              archivos_analista.push({
                tipo: 'novedades',
                nombre: estadoArchivo.archivo_nombre || 'novedades.xlsx',
                fecha_subida: estadoArchivo.fecha_subida || new Date().toISOString(),
                estado: 'procesado'
              });
            } else {
              // No se encontró archivo de novedades
              console.log(`❌ [DEBUG] Novedades - NO ENCONTRADO, marcando como no_subido`);
              archivos_analista.push({
                tipo: 'novedades',
                nombre: 'novedades.xlsx',
                fecha_subida: null,
                estado: 'no_subido'
              });
            }
          }
        } catch (err) {
          console.error(`❌ [ERROR] No se pudo obtener estado del archivo ${tipo}:`, err);
          console.error(`❌ [ERROR] Error details:`, err.response || err.message);
          // En caso de error, agregar como no subido
          archivos_analista.push({
            tipo: tipo,
            nombre: `${tipo}.xlsx`,
            fecha_subida: null,
            estado: 'no_subido'
          });
        }
      }
      
      setArchivosUsados({
        estadisticas,
        talana: archivos_talana,
        analista: archivos_analista,
        resumen_libro: {
          total_haberes: libroData.resumen?.total_haberes || 0,
          total_descuentos: libroData.resumen?.total_descuentos || 0,
          liquido_total: libroData.resumen?.liquido_total || 0
        }
      });
    } catch (err) {
      console.error("Error cargando datos del libro de remuneraciones:", err);
      
      // Fallback a datos mock si hay error
      setArchivosUsados({
        estadisticas: {
          total_empleados: cierre?.total_empleados || 0,
          total_ingresos: cierre?.total_ingresos || 0,
          total_finiquitos: cierre?.total_finiquitos || 0,
          total_ausentismos: cierre?.total_ausentismos || 0
        },
        talana: [
          { 
            tipo: 'libro_remuneraciones', 
            nombre: cierre.libro?.archivo_nombre || 'libro_remuneraciones.xlsx',
            fecha_subida: cierre.libro?.fecha_subida || new Date().toISOString(),
            estado: 'procesado'
          },
          { 
            tipo: 'movimientos_mes', 
            nombre: cierre.movimientos?.archivo_nombre || 'movimientos_mes.xlsx',
            fecha_subida: cierre.movimientos?.fecha_subida || new Date().toISOString(),
            estado: 'procesado'
          }
        ],
        analista: [
          { 
            tipo: 'finiquitos', 
            nombre: 'finiquitos.xlsx',
            fecha_subida: new Date().toISOString(),
            estado: 'no_subido'
          },
          { 
            tipo: 'incidencias', 
            nombre: 'incidencias.xlsx',
            fecha_subida: new Date().toISOString(),
            estado: 'no_subido'
          },
          { 
            tipo: 'ingresos', 
            nombre: 'ingresos.xlsx',
            fecha_subida: new Date().toISOString(),
            estado: 'no_subido'
          },
          { 
            tipo: 'novedades', 
            nombre: 'novedades.xlsx',
            fecha_subida: new Date().toISOString(),
            estado: 'no_subido'
          }
        ]
      });
    } finally {
      setCargando(false);
    }
  };

  const formatearFecha = (fecha) => {
    if (!fecha) return 'No subido';
    return new Date(fecha).toLocaleString('es-CL', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const obtenerEstiloEstado = (estado) => {
    switch (estado) {
      case 'procesado':
        return 'text-green-400 bg-green-900/30';
      case 'no_subido':
        return 'text-gray-400 bg-gray-700/30';
      case 'procesando':
        return 'text-yellow-400 bg-yellow-900/30';
      case 'error':
        return 'text-red-400 bg-red-900/30';
      default:
        return 'text-gray-400 bg-gray-700/30';
    }
  };

  const obtenerTextEstado = (estado) => {
    switch (estado) {
      case 'procesado':
        return 'Procesado';
      case 'no_subido':
        return 'No subido';
      case 'procesando':
        return 'Procesando...';
      case 'error':
        return 'Error';
      default:
        return estado;
    }
  };

  if (cierre?.estado !== 'finalizado') {
    return null;
  }

  return (
    <section className="space-y-6">
      <div
        className="flex items-center justify-between cursor-pointer hover:bg-gray-800/50 p-3 -m-3 rounded-lg transition-colors"
        onClick={() => setExpandido(!expandido)}
      >
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 bg-green-600 rounded-lg">
            <CheckCircle size={20} className="text-white" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-white">
              Resumen del Cierre
            </h2>
            <p className="text-gray-400 text-sm">
              Cierre finalizado - Información consolidada y reportes generados
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-green-400 text-sm font-medium">
            Finalizado
          </span>
          {expandido ? (
            <ChevronDown size={20} className="text-gray-400" />
          ) : (
            <ChevronRight size={20} className="text-gray-400" />
          )}
        </div>
      </div>

      {expandido && (
        <div className="space-y-6">
          {/* Indicador de carga */}
          {cargando && (
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                <span className="ml-3 text-gray-400">Cargando datos del cierre...</span>
              </div>
            </div>
          )}

          {!cargando && archivosUsados && (
            <>
              {/* Estadísticas del Cierre */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400">Total Empleados</p>
                      <p className="text-2xl font-bold text-white">{archivosUsados?.estadisticas?.total_empleados || 0}</p>
                    </div>
                    <Users className="w-8 h-8 text-blue-500" />
                  </div>
                </div>
            
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Total Ingresos</p>
                  <p className="text-2xl font-bold text-white">{archivosUsados?.estadisticas?.total_ingresos || 0}</p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-500" />
              </div>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Total Finiquitos</p>
                  <p className="text-2xl font-bold text-white">{archivosUsados?.estadisticas?.total_finiquitos || 0}</p>
                </div>
                <FileText className="w-8 h-8 text-red-500" />
              </div>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Total Ausentismos</p>
                  <p className="text-2xl font-bold text-white">{archivosUsados?.estadisticas?.total_ausentismos || 0}</p>
                </div>
                <Calendar className="w-8 h-8 text-yellow-500" />
              </div>
            </div>
          </div>

          {/* Resumen Financiero */}
          {archivosUsados?.resumen_libro && (
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-medium text-white mb-4 flex items-center">
                <FileText className="w-5 h-5 mr-2 text-green-400" />
                Resumen Financiero
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center p-4 bg-gray-700 rounded-lg">
                  <p className="text-sm text-gray-400 mb-1">Total Haberes</p>
                  <p className="text-xl font-bold text-green-400">
                    ${archivosUsados.resumen_libro.total_haberes?.toLocaleString('es-CL') || '0'}
                  </p>
                </div>
                
                <div className="text-center p-4 bg-gray-700 rounded-lg">
                  <p className="text-sm text-gray-400 mb-1">Total Descuentos</p>
                  <p className="text-xl font-bold text-red-400">
                    ${archivosUsados.resumen_libro.total_descuentos?.toLocaleString('es-CL') || '0'}
                  </p>
                </div>
                
                <div className="text-center p-4 bg-gray-700 rounded-lg">
                  <p className="text-sm text-gray-400 mb-1">Líquido Total</p>
                  <p className="text-xl font-bold text-blue-400">
                    ${archivosUsados.resumen_libro.liquido_total?.toLocaleString('es-CL') || '0'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Archivos Usados */}
          <div className="space-y-4">
            {/* Archivos Talana */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-medium text-white mb-4 flex items-center">
                <Database className="w-5 h-5 mr-2 text-blue-400" />
                Archivos Talana
              </h3>
              
              <div className="space-y-3">
                {archivosUsados?.talana?.map((archivo, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-blue-400" />
                      <div>
                        <p className="text-white font-medium">{archivo.nombre}</p>
                        <p className="text-gray-400 text-sm">
                          Tipo: {archivo.tipo.replace('_', ' ').toUpperCase()} • Subido: {formatearFecha(archivo.fecha_subida)}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <span className={`text-sm px-2 py-1 rounded ${obtenerEstiloEstado(archivo.estado)}`}>
                        {obtenerTextEstado(archivo.estado)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Archivos del Analista */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-medium text-white mb-4 flex items-center">
                <UserCheck className="w-5 h-5 mr-2 text-green-400" />
                Archivos del Analista
              </h3>
              
              <div className="space-y-3">
                {archivosUsados?.analista?.map((archivo, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-green-400" />
                      <div>
                        <p className="text-white font-medium">{archivo.nombre}</p>
                        <p className="text-gray-400 text-sm">
                          Tipo: {archivo.tipo.toUpperCase()} • Subido: {formatearFecha(archivo.fecha_subida)}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <span className={`text-sm px-2 py-1 rounded ${obtenerEstiloEstado(archivo.estado)}`}>
                        {obtenerTextEstado(archivo.estado)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Mensaje Final y Botón Dashboard */}
          <div className="space-y-4">
            <div className="bg-green-900/20 border border-green-700 rounded-lg p-4">
              <div className="flex items-center gap-2 text-green-400">
                <CheckCircle className="w-5 h-5" />
                <div>
                  <p className="font-medium">🎉 Cierre finalizado exitosamente</p>
                  <p className="text-sm text-green-300 mt-1">
                    Todos los datos han sido consolidados y el cierre de nómina para el periodo {cierre?.periodo} ha sido completado.
                    Los archivos utilizados están listados arriba para referencia.
                  </p>
                </div>
              </div>
            </div>
            
            {/* Botón Ir a Dashboard */}
            <div className="flex justify-center">
              <button
                onClick={onIrDashboard}
                className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-medium transition-colors flex items-center gap-2 shadow-lg hover:shadow-xl"
              >
                <ExternalLink className="w-5 h-5" />
                Ir a Dashboard
              </button>
            </div>
          </div>
          </>
          )}
        </div>
      )}
    </section>
  );
};

export default ResumenCierreSection;
