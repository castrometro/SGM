import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "../../ui/card";
import { Badge } from "../../ui/badge";
import { Button } from "../../ui/button";
import { Alert, AlertDescription } from "../../ui/alert";
import { Textarea } from "../../ui/textarea";
import { Input } from "../../ui/input";
import { 
  Loader2, 
  AlertTriangle, 
  TrendingUp, 
  TrendingDown, 
  MessageSquare, 
  CheckCircle, 
  XCircle, 
  Search,
  Filter,
  FileText,
  User,
  Calendar,
  DollarSign
} from "lucide-react";
import { 
  obtenerIncidenciasVariacion, 
  justificarIncidenciaVariacion, 
  aprobarIncidenciaVariacion, 
  rechazarIncidenciaVariacion 
} from "../../api/nomina";

const IncidenciasVariacionSalarial = ({ cierre, onIncidenciasResueltas }) => {
  const [incidencias, setIncidencias] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");
  const [filtros, setFiltros] = useState({
    busqueda: "",
    estado: "",
    tipo_variacion: ""
  });
  const [incidenciaSeleccionada, setIncidenciaSeleccionada] = useState(null);
  const [mensaje, setMensaje] = useState("");
  const [procesando, setProcesando] = useState(false);

  useEffect(() => {
    if (cierre?.id) {
      cargarIncidencias();
    }
  }, [cierre?.id, filtros]);

  const cargarIncidencias = async () => {
    setCargando(true);
    setError("");
    
    try {
      const data = await obtenerIncidenciasVariacion(cierre.id, filtros);
      setIncidencias(Array.isArray(data.results) ? data.results : data);
    } catch (err) {
      console.error("Error cargando incidencias:", err);
      setError("Error al cargar las incidencias de variación salarial");
    } finally {
      setCargando(false);
    }
  };

  const manejarJustificar = async (incidenciaId) => {
    if (!mensaje.trim()) {
      setError("La justificación es obligatoria");
      return;
    }

    setProcesando(true);
    setError("");

    try {
      await justificarIncidenciaVariacion(incidenciaId, mensaje);
      setMensaje("");
      setIncidenciaSeleccionada(null);
      await cargarIncidencias();
    } catch (err) {
      console.error("Error justificando incidencia:", err);
      setError("Error al enviar la justificación");
    } finally {
      setProcesando(false);
    }
  };

  const manejarAprobar = async (incidenciaId) => {
    setProcesando(true);
    setError("");

    try {
      await aprobarIncidenciaVariacion(incidenciaId, mensaje);
      setMensaje("");
      setIncidenciaSeleccionada(null);
      await cargarIncidencias();
      
      // Verificar si todas las incidencias están resueltas
      const incidenciasActualizadas = await obtenerIncidenciasVariacion(cierre.id);
      const pendientes = incidenciasActualizadas.filter(inc => inc.estado === 'pendiente');
      if (pendientes.length === 0) {
        onIncidenciasResueltas();
      }
    } catch (err) {
      console.error("Error aprobando incidencia:", err);
      setError("Error al aprobar la incidencia");
    } finally {
      setProcesando(false);
    }
  };

  const manejarRechazar = async (incidenciaId) => {
    if (!mensaje.trim()) {
      setError("El comentario es obligatorio al rechazar");
      return;
    }

    setProcesando(true);
    setError("");

    try {
      await rechazarIncidenciaVariacion(incidenciaId, mensaje);
      setMensaje("");
      setIncidenciaSeleccionada(null);
      await cargarIncidencias();
    } catch (err) {
      console.error("Error rechazando incidencia:", err);
      setError("Error al rechazar la incidencia");
    } finally {
      setProcesando(false);
    }
  };

  const obtenerBadgeEstado = (estado) => {
    const colores = {
      'pendiente': 'bg-yellow-100 text-yellow-800',
      'justificada': 'bg-blue-100 text-blue-800',
      'aprobada': 'bg-green-100 text-green-800',
      'rechazada': 'bg-red-100 text-red-800'
    };
    return colores[estado] || 'bg-gray-100 text-gray-800';
  };

  const obtenerIconoTipo = (tipo) => {
    return tipo === 'aumento' ? TrendingUp : TrendingDown;
  };

  const formatearFecha = (fecha) => {
    return new Date(fecha).toLocaleDateString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatearMoneda = (valor) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0
    }).format(valor);
  };

  const incidenciasFiltradas = incidencias.filter(inc => {
    const matchBusqueda = !filtros.busqueda || 
      inc.empleado_nombre.toLowerCase().includes(filtros.busqueda.toLowerCase()) ||
      inc.empleado_rut.includes(filtros.busqueda);
    const matchEstado = !filtros.estado || inc.estado === filtros.estado;
    const matchTipo = !filtros.tipo_variacion || inc.tipo_variacion === filtros.tipo_variacion;
    return matchBusqueda && matchEstado && matchTipo;
  });

  const estadisticas = {
    total: incidencias.length,
    pendientes: incidencias.filter(inc => inc.estado === 'pendiente').length,
    justificadas: incidencias.filter(inc => inc.estado === 'justificada').length,
    aprobadas: incidencias.filter(inc => inc.estado === 'aprobada').length,
    rechazadas: incidencias.filter(inc => inc.estado === 'rechazada').length,
  };

  if (cargando) {
    return (
      <Card className="bg-white shadow-sm">
        <CardContent className="p-6">
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-blue-500 mr-2" />
            <span className="text-gray-600">Cargando incidencias...</span>
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
            <AlertTriangle className="w-5 h-5 text-orange-500" />
            Incidencias de Variación Salarial
          </CardTitle>
          <Badge className="bg-orange-100 text-orange-800">
            {estadisticas.pendientes} pendientes
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {error && (
          <Alert className="border-red-200 bg-red-50">
            <AlertDescription className="text-red-700">{error}</AlertDescription>
          </Alert>
        )}

        {/* Estadísticas */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 bg-gray-50 p-4 rounded-lg">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{estadisticas.total}</div>
            <div className="text-sm text-gray-500">Total</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{estadisticas.pendientes}</div>
            <div className="text-sm text-gray-500">Pendientes</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{estadisticas.justificadas}</div>
            <div className="text-sm text-gray-500">Justificadas</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{estadisticas.aprobadas}</div>
            <div className="text-sm text-gray-500">Aprobadas</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{estadisticas.rechazadas}</div>
            <div className="text-sm text-gray-500">Rechazadas</div>
          </div>
        </div>

        {/* Filtros */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-gray-50 p-4 rounded-lg">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Buscar empleado
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                placeholder="Nombre o RUT..."
                value={filtros.busqueda}
                onChange={(e) => setFiltros({...filtros, busqueda: e.target.value})}
                className="pl-9"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Estado
            </label>
            <select
              value={filtros.estado}
              onChange={(e) => setFiltros({...filtros, estado: e.target.value})}
              className="w-full p-2 border border-gray-300 rounded-md"
            >
              <option value="">Todos</option>
              <option value="pendiente">Pendiente</option>
              <option value="justificada">Justificada</option>
              <option value="aprobada">Aprobada</option>
              <option value="rechazada">Rechazada</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tipo de variación
            </label>
            <select
              value={filtros.tipo_variacion}
              onChange={(e) => setFiltros({...filtros, tipo_variacion: e.target.value})}
              className="w-full p-2 border border-gray-300 rounded-md"
            >
              <option value="">Todos</option>
              <option value="aumento">Aumento</option>
              <option value="disminucion">Disminución</option>
            </select>
          </div>
        </div>

        {/* Lista de incidencias */}
        <div className="space-y-4">
          {incidenciasFiltradas.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No hay incidencias</h3>
              <p className="text-gray-500">
                {incidencias.length === 0 
                  ? "No se encontraron incidencias de variación salarial."
                  : "No hay incidencias que coincidan con los filtros aplicados."
                }
              </p>
            </div>
          ) : (
            incidenciasFiltradas.map((incidencia) => {
              const IconoTipo = obtenerIconoTipo(incidencia.tipo_variacion);
              const esSeleccionada = incidenciaSeleccionada === incidencia.id;
              
              return (
                <div
                  key={incidencia.id}
                  className={`border rounded-lg p-4 ${esSeleccionada ? 'border-blue-300 bg-blue-50' : 'border-gray-200 bg-white'}`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <IconoTipo className={`w-5 h-5 ${incidencia.tipo_variacion === 'aumento' ? 'text-green-500' : 'text-red-500'}`} />
                      <div>
                        <h4 className="font-medium text-gray-900">{incidencia.empleado_nombre}</h4>
                        <p className="text-sm text-gray-500">{incidencia.empleado_rut}</p>
                      </div>
                    </div>
                    <Badge className={obtenerBadgeEstado(incidencia.estado)}>
                      {incidencia.estado}
                    </Badge>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
                    <div className="flex items-center gap-2">
                      <DollarSign className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-600">
                        {formatearMoneda(incidencia.sueldo_anterior)} → {formatearMoneda(incidencia.sueldo_actual)}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-600">
                        Variación: {incidencia.porcentaje_variacion}%
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-600">
                        Creada: {formatearFecha(incidencia.fecha_creacion)}
                      </span>
                    </div>
                  </div>

                  {incidencia.justificacion && (
                    <div className="mb-3 p-3 bg-blue-50 rounded-lg">
                      <h5 className="font-medium text-blue-900 mb-1">Justificación</h5>
                      <p className="text-sm text-blue-700">{incidencia.justificacion}</p>
                    </div>
                  )}

                  {incidencia.comentario_supervisor && (
                    <div className="mb-3 p-3 bg-gray-50 rounded-lg">
                      <h5 className="font-medium text-gray-900 mb-1">Comentario del supervisor</h5>
                      <p className="text-sm text-gray-700">{incidencia.comentario_supervisor}</p>
                    </div>
                  )}

                  {/* Acciones */}
                  <div className="flex gap-2 pt-3 border-t">
                    {incidencia.estado === 'pendiente' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setIncidenciaSeleccionada(esSeleccionada ? null : incidencia.id)}
                        className="flex items-center gap-1"
                      >
                        <MessageSquare className="w-4 h-4" />
                        Justificar
                      </Button>
                    )}
                    
                    {incidencia.estado === 'justificada' && (
                      <>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setIncidenciaSeleccionada(esSeleccionada ? null : incidencia.id)}
                          className="flex items-center gap-1"
                        >
                          <MessageSquare className="w-4 h-4" />
                          Responder
                        </Button>
                      </>
                    )}
                  </div>

                  {/* Panel de acciones expandido */}
                  {esSeleccionada && (
                    <div className="mt-4 p-4 bg-gray-50 rounded-lg border-t">
                      <div className="space-y-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            {incidencia.estado === 'pendiente' ? 'Justificación' : 'Comentario'}
                          </label>
                          <Textarea
                            value={mensaje}
                            onChange={(e) => setMensaje(e.target.value)}
                            placeholder={
                              incidencia.estado === 'pendiente' 
                                ? "Ingrese la justificación para esta variación salarial..."
                                : "Ingrese un comentario..."
                            }
                            rows={3}
                            className="w-full"
                          />
                        </div>
                        <div className="flex gap-2">
                          {incidencia.estado === 'pendiente' && (
                            <Button
                              onClick={() => manejarJustificar(incidencia.id)}
                              disabled={procesando || !mensaje.trim()}
                              className="bg-blue-600 hover:bg-blue-700 text-white"
                            >
                              {procesando ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                              Enviar Justificación
                            </Button>
                          )}
                          
                          {incidencia.estado === 'justificada' && (
                            <>
                              <Button
                                onClick={() => manejarAprobar(incidencia.id)}
                                disabled={procesando}
                                className="bg-green-600 hover:bg-green-700 text-white flex items-center gap-1"
                              >
                                {procesando ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                                Aprobar
                              </Button>
                              <Button
                                onClick={() => manejarRechazar(incidencia.id)}
                                disabled={procesando || !mensaje.trim()}
                                className="bg-red-600 hover:bg-red-700 text-white flex items-center gap-1"
                              >
                                {procesando ? <Loader2 className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />}
                                Rechazar
                              </Button>
                            </>
                          )}
                          
                          <Button
                            variant="outline"
                            onClick={() => {
                              setIncidenciaSeleccionada(null);
                              setMensaje("");
                            }}
                            disabled={procesando}
                          >
                            Cancelar
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default IncidenciasVariacionSalarial;
