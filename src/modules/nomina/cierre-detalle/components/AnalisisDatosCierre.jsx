import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "../../../../components/ui/card";
import { Badge } from "../../../../components/ui/badge";
import { Button } from "../../../../components/ui/button";
import { Alert, AlertDescription } from "../../../../components/ui/alert";
import { Loader2, TrendingUp, TrendingDown, Minus, BarChart3, CheckCircle } from "lucide-react";
import { obtenerAnalisisDatos } from "../api/cierreDetalle.api";

const AnalisisDatosCierre = ({ cierre, onFinalizarCierre }) => {
  const [analisis, setAnalisis] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (cierre?.id) {
      cargarAnalisis();
    }
  }, [cierre?.id]);

  const cargarAnalisis = async () => {
    setCargando(true);
    setError("");
    
    try {
      const data = await obtenerAnalisisDatos(cierre.id);
      console.log("🔍 DEBUG - Datos análisis recibidos:", data);
      
      // Manejar respuesta del ViewSet (puede ser array o objeto con results)
      let analisisData = null;
      if (Array.isArray(data)) {
        analisisData = data.length > 0 ? data[0] : null;
      } else if (data.results && Array.isArray(data.results)) {
        analisisData = data.results.length > 0 ? data.results[0] : null;
      } else if (data.id) {
        // Es un objeto directo
        analisisData = data;
      }
      
      console.log("🔍 DEBUG - Análisis procesado:", analisisData);
      setAnalisis(analisisData);
    } catch (err) {
      console.error("Error cargando análisis:", err);
      setError("Error al cargar los datos del análisis");
    } finally {
      setCargando(false);
    }
  };

  const formatearFecha = (fecha) => {
    if (!fecha) return "N/A";
    return new Date(fecha).toLocaleDateString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const obtenerTendencia = (actual, anterior) => {
    if (anterior === 0) return { tipo: "nuevo", color: "bg-blue-100 text-blue-800" };
    if (actual > anterior) return { tipo: "up", color: "bg-green-100 text-green-800", icono: TrendingUp };
    if (actual < anterior) return { tipo: "down", color: "bg-red-100 text-red-800", icono: TrendingDown };
    return { tipo: "same", color: "bg-gray-100 text-gray-800", icono: Minus };
  };

  const EstadisticaComparativa = ({ titulo, actual, anterior, descripcion }) => {
    console.log(`🔍 DEBUG - ${titulo}:`, { actual, anterior, tipo_actual: typeof actual, tipo_anterior: typeof anterior });
    
    const tendencia = obtenerTendencia(actual || 0, anterior || 0);
    const diferencia = (actual || 0) - (anterior || 0);
    const IconoTendencia = tendencia.icono;

    return (
      <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-medium text-gray-600">{titulo}</h4>
          {IconoTendencia && (
            <Badge className={`${tendencia.color} flex items-center gap-1 px-2 py-1`}>
              <IconoTendencia className="w-3 h-3" />
              {diferencia > 0 ? `+${diferencia}` : diferencia}
            </Badge>
          )}
        </div>
        <div className="space-y-1">
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Mes actual:</span>
            <span className="font-medium">{(actual || 0).toLocaleString()}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Mes anterior:</span>
            <span className="font-medium">{(anterior || 0).toLocaleString()}</span>
          </div>
        </div>
        {descripcion && (
          <p className="text-xs text-gray-500 mt-2">{descripcion}</p>
        )}
      </div>
    );
  };

  if (cargando) {
    return (
      <Card className="bg-white shadow-sm">
        <CardContent className="p-6">
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-blue-500 mr-2" />
            <span className="text-gray-600">Cargando análisis...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="bg-white shadow-sm">
        <CardContent className="p-6">
          <Alert className="border-red-200 bg-red-50">
            <AlertDescription className="text-red-700">{error}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (!analisis) {
    return (
      <Card className="bg-white shadow-sm">
        <CardContent className="p-6">
          <div className="text-center py-8">
            <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No hay análisis disponible</h3>
            <p className="text-gray-500">
              El análisis de datos aún no ha sido ejecutado para este cierre.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-white shadow-sm">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-blue-500" />
            Análisis de Datos del Cierre
          </CardTitle>
          <Badge className="bg-blue-100 text-blue-800">
            Ejecutado el {formatearFecha(analisis.fecha_analisis)}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Información del análisis */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="font-medium text-gray-900 mb-3">Información del Análisis</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <span className="text-sm text-gray-500">Período actual:</span>
              <p className="font-medium">{analisis.periodo_actual}</p>
            </div>
            <div>
              <span className="text-sm text-gray-500">Período anterior:</span>
              <p className="font-medium">{analisis.periodo_anterior || "N/A"}</p>
            </div>
            <div>
              <span className="text-sm text-gray-500">Tolerancia aplicada:</span>
              <p className="font-medium">{analisis.tolerancia_variacion}%</p>
            </div>
            <div>
              <span className="text-sm text-gray-500">Incidencias generadas:</span>
              <p className="font-medium">{analisis.incidencias_generadas || 0}</p>
            </div>
          </div>
        </div>

        {/* Estadísticas comparativas */}
        <div>
          <h3 className="font-medium text-gray-900 mb-4">Comparación Mensual</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <EstadisticaComparativa
              titulo="Empleados"
              actual={analisis.empleados_actual}
              anterior={analisis.empleados_anterior}
              descripcion="Total de empleados en nómina"
            />
            <EstadisticaComparativa
              titulo="Ingresos"
              actual={analisis.ingresos_actual}
              anterior={analisis.ingresos_anterior}
              descripcion="Nuevos ingresos del mes"
            />
            <EstadisticaComparativa
              titulo="Finiquitos"
              actual={analisis.finiquitos_actual}
              anterior={analisis.finiquitos_anterior}
              descripcion="Finiquitos procesados"
            />
            <EstadisticaComparativa
              titulo="Ausentismos"
              actual={analisis.ausentismos_actual}
              anterior={analisis.ausentismos_anterior}
              descripcion="Registros de ausentismo"
            />
          </div>
        </div>

        {/* Estado del análisis */}
        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <h3 className="font-medium text-green-900">Análisis Completado</h3>
          </div>
          <p className="text-sm text-green-700">
            El análisis de datos ha sido completado exitosamente. Se han generado {analisis.incidencias_generadas || 0} incidencias 
            de variación salarial que requieren revisión.
          </p>
        </div>

        {/* Botón de finalizar cierre (solo si no hay incidencias pendientes) */}
        {(analisis.incidencias_generadas === 0 || cierre?.estado === 'sin_incidencias') && (
          <div className="pt-4 border-t">
            <Button
              onClick={onFinalizarCierre}
              className="w-full bg-green-600 hover:bg-green-700 text-white"
            >
              <CheckCircle className="w-4 h-4 mr-2" />
              Finalizar Cierre de Nómina
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AnalisisDatosCierre;
