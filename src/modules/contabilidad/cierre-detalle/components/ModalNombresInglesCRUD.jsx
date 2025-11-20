import { useState, useEffect } from "react";
import { Edit, Trash2, Plus, Save, X } from "lucide-react";
import Notificacion from "../../../../components/Notificacion";
import { 
  crearNombreIngles, 
  actualizarNombreIngles, 
  eliminarNombreIngles,
  registrarActividadTarjeta
} from "../api/cierreDetalle.api";

const ModalNombresInglesCRUD = ({ 
  abierto, 
  onClose, 
  clienteId,
  cierreId, 
  nombresIngles, 
  onActualizar,
  onEliminarTodos,
  eliminando = false,
  errorEliminando = '',
  onNotificacion = null // Nueva prop para callback de notificaciones externas
}) => {
  const [editando, setEditando] = useState(null);
  const [agregando, setAgregando] = useState(false);
  const [nuevoNombre, setNuevoNombre] = useState({ cuenta_codigo: "", nombre_ingles: "" });
  const [editForm, setEditForm] = useState({ cuenta_codigo: "", nombre_ingles: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [confirmandoEliminar, setConfirmandoEliminar] = useState(null);
  const [confirmandoEliminarTodos, setConfirmandoEliminarTodos] = useState(false);
  
  // Estados para notificaciones
  const [notificacion, setNotificacion] = useState({ visible: false, tipo: "", mensaje: "" });

  // Función para mostrar notificaciones
  const mostrarNotificacion = (tipo, mensaje) => {
    setNotificacion({ visible: true, tipo, mensaje });
  };

  const cerrarNotificacion = () => {
    setNotificacion({ visible: false, tipo: "", mensaje: "" });
  };

  // Función para ordenar nombres en inglés alfabéticamente por código de cuenta
  const nombresOrdenados = Array.isArray(nombresIngles) 
    ? [...nombresIngles].sort((a, b) => 
        a.cuenta_codigo.localeCompare(b.cuenta_codigo, 'es', { sensitivity: 'base' })
      )
    : [];

  // Reset states when modal opens/closes
  useEffect(() => {
    if (!abierto) {
      setEditando(null);
      setAgregando(false);
      setNuevoNombre({ cuenta_codigo: "", nombre_ingles: "" });
      setEditForm({ cuenta_codigo: "", nombre_ingles: "" });
      setError("");
      setConfirmandoEliminar(null);
      setConfirmandoEliminarTodos(false);
      cerrarNotificacion();
    }
  }, [abierto]);

  const handleAgregar = async () => {
    if (!nuevoNombre.cuenta_codigo.trim() || !nuevoNombre.nombre_ingles.trim()) {
      setError("Código de cuenta y nombre en inglés son requeridos");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const nombreData = {
        cuenta_codigo: nuevoNombre.cuenta_codigo.trim(),
        nombre_ingles: nuevoNombre.nombre_ingles.trim(),
        cliente: clienteId
      };
      await crearNombreIngles(nombreData);
      
      // Registrar actividad de creación
      try {
        await registrarActividad(
          "manual_create",
          `Creó nombre en inglés desde modal: ${nuevoNombre.cuenta_codigo.trim()} - ${nuevoNombre.nombre_ingles.trim()}`,
          {
            cuenta_codigo: nuevoNombre.cuenta_codigo.trim(),
            nombre_ingles: nuevoNombre.nombre_ingles.trim()
          }
        );
      } catch (logErr) {
        console.warn("Error registrando actividad de creación:", logErr);
      }
      
      setNuevoNombre({ cuenta_codigo: "", nombre_ingles: "" });
      setAgregando(false);
      onActualizar();
      mostrarNotificacion("exito", "Nombre en inglés creado exitosamente");
    } catch (err) {
      let errorMsg = "Error al crear nombre en inglés";
      
      if (err.response?.data) {
        const errorData = err.response.data;
        if (errorData.cuenta_codigo && Array.isArray(errorData.cuenta_codigo)) {
          errorMsg = errorData.cuenta_codigo[0];
        } else if (errorData.detail) {
          errorMsg = errorData.detail;
        } else if (errorData.message) {
          errorMsg = errorData.message;
        } else if (typeof errorData === 'string') {
          errorMsg = errorData;
        }
      }
      
      setError(errorMsg);
      mostrarNotificacion("error", errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleEditar = async () => {
    if (!editForm.cuenta_codigo.trim() || !editForm.nombre_ingles.trim()) {
      setError("Código de cuenta y nombre en inglés son requeridos");
      return;
    }

    setLoading(true);
    setError("");
    try {
      // Solo enviar los campos que se pueden editar
      const updateData = {
        cuenta_codigo: editForm.cuenta_codigo.trim(),
        nombre_ingles: editForm.nombre_ingles.trim()
      };
      await actualizarNombreIngles(editando, updateData);
      
      // Registrar actividad de edición
      try {
        await registrarActividad(
          "manual_edit",
          `Editó nombre en inglés desde modal: ${editForm.cuenta_codigo.trim()} - ${editForm.nombre_ingles.trim()}`,
          {
            id: editando,
            cuenta_codigo: editForm.cuenta_codigo.trim(),
            nombre_ingles: editForm.nombre_ingles.trim()
          }
        );
      } catch (logErr) {
        console.warn("Error registrando actividad de edición:", logErr);
      }
      
      setEditando(null);
      setEditForm({ cuenta_codigo: "", nombre_ingles: "" });
      onActualizar();
      mostrarNotificacion("exito", "Nombre en inglés actualizado exitosamente");
    } catch (err) {
      let errorMsg = "Error al actualizar nombre en inglés";
      
      if (err.response?.data) {
        const errorData = err.response.data;
        if (errorData.cuenta_codigo && Array.isArray(errorData.cuenta_codigo)) {
          errorMsg = errorData.cuenta_codigo[0];
        } else if (errorData.detail) {
          errorMsg = errorData.detail;
        } else if (errorData.message) {
          errorMsg = errorData.message;
        } else if (typeof errorData === 'string') {
          errorMsg = errorData;
        }
      }
      
      setError(errorMsg);
      mostrarNotificacion("error", errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleEliminar = async (id) => {
    setLoading(true);
    setError("");
    try {
      // Obtener datos del nombre antes de eliminar para el log
      const nombreAEliminar = nombresOrdenados.find(n => n.id === id);
      const datosEliminado = nombreAEliminar ? {
        cuenta_codigo: nombreAEliminar.cuenta_codigo,
        nombre_ingles: nombreAEliminar.nombre_ingles
      } : {};
      
      await eliminarNombreIngles(id);
      
      // Registrar actividad de eliminación
      try {
        await registrarActividad(
          "manual_delete",
          `Eliminó nombre en inglés desde modal: ${datosEliminado.cuenta_codigo || 'N/A'} - ${datosEliminado.nombre_ingles || 'N/A'}`,
          {
            id: id,
            ...datosEliminado
          }
        );
      } catch (logErr) {
        console.warn("Error registrando actividad de eliminación:", logErr);
      }
      
      setConfirmandoEliminar(null);
      onActualizar();
      mostrarNotificacion("exito", "Nombre en inglés eliminado exitosamente");
    } catch (err) {
      let errorMsg = "Error al eliminar nombre en inglés";
      
      if (err.response?.data) {
        const errorData = err.response.data;
        if (errorData.detail) {
          errorMsg = errorData.detail;
        } else if (errorData.message) {
          errorMsg = errorData.message;
        } else if (typeof errorData === 'string') {
          errorMsg = errorData;
        }
      }
      
      setError(errorMsg);
      mostrarNotificacion("error", errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const iniciarEdicion = (nombre) => {
    setEditando(nombre.id);
    setEditForm({ cuenta_codigo: nombre.cuenta_codigo, nombre_ingles: nombre.nombre_ingles });
    setAgregando(false);
  };

  const cancelarEdicion = () => {
    setEditando(null);
    setEditForm({ cuenta_codigo: "", nombre_ingles: "" });
    setError("");
  };

  const iniciarAgregar = () => {
    setAgregando(true);
    setEditando(null);
    setNuevoNombre({ cuenta_codigo: "", nombre_ingles: "" });
    setError("");
  };

  const cancelarAgregar = () => {
    setAgregando(false);
    setNuevoNombre({ cuenta_codigo: "", nombre_ingles: "" });
    setError("");
  };

  // Función auxiliar para registrar actividades CRUD
  const registrarActividad = async (accion, descripcion, detalles = {}) => {
    try {
      if (!clienteId) {
        console.warn('No hay clienteId para registrar actividad');
        return;
      }

      await registrarActividadTarjeta(
        clienteId,
        "nombres_ingles", 
        accion,
        descripcion,
        {
          cierre_id: cierreId,
          accion_origen: "modal_nombres_ingles",
          ...detalles
        },
        cierreId
      );
    } catch (error) {
      console.warn('Error registrando actividad:', error);
      // No fallar la operación principal por un error de logging
    }
  };

  // Función para manejar el cierre del modal con logging
  const handleClose = async () => {
    try {
      await registrarActividad(
        "view_data",
        `Cerró modal de nombres en inglés`,
        {
          nombres_cargados: nombresOrdenados.length
        }
      );
    } catch (logErr) {
      console.warn("Error registrando cierre del modal:", logErr);
    }
    
    onClose();
  };

  // Registrar actividad cuando se abre el modal
  useEffect(() => {
    if (abierto && clienteId) {
      registrarActividad(
        "view_data",
        `Abrió modal de nombres en inglés`,
        {
          nombres_disponibles: nombresOrdenados.length
        }
      ).catch(logErr => console.warn("Error registrando apertura del modal:", logErr));
    }
  }, [abierto, clienteId]);

  if (!abierto) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-40 flex items-center justify-center">
      <div className="bg-gray-800 rounded-xl shadow-lg p-6 w-full max-w-4xl relative text-white">
        {loading && (
          <div className="absolute inset-0 bg-gray-800 bg-opacity-75 rounded-xl flex items-center justify-center z-10">
            <div className="flex items-center gap-2 text-blue-400">
              <svg className="animate-spin h-6 w-6" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
              </svg>
              <span>Procesando...</span>
            </div>
          </div>
        )}
        
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Gestión de Nombres en Inglés</h2>
          <button
            className="text-gray-400 hover:text-red-500"
            onClick={handleClose}
            disabled={loading}
          >
            <X size={20} />
          </button>
        </div>

        {error && (
          <div className="bg-red-600/20 border border-red-600 text-red-400 px-3 py-2 rounded mb-4">
            {error}
          </div>
        )}

        <div className="mb-4">
          <button
            onClick={iniciarAgregar}
            disabled={agregando || editando || loading}
            className="bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded font-medium transition flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
              </svg>
            ) : (
              <Plus size={16} />
            )}
            Agregar Nombre en Inglés
          </button>
        </div>

        {agregando && (
          <div className="bg-gray-700 p-4 rounded-lg mb-4">
            <h3 className="font-medium mb-3">Nuevo Nombre en Inglés</h3>
            <div className="grid grid-cols-2 gap-3 mb-3">
              <input
                type="text"
                placeholder="Código de Cuenta"
                value={nuevoNombre.cuenta_codigo}
                onChange={(e) => setNuevoNombre(prev => ({ ...prev, cuenta_codigo: e.target.value }))}
                className="bg-gray-600 border border-gray-500 rounded px-3 py-2 text-white"
                maxLength="20"
              />
              <input
                type="text"
                placeholder="Nombre en Inglés"
                value={nuevoNombre.nombre_ingles}
                onChange={(e) => setNuevoNombre(prev => ({ ...prev, nombre_ingles: e.target.value }))}
                className="bg-gray-600 border border-gray-500 rounded px-3 py-2 text-white"
                maxLength="255"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleAgregar}
                disabled={loading}
                className="bg-green-600 hover:bg-green-500 px-3 py-1 rounded text-sm font-medium transition flex items-center gap-2 disabled:opacity-50"
              >
                <Save size={14} />
                Guardar
              </button>
              <button
                onClick={cancelarAgregar}
                disabled={loading}
                className="bg-gray-600 hover:bg-gray-500 px-3 py-1 rounded text-sm font-medium transition disabled:opacity-50"
              >
                Cancelar
              </button>
            </div>
          </div>
        )}

        <div className="overflow-y-auto" style={{ maxHeight: "400px" }}>
          <table className="w-full text-left">
            <thead className="sticky top-0 bg-gray-800">
              <tr>
                <th className="px-3 py-2 border-b font-semibold">Código de Cuenta</th>
                <th className="px-3 py-2 border-b font-semibold">Nombre en Inglés</th>
                <th className="px-3 py-2 border-b font-semibold w-24">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {nombresOrdenados.length === 0 ? (
                <tr>
                  <td colSpan="3" className="text-center py-10 text-gray-400">
                    No hay nombres en inglés cargados.
                  </td>
                </tr>
              ) : (
                nombresOrdenados.map((nombre) => (
                  <tr key={nombre.id} className="hover:bg-gray-700">
                    {editando === nombre.id ? (
                      <>
                        <td className="px-3 py-2 border-b">
                          <input
                            type="text"
                            value={editForm.cuenta_codigo}
                            onChange={(e) => setEditForm(prev => ({ ...prev, cuenta_codigo: e.target.value }))}
                            className="bg-gray-600 border border-gray-500 rounded px-2 py-1 text-white w-full"
                            maxLength="20"
                          />
                        </td>
                        <td className="px-3 py-2 border-b">
                          <input
                            type="text"
                            value={editForm.nombre_ingles}
                            onChange={(e) => setEditForm(prev => ({ ...prev, nombre_ingles: e.target.value }))}
                            className="bg-gray-600 border border-gray-500 rounded px-2 py-1 text-white w-full"
                            maxLength="255"
                          />
                        </td>
                        <td className="px-3 py-2 border-b">
                          <div className="flex gap-1">
                            <button
                              onClick={handleEditar}
                              disabled={loading}
                              className="bg-green-600 hover:bg-green-500 p-1 rounded transition disabled:opacity-50"
                              title="Guardar"
                            >
                              <Save size={14} />
                            </button>
                            <button
                              onClick={cancelarEdicion}
                              disabled={loading}
                              className="bg-gray-600 hover:bg-gray-500 p-1 rounded transition disabled:opacity-50"
                              title="Cancelar"
                            >
                              <X size={14} />
                            </button>
                          </div>
                        </td>
                      </>
                    ) : (
                      <>
                        <td className="px-3 py-2 border-b">{nombre.cuenta_codigo}</td>
                        <td className="px-3 py-2 border-b">{nombre.nombre_ingles}</td>
                        <td className="px-3 py-2 border-b">
                          <div className="flex gap-1">
                            <button
                              onClick={() => iniciarEdicion(nombre)}
                              disabled={editando || agregando || loading}
                              className="bg-blue-600 hover:bg-blue-500 p-1 rounded transition disabled:opacity-50"
                              title="Editar"
                            >
                              <Edit size={14} />
                            </button>
                            <button
                              onClick={() => setConfirmandoEliminar(nombre.id)}
                              disabled={editando || agregando || loading}
                              className="bg-red-600 hover:bg-red-500 p-1 rounded transition disabled:opacity-50"
                              title="Eliminar"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </td>
                      </>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Confirmación de eliminación individual */}
        {confirmandoEliminar && (
          <div className="fixed inset-0 z-60 bg-black bg-opacity-50 flex items-center justify-center">
            <div className="bg-gray-800 rounded-lg p-6 text-white">
              <h3 className="text-lg font-semibold mb-4">Confirmar eliminación</h3>
              <p className="mb-4">¿Estás seguro de que quieres eliminar este nombre en inglés?</p>
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => handleEliminar(confirmandoEliminar)}
                  disabled={loading}
                  className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded font-medium transition disabled:opacity-50"
                >
                  Eliminar
                </button>
                <button
                  onClick={() => setConfirmandoEliminar(null)}
                  disabled={loading}
                  className="bg-gray-600 hover:bg-gray-500 px-4 py-2 rounded font-medium transition disabled:opacity-50"
                >
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Botón Eliminar Todos */}
        {Array.isArray(nombresIngles) && nombresIngles.length > 0 && (
          <div className="mt-5 flex justify-end">
            {confirmandoEliminarTodos ? (
              <div className="flex gap-2 items-center">
                <span>¿Confirmar eliminación de todos?</span>
                <button
                  className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded font-bold flex items-center gap-2"
                  onClick={() => {
                    onEliminarTodos();
                    setConfirmandoEliminarTodos(false);
                    // Mostrar notificación externa si está disponible
                    if (onNotificacion) {
                      // Esperar un poco para que se complete la operación
                      setTimeout(() => {
                        onNotificacion("exito", "Todos los nombres en inglés han sido eliminados");
                      }, 500);
                    }
                  }}
                  disabled={eliminando}
                >
                  {eliminando && (
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                    </svg>
                  )}
                  Sí, eliminar todos
                </button>
                <button
                  className="bg-gray-600 hover:bg-gray-500 px-3 py-1 rounded"
                  onClick={() => setConfirmandoEliminarTodos(false)}
                  disabled={eliminando}
                >
                  Cancelar
                </button>
              </div>
            ) : (
              <button
                className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded font-bold"
                onClick={() => setConfirmandoEliminarTodos(true)}
                disabled={editando || agregando || loading}
              >
                Eliminar todos
              </button>
            )}
          </div>
        )}

        {errorEliminando && (
          <div className="mt-2 text-red-400 text-xs text-right">{errorEliminando}</div>
        )}
      </div>
      
      {/* Componente de notificación */}
      <Notificacion
        tipo={notificacion.tipo}
        mensaje={notificacion.mensaje}
        visible={notificacion.visible}
        onClose={cerrarNotificacion}
      />
    </div>
  );
};

export default ModalNombresInglesCRUD;
