import React, { useState, useEffect } from "react";
import { X, Send, Upload, AlertTriangle, CheckCircle, MessageSquare, Clock, Eye, Lock } from "lucide-react";
import { crearResolucionIncidencia, obtenerHistorialIncidencia, aprobarIncidencia, rechazarIncidencia } from "../../../api/nomina";

const ModalResolucionIncidencia = ({ abierto, incidencia, onCerrar, onResolucionCreada }) => {
  const [comentario, setComentario] = useState('');
  const [adjunto, setAdjunto] = useState(null);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState('');
  const [historial, setHistorial] = useState([]);
  const [cargandoHistorial, setCargandoHistorial] = useState(false);
  const [usuarioActual, setUsuarioActual] = useState(null);

  useEffect(() => {
    if (abierto && incidencia?.id) {
      cargarHistorial();
      cargarUsuarioActual();
      // Limpiar formulario
      setComentario('');
      setAdjunto(null);
      setError('');
    }
  }, [abierto, incidencia]);

  const cargarUsuarioActual = () => {
    // Simulamos obtener el usuario actual del contexto o localStorage
    // En tu aplicación real, esto vendría del contexto de autenticación
    const userData = {
      id: 1,
      username: 'usuario_actual',
      first_name: 'Usuario',
      last_name: 'Actual',
      is_staff: false, // Cambiar según el rol real
      is_superuser: false
    };
    setUsuarioActual(userData);
  };

  const cargarHistorial = async () => {
    if (!incidencia?.id) return;
    
    setCargandoHistorial(true);
    try {
      const data = await obtenerHistorialIncidencia(incidencia.id);
      setHistorial(data.resoluciones || []);
    } catch (err) {
      console.error("Error cargando historial:", err);
    } finally {
      setCargandoHistorial(false);
    }
  };

  const manejarEnvioJustificacion = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!comentario.trim()) {
      setError('La justificación es requerida');
      return;
    }

    setEnviando(true);
    try {
      const formData = new FormData();
      formData.append('tipo_resolucion', 'justificacion');
      formData.append('comentario', comentario);
      
      if (adjunto) {
        formData.append('adjunto', adjunto);
      }

      const resolucionData = Object.fromEntries(formData.entries());
      await crearResolucionIncidencia(incidencia.id, resolucionData);
      
      // Recargar historial y notificar
      await cargarHistorial();
      if (onResolucionCreada) {
        onResolucionCreada();
      }
      
      // Limpiar formulario
      setComentario('');
      setAdjunto(null);
      
    } catch (err) {
      console.error("Error creando justificación:", err);
      setError('Error al enviar la justificación');
    } finally {
      setEnviando(false);
    }
  };

  const manejarComentarioSupervisor = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!comentario.trim()) {
      setError('El comentario es requerido');
      return;
    }

    setEnviando(true);
    try {
      const formData = new FormData();
      formData.append('tipo_resolucion', 'comentario');
      formData.append('comentario', comentario);
      
      if (adjunto) {
        formData.append('adjunto', adjunto);
      }

      const resolucionData = Object.fromEntries(formData.entries());
      await crearResolucionIncidencia(incidencia.id, resolucionData);
      
      // Recargar historial y notificar
      await cargarHistorial();
      if (onResolucionCreada) {
        onResolucionCreada();
      }
      
      // Limpiar formulario
      setComentario('');
      setAdjunto(null);
      
    } catch (err) {
      console.error("Error creando comentario:", err);
      setError('Error al enviar el comentario');
    } finally {
      setEnviando(false);
    }
  };

  const manejarAprobar = async () => {
    if (!window.confirm('¿Está seguro de aprobar esta incidencia? Quedará marcada como resuelta.')) {
      return;
    }

    setEnviando(true);
    try {
      await aprobarIncidencia(incidencia.id);
      
      // Recargar historial y notificar
      await cargarHistorial();
      if (onResolucionCreada) {
        onResolucionCreada();
      }
      
      // Cerrar modal
      setTimeout(() => {
        onCerrar();
      }, 1000);
      
    } catch (err) {
      console.error("Error aprobando incidencia:", err);
      setError('Error al aprobar la incidencia');
    } finally {
      setEnviando(false);
    }
  };

  const manejarRechazar = async () => {
    if (!comentario.trim()) {
      setError('Debe proporcionar un comentario para el rechazo');
      return;
    }

    if (!window.confirm('¿Está seguro de rechazar esta justificación? La incidencia volverá al estado pendiente.')) {
      return;
    }

    setEnviando(true);
    try {
      await rechazarIncidencia(incidencia.id, comentario);
      
      // Recargar historial y notificar
      await cargarHistorial();
      if (onResolucionCreada) {
        onResolucionCreada();
      }
      
      // Limpiar formulario
      setComentario('');
      
    } catch (err) {
      console.error("Error rechazando incidencia:", err);
      setError('Error al rechazar la incidencia');
    } finally {
      setEnviando(false);
    }
  };

  // Funciones de utilidad para determinar permisos y estados
  const esSupervisor = () => {
    return usuarioActual?.is_staff || usuarioActual?.is_superuser;
  };

  const esAnalista = () => {
    return !esSupervisor();
  };

  const obtenerEstadoIncidencia = () => {
    if (!historial.length) return 'pendiente';
    
    const ultimaResolucion = historial[historial.length - 1];
    
    if (ultimaResolucion.tipo_resolucion === 'aprobacion') {
      return 'resuelta';
    } else if (ultimaResolucion.tipo_resolucion === 'rechazo') {
      return 'pendiente';
    } else if (ultimaResolucion.tipo_resolucion === 'justificacion') {
      return 'en_espera_aprobacion';
    }
    
    return 'pendiente';
  };

  const puedeJustificar = () => {
    const estado = obtenerEstadoIncidencia();
    return esAnalista() && (estado === 'pendiente');
  };

  const puedeComentarSupervisor = () => {
    const estado = obtenerEstadoIncidencia();
    return esSupervisor() && estado === 'en_espera_aprobacion';
  };

  const puedeAprobarORechazar = () => {
    const estado = obtenerEstadoIncidencia();
    return esSupervisor() && estado === 'en_espera_aprobacion';
  };

  const esIncidenciaResuelta = () => {
    return obtenerEstadoIncidencia() === 'resuelta';
  };

  const esIncidenciaEsperandoAprobacion = () => {
    return obtenerEstadoIncidencia() === 'en_espera_aprobacion';
  };

  const manejarArchivoSeleccionado = (e) => {
    const archivo = e.target.files[0];
    if (archivo) {
      // Validar tamaño (máximo 5MB)
      if (archivo.size > 5 * 1024 * 1024) {
        setError('El archivo no puede superar los 5MB');
        return;
      }
      setAdjunto(archivo);
    }
  };

  const formatearFecha = (fecha) => {
    return new Date(fecha).toLocaleString('es-CL', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const obtenerIconoEstado = () => {
    const estado = obtenerEstadoIncidencia();
    switch (estado) {
      case 'pendiente':
        return <AlertTriangle className="w-5 h-5 text-yellow-400" />;
      case 'en_espera_aprobacion':
        return <Clock className="w-5 h-5 text-blue-400" />;
      case 'resuelta':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      default:
        return <AlertTriangle className="w-5 h-5 text-gray-400" />;
    }
  };

  const obtenerTextoEstado = () => {
    const estado = obtenerEstadoIncidencia();
    switch (estado) {
      case 'pendiente':
        return 'Pendiente';
      case 'en_espera_aprobacion':
        return 'En Espera de Aprobación';
      case 'resuelta':
        return 'Resuelta';
      default:
        return 'Desconocido';
    }
  };

  const obtenerIconoTipoResolucion = (tipo) => {
    switch (tipo) {
      case 'justificacion':
        return <MessageSquare className="w-4 h-4 text-blue-500" />;
      case 'comentario':
        return <MessageSquare className="w-4 h-4 text-gray-400" />;
      case 'aprobacion':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'rechazo':
        return <X className="w-4 h-4 text-red-500" />;
      default:
        return <MessageSquare className="w-4 h-4 text-gray-500" />;
    }
  };

  const obtenerColorBordeResolucion = (tipo) => {
    switch (tipo) {
      case 'justificacion':
        return 'border-blue-500';
      case 'comentario':
        return 'border-gray-500';
      case 'aprobacion':
        return 'border-green-600';
      case 'rechazo':
        return 'border-red-500';
      default:
        return 'border-gray-500';
    }
  };

  if (!abierto || !incidencia) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex justify-center items-center p-4">
      <div className="bg-gray-900 rounded-lg shadow-lg w-full max-w-4xl max-h-[85vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700 flex-shrink-0">
          <div>
            <h2 className="text-xl font-semibold text-white">
              Resolución de Incidencia
            </h2>
            <p className="text-gray-400 text-sm mt-1">
              {incidencia.rut_empleado} - {incidencia.get_tipo_incidencia_display || incidencia.tipo_incidencia}
            </p>
            {/* Indicador de estado */}
            <div className="flex items-center gap-2 mt-2">
              {obtenerIconoEstado()}
              <span className="text-sm font-medium text-white">
                Estado: {obtenerTextoEstado()}
              </span>
              {esSupervisor() && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-900/50 text-purple-300 border border-purple-500/30 ml-2">
                  Supervisor
                </span>
              )}
            </div>
          </div>
          <button
            onClick={onCerrar}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Detalles de la incidencia */}
        <div className="p-4 border-b border-gray-700 bg-gray-800/50 flex-shrink-0">
          <h3 className="text-md font-medium text-white mb-2">Detalles de la Incidencia</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-gray-400">Descripción:</span>
              <p className="text-white mt-1">{incidencia.descripcion}</p>
            </div>
            <div>
              <span className="text-gray-400">Prioridad:</span>
              <p className="text-white mt-1 capitalize">{incidencia.prioridad}</p>
            </div>
            {incidencia.valor_libro && (
              <div>
                <span className="text-gray-400">
                  {incidencia.tipo_incidencia === 'variacion_concepto' ? 
                    'Valor Período Actual:' : 
                    'Valor en Libro:'
                  }
                </span>
                <p className="text-white mt-1">{incidencia.valor_libro}</p>
              </div>
            )}
            {incidencia.valor_novedades && (
              <div>
                <span className="text-gray-400">
                  {incidencia.tipo_incidencia === 'variacion_concepto' ? 
                    'Valor Período Anterior:' : 
                    'Valor en Novedades:'
                  }
                </span>
                <p className="text-white mt-1">{incidencia.valor_novedades}</p>
              </div>
            )}
          </div>
        </div>

        {/* Contenido principal - Flujo de conversación */}
        <div className="flex-1 overflow-y-auto min-h-0">
          {/* Historial de conversación */}
          <div className="p-4">
            {cargandoHistorial ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              </div>
            ) : historial.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No hay conversación aún</p>
                <p className="text-sm">
                  {esAnalista() ? "Comienza escribiendo una justificación" : "Esperando justificación del analista"}
                </p>
              </div>
            ) : (
              <div className="space-y-4 mb-4">
                <h3 className="text-md font-medium text-white mb-3">Conversación</h3>
                {historial.map((resolucion, index) => (
                  <div key={resolucion.id} className={`bg-gray-800 rounded-lg p-4 border-l-4 ${obtenerColorBordeResolucion(resolucion.tipo_resolucion)}`}>
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-2">
                        {obtenerIconoTipoResolucion(resolucion.tipo_resolucion)}
                        <span className="font-medium text-white capitalize">
                          {resolucion.tipo_resolucion === 'justificacion' ? 'Justificación' : 
                           resolucion.tipo_resolucion === 'comentario' ? 'Comentario' :
                           resolucion.tipo_resolucion === 'aprobacion' ? 'Aprobación' :
                           resolucion.tipo_resolucion === 'rechazo' ? 'Rechazo' :
                           resolucion.tipo_resolucion}
                        </span>
                        <span className="text-gray-400">por</span>
                        <span className="text-blue-400 font-medium">
                          {resolucion.usuario?.first_name} {resolucion.usuario?.last_name}
                        </span>
                        {(resolucion.usuario?.is_staff || resolucion.usuario?.is_superuser) && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-900/50 text-purple-300 border border-purple-500/30">
                            Supervisor
                          </span>
                        )}
                      </div>
                      <span className="text-sm text-gray-400">
                        {formatearFecha(resolucion.fecha_creacion)}
                      </span>
                    </div>
                    
                    <p className="text-gray-300 mb-3 whitespace-pre-wrap">{resolucion.comentario}</p>
                    
                    {resolucion.adjunto && (
                      <div className="flex items-center text-blue-400 text-sm">
                        <Upload className="w-4 h-4 mr-1" />
                        <a href={resolucion.adjunto} target="_blank" rel="noopener noreferrer" className="hover:underline">
                          Ver adjunto
                        </a>
                      </div>
                    )}
                    
                    {/* Indicadores de estado */}
                    {resolucion.tipo_resolucion === 'aprobacion' && (
                      <div className="mt-3 inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-900/50 text-green-300 border border-green-500/30">
                        <CheckCircle className="w-4 h-4 mr-1" />
                        Incidencia Aprobada y Resuelta
                      </div>
                    )}
                    {resolucion.tipo_resolucion === 'rechazo' && (
                      <div className="mt-3 inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-900/50 text-red-300 border border-red-500/30">
                        <X className="w-4 h-4 mr-1" />
                        Justificación Rechazada - Vuelve a Pendiente
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Formulario de entrada según el estado y rol */}
            {!esIncidenciaResuelta() && (
              <div className="border-t border-gray-700 pt-4">
                {/* Caso 1: Analista puede justificar (estado pendiente) */}
                {puedeJustificar() && (
                  <div>
                    <h4 className="text-md font-medium text-blue-400 mb-3">
                      📝 Escribir Justificación (Analista)
                    </h4>
                    <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-3 mb-3">
                      <p className="text-blue-300 text-sm">
                        <strong>Instrucciones:</strong> Explica por qué esta incidencia es correcta o cómo debe resolverse. 
                        Una vez enviada, la incidencia pasará a "En Espera de Aprobación" y solo el supervisor podrá responder.
                      </p>
                    </div>
                    <form onSubmit={manejarEnvioJustificacion} className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Justificación *
                        </label>
                        <textarea
                          value={comentario}
                          onChange={(e) => setComentario(e.target.value)}
                          placeholder="Explica por qué esta incidencia es válida o cómo debe resolverse..."
                          rows={3}
                          className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                          required
                        />
                      </div>
                      
                      {/* Adjunto */}
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Adjunto (opcional)
                        </label>
                        <div className="flex items-center space-x-3">
                          <input
                            type="file"
                            onChange={manejarArchivoSeleccionado}
                            accept=".pdf,.doc,.docx,.xlsx,.xls,.png,.jpg,.jpeg"
                            className="hidden"
                            id="adjunto-input"
                          />
                          <label
                            htmlFor="adjunto-input"
                            className="flex items-center px-4 py-2 bg-gray-700 text-white rounded-lg cursor-pointer hover:bg-gray-600 transition-colors"
                          >
                            <Upload className="w-4 h-4 mr-2" />
                            Subir archivo
                          </label>
                          {adjunto && (
                            <span className="text-sm text-gray-300">
                              {adjunto.name}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          Máximo 5MB. Formatos: PDF, Word, Excel, imágenes
                        </p>
                      </div>

                      {/* Error */}
                      {error && (
                        <div className="bg-red-900/20 border border-red-500 rounded-lg p-3">
                          <div className="flex items-center text-red-400">
                            <AlertTriangle className="w-4 h-4 mr-2" />
                            {error}
                          </div>
                        </div>
                      )}

                      {/* Botones */}
                      <div className="flex justify-end space-x-3">
                        <button
                          type="button"
                          onClick={onCerrar}
                          className="px-4 py-2 text-gray-300 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors"
                        >
                          Cancelar
                        </button>
                        <button
                          type="submit"
                          disabled={enviando || !comentario.trim()}
                          className="flex items-center px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          {enviando ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                              Enviando...
                            </>
                          ) : (
                            <>
                              <Send className="w-4 h-4 mr-2" />
                              Enviar Justificación
                            </>
                          )}
                        </button>
                      </div>
                    </form>
                  </div>
                )}

                {/* Caso 2: Solo lectura para analista cuando está en espera de aprobación */}
                {esIncidenciaEsperandoAprobacion() && esAnalista() && (
                  <div className="text-center py-6">
                    <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
                      <div className="flex items-center justify-center mb-4">
                        <Clock className="w-8 h-8 text-blue-400 mr-3" />
                        <div>
                          <h4 className="text-lg font-medium text-blue-400">En Espera de Aprobación</h4>
                          <p className="text-blue-300 text-sm">El supervisor debe revisar y aprobar/rechazar tu justificación</p>
                        </div>
                      </div>
                      <div className="flex items-center justify-center space-x-2 text-blue-300">
                        <Eye className="w-4 h-4" />
                        <span className="text-sm">Modo solo lectura para analistas</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Caso 3: Supervisor puede comentar y aprobar/rechazar */}
                {puedeComentarSupervisor() && (
                  <div>
                    <h4 className="text-md font-medium text-purple-400 mb-3">
                      👨‍💼 Respuesta del Supervisor
                    </h4>
                    <div className="bg-purple-900/20 border border-purple-500/30 rounded-lg p-3 mb-3">
                      <p className="text-purple-300 text-sm">
                        <strong>Instrucciones:</strong> Puedes comentar la justificación del analista y luego aprobar o rechazar la incidencia.
                      </p>
                    </div>

                    {/* Formulario de comentario del supervisor */}
                    <form onSubmit={manejarComentarioSupervisor} className="space-y-3 mb-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Comentario del Supervisor (opcional)
                        </label>
                        <textarea
                          value={comentario}
                          onChange={(e) => setComentario(e.target.value)}
                          placeholder="Comentarios adicionales sobre la justificación..."
                          rows={3}
                          className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                      </div>
                      
                      {/* Adjunto */}
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Adjunto (opcional)
                        </label>
                        <div className="flex items-center space-x-3">
                          <input
                            type="file"
                            onChange={manejarArchivoSeleccionado}
                            accept=".pdf,.doc,.docx,.xlsx,.xls,.png,.jpg,.jpeg"
                            className="hidden"
                            id="adjunto-supervisor-input"
                          />
                          <label
                            htmlFor="adjunto-supervisor-input"
                            className="flex items-center px-4 py-2 bg-gray-700 text-white rounded-lg cursor-pointer hover:bg-gray-600 transition-colors"
                          >
                            <Upload className="w-4 h-4 mr-2" />
                            Subir archivo
                          </label>
                          {adjunto && (
                            <span className="text-sm text-gray-300">
                              {adjunto.name}
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex justify-end">
                        <button
                          type="submit"
                          disabled={enviando || !comentario.trim()}
                          className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          {enviando ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                              Enviando...
                            </>
                          ) : (
                            <>
                              <Send className="w-4 h-4 mr-2" />
                              Agregar Comentario
                            </>
                          )}
                        </button>
                      </div>
                    </form>

                    {/* Botones de Aprobación/Rechazo */}
                    <div className="border-t border-gray-700 pt-3">
                      <h5 className="text-sm font-medium text-white mb-3">Decisión Final</h5>
                      <div className="flex justify-center space-x-4">
                        <button
                          onClick={manejarAprobar}
                          disabled={enviando}
                          className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          {enviando ? (
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          ) : (
                            <CheckCircle className="w-4 h-4 mr-2" />
                          )}
                          Aprobar Incidencia
                        </button>
                        
                        <button
                          onClick={manejarRechazar}
                          disabled={enviando || !comentario.trim()}
                          className="flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          title={!comentario.trim() ? "Debe agregar un comentario antes de rechazar" : ""}
                        >
                          {enviando ? (
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          ) : (
                            <X className="w-4 h-4 mr-2" />
                          )}
                          Rechazar y Volver a Pendiente
                        </button>
                      </div>
                      {!comentario.trim() && (
                        <p className="text-center text-yellow-400 text-sm mt-2">
                          💡 Agregue un comentario explicando el motivo del rechazo
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {/* Error general */}
                {error && !puedeJustificar() && !puedeComentarSupervisor() && (
                  <div className="bg-red-900/20 border border-red-500 rounded-lg p-3">
                    <div className="flex items-center text-red-400">
                      <AlertTriangle className="w-4 h-4 mr-2" />
                      {error}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Caso 4: Incidencia resuelta - Solo vista */}
            {esIncidenciaResuelta() && (
              <div className="text-center py-6">
                <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-4">
                  <div className="flex items-center justify-center mb-3">
                    <CheckCircle className="w-6 h-6 text-green-400 mr-2" />
                    <div>
                      <h4 className="text-md font-medium text-green-400">Incidencia Resuelta</h4>
                      <p className="text-green-300 text-sm">Esta incidencia ha sido aprobada y marcada como resuelta</p>
                    </div>
                  </div>
                  <button
                    onClick={onCerrar}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    Cerrar
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModalResolucionIncidencia;
