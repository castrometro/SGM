import React, { useState, useEffect } from "react";
import { X, Send, Upload, AlertTriangle, CheckCircle, MessageSquare, Clock, Eye, Lock, Download, Image as ImageIcon } from "lucide-react";
import { crearResolucionIncidencia, obtenerHistorialIncidencia, aprobarIncidencia, rechazarIncidencia, confirmarDesaparicionIncidencia } from "../../api/cierreDetalle.api";
import { ESTADOS_INCIDENCIA } from "../../../../../utils/incidenciaUtils";

// Base de media: si la API está en 8000 y Vite en 5174, necesitamos apuntar al host backend
const MEDIA_BASE = import.meta?.env?.VITE_MEDIA_BASE_URL || 'http://172.17.11.18:8000';

const construirURLAdjunto = (urlRelativa) => {
  if (!urlRelativa) return null;
  // Si ya es absoluta devolver directamente
  if (/^https?:\/\//i.test(urlRelativa)) return urlRelativa;
  // Asegurar que empieza con /media/
  const path = urlRelativa.startsWith('/media/') ? urlRelativa : (urlRelativa.startsWith('media/') ? '/' + urlRelativa : '/media/' + urlRelativa.replace(/^\/+/, ''));
  return MEDIA_BASE.replace(/\/$/, '') + path;
};

const esImagen = (url) => /\.(png|jpe?g|webp)$/i.test(url || '');

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
    // Obtener el usuario actual del localStorage como en el resto de la aplicación
    try {
      const usuarioData = JSON.parse(localStorage.getItem("usuario"));
      if (usuarioData) {
        // Mapear la estructura del usuario de tu sistema al formato esperado
        const userData = {
          id: usuarioData.id,
          username: usuarioData.correo_bdo || usuarioData.correo || 'usuario',
          first_name: usuarioData.nombre || 'Usuario',
          last_name: usuarioData.apellido || 'Actual',
          // Determinar si es supervisor basado en el tipo de usuario
          is_staff: usuarioData.tipo_usuario === 'supervisor' || usuarioData.tipo_usuario === 'gerente',
          is_superuser: usuarioData.tipo_usuario === 'gerente'
        };
        setUsuarioActual(userData);
        console.log('Usuario cargado para modal:', userData);
      } else {
        console.warn('No se encontró usuario en localStorage');
        // Fallback en caso de no encontrar usuario
        setUsuarioActual({
          id: 0,
          username: 'desconocido',
          first_name: 'Usuario',
          last_name: 'Desconocido',
          is_staff: false,
          is_superuser: false
        });
      }
    } catch (error) {
      console.error('Error cargando usuario actual:', error);
      // Fallback en caso de error
      setUsuarioActual({
        id: 0,
        username: 'error',
        first_name: 'Error',
        last_name: 'Usuario',
        is_staff: false,
        is_superuser: false
      });
    }
  };

  const cargarHistorial = async () => {
    if (!incidencia?.id) return;
    
    setCargandoHistorial(true);
    try {
      const data = await obtenerHistorialIncidencia(incidencia.id);
      console.log('📋 Historial cargado:', data);
      
      // Debug simplificado - solo mostrar lo esencial
      if (data.resoluciones && data.resoluciones.length > 0) {
        console.log('🔄 Estado actual de la conversación:');
        data.resoluciones.forEach((resolucion, index) => {
          console.log(`  ${index + 1}. ${resolucion.tipo_resolucion} - ${resolucion.usuario?.first_name} ${resolucion.usuario?.last_name}`);
        });
        
        const ultimaResolucion = data.resoluciones[data.resoluciones.length - 1];
        console.log(`✅ Último mensaje: ${ultimaResolucion.tipo_resolucion}`);
        console.log(`🎯 Estado conversación: ${ultimaResolucion.tipo_resolucion === 'aprobacion' ? 'RESUELTA' : 'EN PROGRESO'}`);
      }
      
      setHistorial(data.resoluciones || []);
    } catch (err) {
      console.error("❌ Error cargando historial:", err);
    } finally {
      setCargandoHistorial(false);
    }
  };

  const esSistema = (res) => {
    try {
      const correoSistema = (import.meta?.env?.VITE_SYSTEM_USER_EMAIL || 'sistema@sgm.local').toLowerCase();
      const correo = (res?.usuario_correo || res?.usuario?.correo_bdo || '').toLowerCase();
      const nombre = (res?.usuario?.first_name || '').toLowerCase();
      // Detectar por correo preferentemente; fallback por nombre "Sistema"
      return correo && correo === correoSistema || nombre === 'sistema';
    } catch {
      return false;
    }
  };

  const manejarEnviarMensaje = async (e) => {
    e.preventDefault();
    setError('');
    
    // Requerir mensaje solo del analista; para supervisor es opcional (puede adjuntar archivo)
    if (esAnalista() && !comentario.trim()) {
      setError('El mensaje es requerido');
      return;
    }

    setEnviando(true);
    try {
      const formData = new FormData();
      // Determinar el tipo de resolución basado en el rol
      // Mensaje neutral de conversación:
      // - Analista: justificación
      // - Supervisor: consulta (comentario/pregunta)
      formData.append('tipo_resolucion', esAnalista() ? 'justificacion' : 'consulta');
      // Comentario opcional para supervisor (permite mandar solo adjunto)
      if (comentario && comentario.trim()) {
        formData.append('comentario', comentario.trim());
      }
      if (adjunto) {
        formData.append('adjunto', adjunto);
      }
      // Enviar como FormData para preservar adjuntos
      await crearResolucionIncidencia(incidencia.id, formData);
      
      // Recargar historial y notificar
      await cargarHistorial();
      if (onResolucionCreada) {
        onResolucionCreada();
      }
      
      // Limpiar formulario
      setComentario('');
      setAdjunto(null);
      
    } catch (err) {
      console.error("Error enviando mensaje:", err);
      setError('Error al enviar el mensaje');
    } finally {
      setEnviando(false);
    }
  };

  const manejarAprobar = async () => {
    // Verificar que realmente se pueda aprobar
    if (esIncidenciaResuelta()) {
      setError('Esta incidencia ya está resuelta');
      return;
    }

    if (!puedeAprobarORechazar()) {
      setError('No tienes permisos para aprobar en este momento');
      return;
    }

    if (!window.confirm('¿Está seguro de aprobar esta incidencia? Quedará marcada como resuelta.')) {
      return;
    }

    setEnviando(true);
    setError(''); // Limpiar errores previos
    
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
      
      // Manejar diferentes tipos de errores
      if (err.response?.status === 403) {
        setError('No tienes permisos para aprobar esta incidencia o ya está resuelta');
      } else if (err.response?.status === 404) {
        setError('La incidencia no fue encontrada');
      } else if (err.response?.status === 400) {
        setError(err.response?.data?.error || 'Error en la solicitud - La incidencia puede estar en un estado inválido');
      } else {
        setError('Error al aprobar la incidencia. Intenta nuevamente.');
      }
    } finally {
      setEnviando(false);
    }
  };

  const manejarRechazar = async () => {
    if (!comentario.trim()) {
      setError('Debe proporcionar un comentario para el rechazo');
      return;
    }

    // Verificar permisos antes de proceder
    if (esIncidenciaResuelta()) {
      setError('Esta incidencia ya está resuelta y no puede ser rechazada');
      return;
    }

    if (!puedeAprobarORechazar()) {
      setError('No tienes permisos para rechazar en este momento');
      return;
    }

    if (!window.confirm('¿Está seguro de rechazar esta justificación? El analista podrá responder y continuar la conversación.')) {
      return;
    }

    setEnviando(true);
    setError(''); // Limpiar errores previos
    
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
      
      // Manejar diferentes tipos de errores
      if (err.response?.status === 403) {
        setError('No tienes permisos para rechazar esta incidencia o ya está resuelta');
      } else if (err.response?.status === 404) {
        setError('La incidencia no fue encontrada');
      } else if (err.response?.status === 400) {
        setError(err.response?.data?.error || 'Error en la solicitud - La incidencia puede estar en un estado inválido');
      } else {
        setError('Error al rechazar la incidencia. Intenta nuevamente.');
      }
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

  const obtenerEstadoConversacion = () => {
    if (!historial.length) {
      return 'turno_analista'; // El analista inicia la conversación
    }
    
    const ultimaResolucion = historial[historial.length - 1];
    
    // ✅ LÓGICA SIMPLIFICADA - Solo verificar tipo_resolucion
    if (ultimaResolucion.tipo_resolucion === 'aprobacion') {
      return 'resuelta';
    }
    
    // Determinar turno basado en el último mensaje
    // Supervisor: 'consulta', 'rechazo' → Turno del analista
    // Analista: 'justificacion' → Turno del supervisor
    const ultimoEraDeSupervisor = ['consulta', 'rechazo'].includes(ultimaResolucion.tipo_resolucion);
    
    return ultimoEraDeSupervisor ? 'turno_analista' : 'turno_supervisor';
  };

  const puedeEscribirAnalista = () => {
    const estado = obtenerEstadoConversacion();
    return esAnalista() && estado === 'turno_analista';
  };

  const puedeEscribirSupervisor = () => {
    const estado = obtenerEstadoConversacion();
    return esSupervisor() && estado === 'turno_supervisor';
  };

  const puedeAprobarORechazar = () => {
    const estado = obtenerEstadoConversacion();
    return esSupervisor() && estado === 'turno_supervisor';
  };

  const esIncidenciaResuelta = () => {
    return obtenerEstadoConversacion() === 'resuelta';
  };

  const esConfirmacionPendiente = () => {
    try {
      return incidencia?.estado === ESTADOS_INCIDENCIA.RESOLUCION_SUPERVISOR_PENDIENTE;
    } catch {
      return false;
    }
  };

  const manejarConfirmarDesaparicion = async () => {
    if (!esConfirmacionPendiente()) return;
    if (!window.confirm('¿Confirmar desaparición de esta incidencia?')) return;
    setEnviando(true);
    setError('');
    try {
      await confirmarDesaparicionIncidencia(incidencia.id, 'Confirmación desde modal');
      await cargarHistorial();
      if (onResolucionCreada) onResolucionCreada();
      setTimeout(() => onCerrar && onCerrar(), 500);
    } catch (e) {
      console.error(e);
      setError(e.message || 'Error confirmando desaparición');
    } finally {
      setEnviando(false);
    }
  };

  const obtenerMensajeTurno = () => {
    const estado = obtenerEstadoConversacion();
    if (estado === 'resuelta') {
      return 'Incidencia resuelta';
    } else if (estado === 'turno_analista') {
      return esAnalista() ? 'Es tu turno para responder' : 'Esperando respuesta del analista';
    } else if (estado === 'turno_supervisor') {
      return esSupervisor() ? 'Es tu turno para responder' : 'Esperando respuesta del supervisor';
    }
    return '';
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
    if (!fecha) return 'Fecha no disponible';
    
    try {
      // Probar diferentes campos de fecha que podrían venir del backend
      const fechaAUsar = fecha.fecha_creacion || fecha.fecha_resolucion || fecha.created_at || fecha.timestamp || fecha;
      
      if (!fechaAUsar) return 'Fecha no disponible';
      
      const fechaObj = new Date(fechaAUsar);
      
      // Verificar si la fecha es válida
      if (isNaN(fechaObj.getTime())) {
        console.warn('Fecha inválida recibida:', fechaAUsar);
        return 'Fecha inválida';
      }
      
      return fechaObj.toLocaleString('es-CL', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      console.error('Error formateando fecha:', error, fecha);
      return 'Error en fecha';
    }
  };

  const obtenerIconoEstado = () => {
    const estado = obtenerEstadoConversacion();
    switch (estado) {
      case 'turno_analista':
        return <Clock className="w-5 h-5 text-blue-400" />;
      case 'turno_supervisor':
        return <Clock className="w-5 h-5 text-purple-400" />;
      case 'resuelta':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      default:
        return <AlertTriangle className="w-5 h-5 text-gray-400" />;
    }
  };

  const obtenerTextoEstado = () => {
    const estado = obtenerEstadoConversacion();
    switch (estado) {
      case 'turno_analista':
        return 'En conversación - Turno del Analista';
      case 'turno_supervisor':
        return 'En conversación - Turno del Supervisor';
      case 'resuelta':
        return 'Resuelta';
      default:
        return 'Pendiente';
    }
  };

  const obtenerIconoTipoResolucion = (tipo) => {
    switch (tipo) {
      case 'justificacion':
        return <MessageSquare className="w-4 h-4 text-blue-500" />;
      case 'consulta':
        return <MessageSquare className="w-4 h-4 text-purple-500" />;
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
      case 'consulta':
        return 'border-purple-500';
      case 'aprobacion':
        return 'border-green-600';
      case 'rechazo':
        return 'border-red-500';
      default:
        return 'border-gray-500';
    }
  };

  const obtenerTextoTipoResolucion = (tipo, usuario) => {
    const esSupervisorMensaje = usuario?.is_staff || usuario?.is_superuser;
    
    switch (tipo) {
      case 'justificacion':
        return 'Justificación del Analista';
      case 'consulta':
        return 'Consulta del Supervisor';
      case 'aprobacion':
        return 'Aprobación Final del Supervisor';
      case 'rechazo':
        return 'Rechazo del Supervisor';
      default:
        return tipo;
    }
  };

  if (!abierto || !incidencia) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex justify-center items-center p-4">
      <div className="bg-gray-900 rounded-lg shadow-lg w-full max-w-4xl max-h-[85vh] overflow-hidden flex flex-col">
        {/* Encabezado unificado + Resumen colapsable */}
        <div className="p-4 border-b border-gray-700 bg-gray-900/90 flex-shrink-0">
          <div className="flex items-start justify-between">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                {obtenerIconoEstado()}
                <h2 className="text-lg md:text-xl font-semibold text-white truncate">
                  Resolución de Incidencia
                </h2>
                {esSupervisor() && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-900/50 text-purple-300 border border-purple-500/30">
                    Supervisor
                  </span>
                )}
              </div>
              <div className="text-gray-400 text-xs md:text-sm mt-1 truncate">
                {incidencia.rut_empleado} - {incidencia.get_tipo_incidencia_display || incidencia.tipo_incidencia}
              </div>
              <div className="flex flex-wrap items-center gap-2 mt-2">
                <span className="text-xs font-medium text-white/90">
                  Estado: {obtenerTextoEstado()}
                </span>
                <span className="text-xs text-gray-400">
                  • {obtenerMensajeTurno()}
                </span>
                {esConfirmacionPendiente() && (
                  <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-900/50 text-yellow-300 border border-yellow-700/30">
                    Confirmación de desaparición pendiente
                  </span>
                )}
              </div>
            </div>
            <button
              onClick={onCerrar}
              className="text-gray-400 hover:text-white transition-colors ml-3 flex-shrink-0"
              aria-label="Cerrar"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Resumen compacto colapsable */}
          <details className="mt-3 group">
            <summary className="list-none flex items-center justify-between cursor-pointer select-none">
              <div className="flex items-center gap-2 text-sm text-gray-300">
                <span className="font-medium text-white">Resumen de la incidencia</span>
                <span className="px-2 py-0.5 rounded-full text-xs bg-gray-800/80 border border-gray-700 text-gray-300 capitalize">
                  Prioridad: {incidencia.prioridad}
                </span>
              </div>
              <span className="text-xs text-gray-400 group-open:hidden">Ver más</span>
              <span className="text-xs text-gray-400 hidden group-open:inline">Ver menos</span>
            </summary>
            <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3 text-sm bg-gray-800/40 border border-gray-700 rounded-lg p-3">
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
                    {incidencia.tipo_incidencia === 'variacion_concepto' ? 'Valor Período Actual:' : 'Valor en Libro:'}
                  </span>
                  <p className="text-white mt-1">{incidencia.valor_libro}</p>
                </div>
              )}
              {incidencia.valor_novedades && (
                <div>
                  <span className="text-gray-400">
                    {incidencia.tipo_incidencia === 'variacion_concepto' ? 'Valor Período Anterior:' : 'Valor en Novedades:'}
                  </span>
                  <p className="text-white mt-1">{incidencia.valor_novedades}</p>
                </div>
              )}
            </div>
          </details>
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
                        <span className="font-medium text-white">
                          {obtenerTextoTipoResolucion(resolucion.tipo_resolucion, resolucion.usuario)}
                        </span>
                        <span className="text-gray-400">de</span>
                        <span className="text-blue-400 font-medium">
                          {esSistema(resolucion) ? 'Sistema' : `${resolucion.usuario?.first_name || ''} ${resolucion.usuario?.last_name || ''}`}
                        </span>
                        {esSistema(resolucion) ? (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-600/40">
                            Automático
                          </span>
                        ) : (
                          (resolucion.usuario?.is_staff || resolucion.usuario?.is_superuser) && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-900/50 text-purple-300 border border-purple-500/30">
                              Supervisor
                            </span>
                          )
                        )}
                      </div>
                      <span className="text-sm text-gray-400">
                        {formatearFecha(resolucion)}
                      </span>
                    </div>
                    
                    <p className="text-gray-300 mb-3 whitespace-pre-wrap">{resolucion.comentario}</p>
                    
                    {resolucion.adjunto && (() => {
                      const urlAbs = construirURLAdjunto(resolucion.adjunto);
                      const imagen = esImagen(urlAbs);
                      return (
                        <div className="mt-2 space-y-2">
                          <div className="flex items-center gap-2 text-blue-400 text-sm">
                            <Upload className="w-4 h-4" />
                            <a href={urlAbs} target="_blank" rel="noopener noreferrer" className="hover:underline">
                              Ver adjunto
                            </a>
                            <a
                              href={urlAbs}
                              download
                              className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-blue-600/20 text-blue-300 hover:bg-blue-600/30 text-xs"
                              title="Descargar"
                            >
                              <Download className="w-3.5 h-3.5" />
                              Descargar
                            </a>
                          </div>
                          {imagen && (
                            <div className="border border-gray-700 rounded-lg p-2 bg-gray-900/40 max-w-xs">
                              <div className="flex items-center gap-1 text-gray-400 text-xs mb-1">
                                <ImageIcon className="w-3.5 h-3.5" /> Previsualización
                              </div>
                              <a href={urlAbs} target="_blank" rel="noopener noreferrer">
                                <img
                                  src={urlAbs}
                                  alt="Adjunto"
                                  className="max-h-48 rounded object-contain mx-auto"
                                  loading="lazy"
                                  onError={(e) => { e.currentTarget.style.display = 'none'; }}
                                />
                              </a>
                            </div>
                          )}
                        </div>
                      );
                    })()}
                    
                    {/* Indicadores de estado específicos - SIMPLIFICADOS */}
                    {resolucion.tipo_resolucion === 'aprobacion' && (
                      <div className="mt-3 inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-900/50 text-green-300 border border-green-500/30">
                        <CheckCircle className="w-4 h-4 mr-1" />
                        Incidencia Aprobada y Resuelta
                      </div>
                    )}
                    {resolucion.tipo_resolucion === 'rechazo' && (
                      <div className="mt-3 inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-900/50 text-red-300 border border-red-500/30">
                        <X className="w-4 h-4 mr-1" />
                        Justificación Rechazada - El analista puede responder
                      </div>
                    )}
                    
                    {/* Indicador si es el mensaje más reciente y de quién es el turno */}
                    {index === historial.length - 1 && !esIncidenciaResuelta() && (
                      <div className="mt-3 text-xs text-gray-500 italic">
                        Último mensaje • {obtenerMensajeTurno()}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Formulario conversacional según turno y rol */}
            {!esIncidenciaResuelta() && (
              <div className="border-t border-gray-700 pt-4">
                
                {/* Turno del Analista */}
                {puedeEscribirAnalista() && (
                  <div>
                    <h4 className="text-md font-medium text-blue-400 mb-3">
                      📝 {historial.length === 0 ? 'Escribir Justificación Inicial' : 'Tu Respuesta'} (Analista)
                    </h4>
                    <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-3 mb-3">
                      <p className="text-blue-300 text-sm">
                        <strong>Tu turno:</strong> {historial.length === 0 
                          ? 'Explica por qué esta incidencia es correcta o cómo debe resolverse.' 
                          : 'Responde al comentario del supervisor y proporciona información adicional si es necesario.'
                        }
                      </p>
                    </div>
                    <form onSubmit={manejarEnviarMensaje} className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          {historial.length === 0 ? 'Justificación Inicial *' : 'Tu Respuesta *'}
                        </label>
                        <textarea
                          value={comentario}
                          onChange={(e) => setComentario(e.target.value)}
                          placeholder={historial.length === 0 
                            ? "Explica por qué esta incidencia es válida o cómo debe resolverse..."
                            : "Responde al supervisor, proporciona más información o clarifica tu posición..."
                          }
                          rows={4}
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
                            accept="image/png,image/jpeg,image/webp,.png,.jpg,.jpeg,.webp"
                            className="hidden"
                            id="adjunto-analista-input"
                          />
                          <label
                            htmlFor="adjunto-analista-input"
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
                          Máximo 5MB. Solo imágenes (PNG, JPG, JPEG, WEBP). PDFs y otros tipos han sido deshabilitados.
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
                          Cerrar
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
                              {historial.length === 0 ? 'Enviar Justificación' : 'Enviar Respuesta'}
                            </>
                          )}
                        </button>
                      </div>
                    </form>
                  </div>
                )}

                {/* Turno del Supervisor */}
                {puedeEscribirSupervisor() && (
                  <div>
                    <h4 className="text-md font-medium text-purple-400 mb-3">
                      👨‍💼 Tu Respuesta (Supervisor)
                    </h4>
                    <div className="bg-purple-900/20 border border-purple-500/30 rounded-lg p-3 mb-3">
                      <p className="text-purple-300 text-sm">
                        <strong>Tu turno:</strong> Revisa la justificación del analista. Puedes comentar, hacer preguntas, solicitar más información, o tomar una decisión final (aprobar/rechazar).
                      </p>
                    </div>

                    {/* Formulario de mensaje del supervisor */}
                    <form onSubmit={manejarEnviarMensaje} className="space-y-3 mb-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Tu Comentario (opcional antes de decidir)
                        </label>
                        <textarea
                          value={comentario}
                          onChange={(e) => setComentario(e.target.value)}
                          placeholder="Comenta sobre la justificación, haz preguntas o solicita más información..."
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
                            accept="image/png,image/jpeg,image/webp,.png,.jpg,.jpeg,.webp"
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
                              Enviar Comentario
                            </>
                          )}
                        </button>
                      </div>
                    </form>

                    {/* Botones de Decisión Final */}
                    <div className="border-t border-gray-600 pt-3">
                      <h5 className="text-sm font-medium text-white mb-3">Decisión Final</h5>
                      
                      {/* Mostrar advertencia si la incidencia ya está resuelta */}
                      {esIncidenciaResuelta() ? (
                        <div className="text-center py-3">
                          <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-3">
                            <div className="flex items-center justify-center text-green-400">
                              <CheckCircle className="w-4 h-4 mr-2" />
                              <span className="text-sm">Esta incidencia ya está resuelta</span>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="flex justify-center space-x-4">
                          {esConfirmacionPendiente() && esSupervisor() && (
                            <button
                              onClick={manejarConfirmarDesaparicion}
                              disabled={enviando}
                              className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                              {enviando ? (
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                              ) : (
                                <CheckCircle className="w-4 h-4 mr-2" />
                              )}
                              Confirmar desaparición
                            </button>
                          )}
                          <button
                            onClick={manejarAprobar}
                            disabled={enviando || esIncidenciaResuelta() || !puedeAprobarORechazar()}
                            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            title={
                              esIncidenciaResuelta() ? "La incidencia ya está resuelta" :
                              !puedeAprobarORechazar() ? "No es tu turno o no tienes permisos" :
                              "Aprobar y marcar como resuelta"
                            }
                          >
                            {enviando ? (
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            ) : (
                              <CheckCircle className="w-4 h-4 mr-2" />
                            )}
                            Aprobar y Resolver
                          </button>
                          
                          <button
                            onClick={manejarRechazar}
                            disabled={enviando || !comentario.trim() || esIncidenciaResuelta() || !puedeAprobarORechazar()}
                            className="flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            title={
                              esIncidenciaResuelta() ? "La incidencia ya está resuelta" :
                              !puedeAprobarORechazar() ? "No es tu turno o no tienes permisos" :
                              !comentario.trim() ? "Debe agregar un comentario antes de rechazar" : 
                              "Rechazar justificación y continuar conversación"
                            }
                          >
                            {enviando ? (
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            ) : (
                              <X className="w-4 h-4 mr-2" />
                            )}
                            Rechazar (Continúa Conversación)
                          </button>
                        </div>
                      )}
                      
                      {!esIncidenciaResuelta() && (
                        <>
                          <p className="text-center text-gray-400 text-xs mt-2">
                            💡 Rechazar permite al analista responder y continuar la conversación
                          </p>
                          {!comentario.trim() && (
                            <p className="text-center text-yellow-400 text-sm mt-2">
                              ⚠️ Agregue un comentario explicando el motivo del rechazo
                            </p>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                )}

                {/* Estado de Solo Lectura - No es tu turno */}
                {!puedeEscribirAnalista() && !puedeEscribirSupervisor() && !esIncidenciaResuelta() && (
                  <div className="text-center py-6">
                    <div className="bg-gray-800/50 border border-gray-600 rounded-lg p-4">
                      <div className="flex items-center justify-center mb-3">
                        <Clock className="w-6 h-6 text-gray-400 mr-2" />
                        <div>
                          <h4 className="text-md font-medium text-gray-300">No es tu turno</h4>
                          <p className="text-gray-400 text-sm">{obtenerMensajeTurno()}</p>
                        </div>
                      </div>
                      <div className="flex items-center justify-center space-x-2 text-gray-400">
                        <Eye className="w-4 h-4" />
                        <span className="text-sm">Modo solo lectura</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Error general */}
                {error && !puedeEscribirAnalista() && !puedeEscribirSupervisor() && (
                  <div className="bg-red-900/20 border border-red-500 rounded-lg p-3">
                    <div className="flex items-center text-red-400">
                      <AlertTriangle className="w-4 h-4 mr-2" />
                      {error}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Incidencia Resuelta - Vista Final */}
            {esIncidenciaResuelta() && (
              <div className="text-center py-6">
                <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-4">
                  <div className="flex items-center justify-center mb-3">
                    <CheckCircle className="w-8 h-8 text-green-400 mr-3" />
                    <div>
                      <h4 className="text-lg font-medium text-green-400">🎉 Incidencia Resuelta</h4>
                      <p className="text-green-300 text-sm">Esta incidencia ha sido aprobada por el supervisor y marcada como resuelta</p>
                    </div>
                  </div>
                  <div className="text-green-300 text-sm mb-4">
                    La conversación ha finalizado exitosamente
                  </div>
                  <button
                    onClick={onCerrar}
                    className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    Cerrar Conversación
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
