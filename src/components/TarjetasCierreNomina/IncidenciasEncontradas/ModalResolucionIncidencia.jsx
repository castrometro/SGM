import React, { useState, useEffect } from "react";
import { X, Send, Upload, AlertTriangle, CheckCircle, MessageSquare } from "lucide-react";
import { crearResolucionIncidencia, obtenerHistorialIncidencia } from "../../../api/nomina";

const ModalResolucionIncidencia = ({ abierto, incidencia, onCerrar, onResolucionCreada }) => {
  const [tipoResolucion, setTipoResolucion] = useState('comentario');
  const [comentario, setComentario] = useState('');
  const [valorCorregido, setValorCorregido] = useState('');
  const [campoCorregido, setCampoCorregido] = useState('');
  const [adjunto, setAdjunto] = useState(null);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState('');
  const [historial, setHistorial] = useState([]);
  const [cargandoHistorial, setCargandoHistorial] = useState(false);
  const [tabActiva, setTabActiva] = useState('nueva'); // 'nueva' o 'historial'

  useEffect(() => {
    if (abierto && incidencia?.id) {
      cargarHistorial();
      // Limpiar formulario
      setTipoResolucion('comentario');
      setComentario('');
      setValorCorregido('');
      setCampoCorregido('');
      setAdjunto(null);
      setError('');
    }
  }, [abierto, incidencia]);

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

  const manejarEnvio = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!comentario.trim()) {
      setError('El comentario es requerido');
      return;
    }

    if (tipoResolucion === 'correccion' && !valorCorregido.trim()) {
      setError('El valor corregido es requerido para correcciones');
      return;
    }

    setEnviando(true);
    try {
      const formData = new FormData();
      formData.append('tipo_resolucion', tipoResolucion);
      formData.append('comentario', comentario);
      
      if (tipoResolucion === 'correccion') {
        formData.append('valor_corregido', valorCorregido);
        formData.append('campo_corregido', campoCorregido || 'valor_general');
      }
      
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
      setValorCorregido('');
      setCampoCorregido('');
      setAdjunto(null);
      setTabActiva('historial'); // Cambiar a historial para ver la nueva resolución
      
    } catch (err) {
      console.error("Error creando resolución:", err);
      setError('Error al crear la resolución');
    } finally {
      setEnviando(false);
    }
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

  const obtenerIconoTipoResolucion = (tipo) => {
    switch (tipo) {
      case 'solucion':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'correccion':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'comentario':
        return <MessageSquare className="w-4 h-4 text-blue-500" />;
      default:
        return <MessageSquare className="w-4 h-4 text-gray-500" />;
    }
  };

  if (!abierto || !incidencia) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex justify-center items-center p-4">
      <div className="bg-gray-900 rounded-lg shadow-lg w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <div>
            <h2 className="text-xl font-semibold text-white">
              Resolución de Incidencia
            </h2>
            <p className="text-gray-400 text-sm mt-1">
              {incidencia.rut_empleado} - {incidencia.get_tipo_incidencia_display || incidencia.tipo_incidencia}
            </p>
          </div>
          <button
            onClick={onCerrar}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Detalles de la incidencia */}
        <div className="p-6 border-b border-gray-700 bg-gray-800/50">
          <h3 className="text-lg font-medium text-white mb-3">Detalles de la Incidencia</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
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
                <span className="text-gray-400">Valor en Libro:</span>
                <p className="text-white mt-1">{incidencia.valor_libro}</p>
              </div>
            )}
            {incidencia.valor_novedades && (
              <div>
                <span className="text-gray-400">Valor en Novedades:</span>
                <p className="text-white mt-1">{incidencia.valor_novedades}</p>
              </div>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-700">
          <button
            onClick={() => setTabActiva('nueva')}
            className={`px-6 py-3 text-sm font-medium transition-colors ${
              tabActiva === 'nueva'
                ? 'text-blue-400 border-b-2 border-blue-400 bg-gray-800/50'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Nueva Resolución
          </button>
          <button
            onClick={() => setTabActiva('historial')}
            className={`px-6 py-3 text-sm font-medium transition-colors ${
              tabActiva === 'historial'
                ? 'text-blue-400 border-b-2 border-blue-400 bg-gray-800/50'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Historial ({historial.length})
          </button>
        </div>

        <div className="overflow-y-auto max-h-96">
          {tabActiva === 'nueva' ? (
            /* Formulario de nueva resolución */
            <div className="p-6">
              <form onSubmit={manejarEnvio} className="space-y-6">
                {/* Tipo de resolución */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Tipo de Resolución
                  </label>
                  <select
                    value={tipoResolucion}
                    onChange={(e) => setTipoResolucion(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="comentario">Comentario / Consulta</option>
                    <option value="solucion">Solución Propuesta</option>
                    <option value="correccion">Corrección de Valores</option>
                    <option value="rechazo">Rechazo</option>
                  </select>
                </div>

                {/* Campo corregido (solo para correcciones) */}
                {tipoResolucion === 'correccion' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Campo Corregido
                    </label>
                    <input
                      type="text"
                      value={campoCorregido}
                      onChange={(e) => setCampoCorregido(e.target.value)}
                      placeholder="Ej: sueldo_base, concepto_x, etc."
                      className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                )}

                {/* Valor corregido (solo para correcciones) */}
                {tipoResolucion === 'correccion' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Valor Corregido *
                    </label>
                    <input
                      type="text"
                      value={valorCorregido}
                      onChange={(e) => setValorCorregido(e.target.value)}
                      placeholder="Ingrese el valor correcto"
                      className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                )}

                {/* Comentario */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Comentario *
                  </label>
                  <textarea
                    value={comentario}
                    onChange={(e) => setComentario(e.target.value)}
                    placeholder="Describe la resolución, explicación o comentario..."
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
                    className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {enviando ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Enviando...
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4 mr-2" />
                        Enviar Resolución
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          ) : (
            /* Historial de resoluciones */
            <div className="p-6">
              {cargandoHistorial ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                </div>
              ) : historial.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>No hay resoluciones aún</p>
                  <p className="text-sm">Las resoluciones aparecerán aquí</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {historial.map((resolucion, index) => (
                    <div key={resolucion.id} className="bg-gray-800 rounded-lg p-4 border-l-4 border-blue-500">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          {obtenerIconoTipoResolucion(resolucion.tipo_resolucion)}
                          <span className="font-medium text-white capitalize">
                            {resolucion.get_tipo_resolucion_display || resolucion.tipo_resolucion}
                          </span>
                          <span className="text-gray-400">por</span>
                          <span className="text-blue-400">
                            {resolucion.usuario?.first_name} {resolucion.usuario?.last_name}
                          </span>
                        </div>
                        <span className="text-sm text-gray-400">
                          {formatearFecha(resolucion.fecha_creacion)}
                        </span>
                      </div>
                      
                      <p className="text-gray-300 mb-3">{resolucion.comentario}</p>
                      
                      {resolucion.valor_corregido && (
                        <div className="bg-gray-700 rounded p-2 mb-3">
                          <span className="text-sm text-gray-400">Valor corregido:</span>
                          <p className="text-white">{resolucion.valor_corregido}</p>
                          {resolucion.campo_corregido && (
                            <p className="text-sm text-gray-400">Campo: {resolucion.campo_corregido}</p>
                          )}
                        </div>
                      )}
                      
                      {resolucion.adjunto && (
                        <div className="flex items-center text-blue-400 text-sm">
                          <Upload className="w-4 h-4 mr-1" />
                          <a href={resolucion.adjunto} target="_blank" rel="noopener noreferrer" className="hover:underline">
                            Ver adjunto
                          </a>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ModalResolucionIncidencia;
