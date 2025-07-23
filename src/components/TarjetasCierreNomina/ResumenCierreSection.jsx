import { useState, useEffect } from "react";
import { FileText, Users, Calendar, CheckCircle, Download, Eye, ChevronDown, ChevronRight, Database, UserCheck, ExternalLink } from "lucide-react";

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
      // TODO: Implementar endpoint para obtener archivos usados y estadísticas del cierre
      // const archivos = await obtenerArchivosUsadosCierre(cierre.id);
      // setArchivosUsados(archivos);
      
      // Datos mock de archivos usados y estadísticas mientras se implementa el endpoint
      setArchivosUsados({
        estadisticas: {
          total_empleados: cierre?.total_empleados || 145,
          total_ingresos: cierre?.total_ingresos || 12,
          total_finiquitos: cierre?.total_finiquitos || 8,
          total_ausentismos: cierre?.total_ausentismos || 23
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
            estado: 'procesado'
          },
          { 
            tipo: 'incidencias', 
            nombre: 'incidencias.xlsx',
            fecha_subida: new Date().toISOString(),
            estado: 'procesado'
          },
          { 
            tipo: 'ingresos', 
            nombre: 'ingresos.xlsx',
            fecha_subida: new Date().toISOString(),
            estado: 'procesado'
          },
          { 
            tipo: 'novedades', 
            nombre: 'novedades.xlsx',
            fecha_subida: new Date().toISOString(),
            estado: 'procesado'
          }
        ]
      });
    } catch (err) {
      console.error("Error cargando archivos usados:", err);
    } finally {
      setCargando(false);
    }
  };

  const formatearFecha = (fecha) => {
    if (!fecha) return 'N/A';
    return new Date(fecha).toLocaleString('es-CL', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
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
          {/* Información General */}
          <div className="bg-gray-800 rounded-lg p-6 border border-green-700/30">
            <h3 className="text-lg font-medium text-white mb-4 flex items-center">
              <Calendar className="w-5 h-5 mr-2 text-green-400" />
              Información del Cierre
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-400">Periodo</p>
                  <p className="text-white font-medium">{cierre?.periodo || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Cliente</p>
                  <p className="text-white font-medium">{cierre?.cliente?.nombre || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Estado Final</p>
                  <p className="text-green-400 font-medium">Finalizado</p>
                </div>
              </div>
              
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-400">Fecha de Finalización</p>
                  <p className="text-white font-medium">
                    {formatearFecha(cierre?.fecha_finalizacion)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Finalizado por</p>
                  <p className="text-white font-medium">{cierre?.usuario_finalizacion || 'Sistema'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Estado de Incidencias</p>
                  <p className="text-green-400 font-medium">
                    {cierre?.estado_incidencias === 'resueltas' ? 'Resueltas' : cierre?.estado_incidencias || 'N/A'}
                  </p>
                </div>
              </div>
            </div>
          </div>

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
                      <span className="text-green-400 text-sm bg-green-900/30 px-2 py-1 rounded">
                        {archivo.estado === 'procesado' ? 'Procesado' : archivo.estado}
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
                      <span className="text-green-400 text-sm bg-green-900/30 px-2 py-1 rounded">
                        {archivo.estado === 'procesado' ? 'Procesado' : archivo.estado}
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
        </div>
      )}
    </section>
  );
};

export default ResumenCierreSection;
