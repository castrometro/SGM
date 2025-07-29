import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  FileCheck, 
  AlertTriangle, 
  RefreshCw, 
  Database,
  Users,
  CheckCircle,
  XCircle,
  Clock
} from 'lucide-react';
import { 
  obtenerArchivosSubidosCierre,
  obtenerIncidenciasCierre,
  obtenerDatosConsolidadosNomina
} from '@/api/nomina';

const CierreActionMonitor = ({ cierreId }) => {
  const [archivos, setArchivos] = useState([]);
  const [incidencias, setIncidencias] = useState([]);
  const [datosConsolidados, setDatosConsolidados] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  // Función para obtener todos los datos relevantes
  const fetchAllData = async () => {
    setIsLoading(true);
    try {
      console.log("🔍 [ActionMonitor] Obteniendo datos para cierre:", cierreId);
      
      // Obtener archivos
      try {
        const archivosData = await obtenerArchivosSubidosCierre(cierreId);
        setArchivos(archivosData.results || archivosData || []);
        console.log("📁 [ActionMonitor] Archivos obtenidos:", archivosData);
      } catch (error) {
        console.warn("⚠️ [ActionMonitor] Error obteniendo archivos:", error);
        setArchivos([]);
      }

      // Obtener incidencias
      try {
        const incidenciasData = await obtenerIncidenciasCierre(cierreId);
        setIncidencias(incidenciasData.results || incidenciasData || []);
        console.log("🚨 [ActionMonitor] Incidencias obtenidas:", incidenciasData);
      } catch (error) {
        console.warn("⚠️ [ActionMonitor] Error obteniendo incidencias:", error);
        setIncidencias([]);
      }

      // Obtener datos consolidados
      try {
        const consolidadosData = await obtenerDatosConsolidadosNomina(cierreId);
        setDatosConsolidados(consolidadosData);
        console.log("📊 [ActionMonitor] Datos consolidados:", consolidadosData);
      } catch (error) {
        console.warn("⚠️ [ActionMonitor] Error obteniendo consolidados:", error);
        setDatosConsolidados(null);
      }

      setLastUpdate(new Date());
      console.log("✅ [ActionMonitor] Actualización completada");
      
    } catch (error) {
      console.error("❌ [ActionMonitor] Error general:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Cargar datos al montar componente
  useEffect(() => {
    if (cierreId) {
      fetchAllData();
    }
  }, [cierreId]);

  // Función para obtener el estado de un archivo
  const getFileStatus = (archivo) => {
    if (!archivo) return 'sin_datos';
    
    if (archivo.estado === 'subido' || archivo.uploaded || archivo.is_uploaded) {
      return 'subido';
    } else if (archivo.estado === 'procesando' || archivo.processing) {
      return 'procesando';
    } else if (archivo.estado === 'error' || archivo.error) {
      return 'error';
    } else {
      return 'no_subido';
    }
  };

  // Función para obtener el color del badge según estado
  const getStatusBadgeVariant = (status) => {
    switch (status) {
      case 'subido': return 'default';
      case 'procesando': return 'secondary';
      case 'error': return 'destructive';
      default: return 'outline';
    }
  };

  // Función para obtener estadísticas de archivos
  const getFileStats = () => {
    const stats = {
      total: archivos.length,
      subidos: 0,
      procesando: 0,
      errores: 0,
      no_subidos: 0
    };

    archivos.forEach(archivo => {
      const status = getFileStatus(archivo);
      switch (status) {
        case 'subido': stats.subidos++; break;
        case 'procesando': stats.procesando++; break;
        case 'error': stats.errores++; break;
        default: stats.no_subidos++; break;
      }
    });

    return stats;
  };

  const fileStats = getFileStats();

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Monitor de Acciones - Análisis Detallado
          </span>
          <div className="flex items-center gap-2">
            {lastUpdate && (
              <span className="text-sm text-gray-500">
                Actualizado: {lastUpdate.toLocaleTimeString()}
              </span>
            )}
            <Button
              onClick={fetchAllData}
              disabled={isLoading}
              variant="outline"
              size="sm"
            >
              <RefreshCw className={`h-4 w-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
              Actualizar
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-6">

        {/* Estadísticas de archivos */}
        <div>
          <h4 className="font-medium mb-3 flex items-center gap-2">
            <FileCheck className="h-4 w-4" />
            Estado de Archivos ({fileStats.total} total)
          </h4>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="text-center p-3 bg-green-50 rounded">
              <div className="text-2xl font-bold text-green-600">{fileStats.subidos}</div>
              <div className="text-sm text-green-700">Subidos</div>
            </div>
            <div className="text-center p-3 bg-yellow-50 rounded">
              <div className="text-2xl font-bold text-yellow-600">{fileStats.procesando}</div>
              <div className="text-sm text-yellow-700">Procesando</div>
            </div>
            <div className="text-center p-3 bg-red-50 rounded">
              <div className="text-2xl font-bold text-red-600">{fileStats.errores}</div>
              <div className="text-sm text-red-700">Con Errores</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded">
              <div className="text-2xl font-bold text-gray-600">{fileStats.no_subidos}</div>
              <div className="text-sm text-gray-700">Sin Subir</div>
            </div>
          </div>

          {/* Lista detallada de archivos */}
          {archivos.length > 0 && (
            <div className="space-y-2">
              <h5 className="font-medium text-sm">Detalle por Archivo:</h5>
              {archivos.map((archivo, index) => {
                const status = getFileStatus(archivo);
                return (
                  <div key={index} className="flex items-center justify-between p-2 border rounded">
                    <div>
                      <div className="font-medium text-sm">
                        {archivo.tipo_archivo || archivo.name || `Archivo ${index + 1}`}
                      </div>
                      <div className="text-xs text-gray-600">
                        {archivo.nombre_archivo || archivo.filename || 'Sin nombre'}
                      </div>
                      {archivo.fecha_subida && (
                        <div className="text-xs text-gray-500">
                          Subido: {new Date(archivo.fecha_subida).toLocaleString()}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={getStatusBadgeVariant(status)}>
                        {status.replace('_', ' ')}
                      </Badge>
                      {archivo.total_registros && (
                        <span className="text-xs text-gray-500">
                          ({archivo.total_registros} registros)
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Estadísticas de incidencias */}
        <div>
          <h4 className="font-medium mb-3 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            Estado de Incidencias ({incidencias.length} total)
          </h4>
          
          {incidencias.length > 0 ? (
            <div className="space-y-2">
              {incidencias.slice(0, 5).map((incidencia, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-orange-50 border-l-4 border-orange-400">
                  <div>
                    <div className="font-medium text-sm">
                      {incidencia.tipo_incidencia || incidencia.tipo || 'Incidencia'}
                    </div>
                    <div className="text-xs text-gray-600">
                      {incidencia.descripcion || incidencia.mensaje || 'Sin descripción'}
                    </div>
                  </div>
                  <Badge variant={incidencia.estado === 'resuelta' ? 'default' : 'destructive'}>
                    {incidencia.estado || 'pendiente'}
                  </Badge>
                </div>
              ))}
              {incidencias.length > 5 && (
                <div className="text-sm text-gray-500 text-center">
                  ... y {incidencias.length - 5} incidencias más
                </div>
              )}
            </div>
          ) : (
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>
                No hay incidencias reportadas para este cierre.
              </AlertDescription>
            </Alert>
          )}
        </div>

        {/* Datos consolidados */}
        <div>
          <h4 className="font-medium mb-3 flex items-center gap-2">
            <Users className="h-4 w-4" />
            Datos Consolidados
          </h4>
          
          {datosConsolidados ? (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="p-3 bg-blue-50 rounded">
                <div className="text-lg font-bold text-blue-600">
                  {datosConsolidados.total_empleados || 0}
                </div>
                <div className="text-sm text-blue-700">Total Empleados</div>
              </div>
              <div className="p-3 bg-purple-50 rounded">
                <div className="text-lg font-bold text-purple-600">
                  {datosConsolidados.total_registros || 0}
                </div>
                <div className="text-sm text-purple-700">Registros Procesados</div>
              </div>
              <div className="p-3 bg-indigo-50 rounded">
                <div className="text-lg font-bold text-indigo-600">
                  {datosConsolidados.fecha_consolidacion ? 
                    new Date(datosConsolidados.fecha_consolidacion).toLocaleDateString() : 
                    'Pendiente'
                  }
                </div>
                <div className="text-sm text-indigo-700">Fecha Consolidación</div>
              </div>
            </div>
          ) : (
            <Alert>
              <Clock className="h-4 w-4" />
              <AlertDescription>
                Los datos aún no han sido consolidados.
              </AlertDescription>
            </Alert>
          )}
        </div>

        {/* Alertas y problemas detectados */}
        <div>
          <h4 className="font-medium mb-3 flex items-center gap-2">
            <XCircle className="h-4 w-4" />
            Problemas Detectados
          </h4>
          
          <div className="space-y-2">
            {fileStats.errores > 0 && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  Hay {fileStats.errores} archivo(s) con errores que pueden estar bloqueando el progreso.
                </AlertDescription>
              </Alert>
            )}
            
            {fileStats.no_subidos > 0 && (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Faltan {fileStats.no_subidos} archivo(s) por subir para completar el cierre.
                </AlertDescription>
              </Alert>
            )}
            
            {incidencias.filter(i => i.estado !== 'resuelta').length > 0 && (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  Hay {incidencias.filter(i => i.estado !== 'resuelta').length} incidencia(s) pendiente(s) de resolución.
                </AlertDescription>
              </Alert>
            )}
            
            {fileStats.errores === 0 && fileStats.no_subidos === 0 && incidencias.filter(i => i.estado !== 'resuelta').length === 0 && (
              <Alert>
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>
                  No se detectaron problemas aparentes. El cierre parece estar en buen estado.
                </AlertDescription>
              </Alert>
            )}
          </div>
        </div>

      </CardContent>
    </Card>
  );
};

export default CierreActionMonitor;
