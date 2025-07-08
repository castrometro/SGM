import { useState, useEffect } from "react";
import { Edit, Trash2, Plus, Save, X } from "lucide-react";
import Notificacion from "../Notificacion";
import { 
  crearTipoDocumento, 
  actualizarTipoDocumento, 
  eliminarTipoDocumento,
  registrarActividadTarjeta
} from "../../api/contabilidad";

const ModalTipoDocumentoCRUD = ({ 
  abierto, 
  onClose, 
  clienteId, 
  tiposDocumento, 
  onActualizar,
  onEliminarTodos,
  eliminando = false,
  errorEliminando = '',
  onNotificacion = null, // Nueva prop para callback de notificaciones externas
  cierreId = null // Agregar cierreId para logging
}) => {
  const [editando, setEditando] = useState(null);
  const [agregando, setAgregando] = useState(false);
  const [nuevoTipo, setNuevoTipo] = useState({ codigo: "", descripcion: "" });
  const [editForm, setEditForm] = useState({ codigo: "", descripcion: "" });
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

  // Función para ordenar tipos de documento alfabéticamente
  const tiposOrdenados = [...tiposDocumento].sort((a, b) => 
    a.codigo.localeCompare(b.codigo, 'es', { sensitivity: 'base' })
  );

  // Reset states when modal opens/closes
  useEffect(() => {
    if (!abierto) {
      setEditando(null);
      setAgregando(false);
      setNuevoTipo({ codigo: "", descripcion: "" });
      setEditForm({ codigo: "", descripcion: "" });
      setError("");
      setConfirmandoEliminar(null);
      setConfirmandoEliminarTodos(false);
      cerrarNotificacion();
    } else {
      // Registrar vista en el backend al abrir el modal
      const registrarVista = async () => {
        try {
          await registrarVistaTiposDocumento(cierreId);
        } catch (err) {
          console.error("Error al registrar vista de tipos de documento:", err);
        }
      };

      registrarVista();
    }
  }, [abierto]);

  const handleAgregar = async () => {
    if (!nuevoTipo.codigo.trim() || !nuevoTipo.descripcion.trim()) {
      setError("Código y descripción son requeridos");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const tipoData = {
        codigo: nuevoTipo.codigo.trim(),
        descripcion: nuevoTipo.descripcion.trim()
      };
      const tipoCreado = await crearTipoDocumento(clienteId, tipoData);
      
      // Registrar actividad detallada de creación manual
      try {
        await registrarActividadTarjeta(
          clienteId,
          "tipo_documento", 
          "manual_create",
          `Creó tipo documento manual desde modal: ${tipoData.codigo} - ${tipoData.descripcion}`,
          {
            tipo_documento_id: tipoCreado.id,
            codigo: tipoData.codigo,
            descripcion: tipoData.descripcion,
            accion_origen: "modal_crud"
          },
          cierreId
        );
      } catch (logErr) {
        console.warn("Error registrando actividad de creación:", logErr);
      }
      
      setNuevoTipo({ codigo: "", descripcion: "" });
      setAgregando(false);
      onActualizar();
      mostrarNotificacion("exito", "Tipo de documento creado exitosamente");
    } catch (err) {
      let errorMsg = "Error al crear tipo de documento";
      
      if (err.response?.data) {
        const errorData = err.response.data;
        if (errorData.codigo && Array.isArray(errorData.codigo)) {
          errorMsg = errorData.codigo[0];
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
    if (!editForm.codigo.trim() || !editForm.descripcion.trim()) {
      setError("Código y descripción son requeridos");
      return;
    }

    setLoading(true);
    setError("");
    try {
      // Solo enviar los campos que se pueden editar, no el cliente
      const updateData = {
        codigo: editForm.codigo.trim(),
        descripcion: editForm.descripcion.trim()
      };
      
      // Obtener datos del tipo actual para el log
      const tipoActual = tiposDocumento.find(t => t.id === editando);
      const datosAnteriores = tipoActual ? {
        codigo_anterior: tipoActual.codigo,
        descripcion_anterior: tipoActual.descripcion
      } : {};
      
      await actualizarTipoDocumento(editando, updateData);
      
      // Registrar actividad detallada de edición manual
      try {
        await registrarActividadTarjeta(
          clienteId,
          "tipo_documento", 
          "manual_edit",
          `Editó tipo documento desde modal: ${updateData.codigo} - ${updateData.descripcion}`,
          {
            tipo_documento_id: editando,
            codigo_nuevo: updateData.codigo,
            descripcion_nueva: updateData.descripcion,
            ...datosAnteriores,
            accion_origen: "modal_crud"
          },
          cierreId
        );
      } catch (logErr) {
        console.warn("Error registrando actividad de edición:", logErr);
      }
      
      setEditando(null);
      setEditForm({ codigo: "", descripcion: "" });
      onActualizar();
      mostrarNotificacion("exito", "Tipo de documento actualizado exitosamente");
    } catch (err) {
      let errorMsg = "Error al actualizar tipo de documento";
      
      if (err.response?.data) {
        const errorData = err.response.data;
        if (errorData.codigo && Array.isArray(errorData.codigo)) {
          errorMsg = errorData.codigo[0];
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
      // Obtener datos del tipo antes de eliminar para el log
      const tipoAEliminar = tiposDocumento.find(t => t.id === id);
      const datosEliminado = tipoAEliminar ? {
        codigo: tipoAEliminar.codigo,
        descripcion: tipoAEliminar.descripcion
      } : {};
      
      await eliminarTipoDocumento(id);
      
      // Registrar actividad detallada de eliminación manual
      try {
        await registrarActividadTarjeta(
          clienteId,
          "tipo_documento", 
          "manual_delete",
          `Eliminó tipo documento desde modal: ${datosEliminado.codigo || 'N/A'} - ${datosEliminado.descripcion || 'N/A'}`,
          {
            tipo_documento_id: id,
            ...datosEliminado,
            accion_origen: "modal_crud"
          },
          cierreId
        );
      } catch (logErr) {
        console.warn("Error registrando actividad de eliminación:", logErr);
      }
      
      setConfirmandoEliminar(null);
      onActualizar();
      mostrarNotificacion("exito", "Tipo de documento eliminado exitosamente");
    } catch (err) {
      let errorMsg = "Error al eliminar tipo de documento";
      
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

  const iniciarEdicion = (tipo) => {
    setEditando(tipo.id);
    setEditForm({ codigo: tipo.codigo, descripcion: tipo.descripcion });
    setAgregando(false);
  };

  const cancelarEdicion = () => {
    setEditando(null);
    setEditForm({ codigo: "", descripcion: "" });
    setError("");
  };

  const iniciarAgregar = () => {
    setAgregando(true);
    setEditando(null);
    setNuevoTipo({ codigo: "", descripcion: "" });
    setError("");
  };

  const cancelarAgregar = () => {
    setAgregando(false);
    setNuevoTipo({ codigo: "", descripcion: "" });
    setError("");
  };

  if (!abierto) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-40 flex items-center justify-center">
      <div className="bg-gray-800 rounded-xl shadow-lg p-6 w-full max-w-2xl relative text-white">
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
          <h2 className="text-xl font-semibold">Gestión de Tipos de Documento</h2>
          <button
            className="text-gray-400 hover:text-red-500"
            onClick={onClose}
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
            Agregar Tipo de Documento
          </button>
        </div>

        {agregando && (
          <div className="bg-gray-700 p-4 rounded-lg mb-4">
            <h3 className="font-medium mb-3">Nuevo Tipo de Documento</h3>
            <div className="grid grid-cols-2 gap-3 mb-3">
              <input
                type="text"
                placeholder="Código"
                value={nuevoTipo.codigo}
                onChange={(e) => setNuevoTipo(prev => ({ ...prev, codigo: e.target.value }))}
                className="bg-gray-600 border border-gray-500 rounded px-3 py-2 text-white"
                maxLength="10"
              />
              <input
                type="text"
                placeholder="Descripción"
                value={nuevoTipo.descripcion}
                onChange={(e) => setNuevoTipo(prev => ({ ...prev, descripcion: e.target.value }))}
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
                <th className="px-3 py-2 border-b font-semibold">Código</th>
                <th className="px-3 py-2 border-b font-semibold">Descripción</th>
                <th className="px-3 py-2 border-b font-semibold w-24">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {tiposOrdenados.length === 0 ? (
                <tr>
                  <td colSpan="3" className="text-center py-10 text-gray-400">
                    No hay tipos de documento cargados.
                  </td>
                </tr>
              ) : (
                tiposOrdenados.map((tipo) => (
                  <tr key={tipo.id} className="hover:bg-gray-700">
                    {editando === tipo.id ? (
                      <>
                        <td className="px-3 py-2 border-b">
                          <input
                            type="text"
                            value={editForm.codigo}
                            onChange={(e) => setEditForm(prev => ({ ...prev, codigo: e.target.value }))}
                            className="bg-gray-600 border border-gray-500 rounded px-2 py-1 text-white w-full"
                            maxLength="10"
                          />
                        </td>
                        <td className="px-3 py-2 border-b">
                          <input
                            type="text"
                            value={editForm.descripcion}
                            onChange={(e) => setEditForm(prev => ({ ...prev, descripcion: e.target.value }))}
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
                        <td className="px-3 py-2 border-b">{tipo.codigo}</td>
                        <td className="px-3 py-2 border-b">{tipo.descripcion}</td>
                        <td className="px-3 py-2 border-b">
                          <div className="flex gap-1">
                            <button
                              onClick={() => iniciarEdicion(tipo)}
                              disabled={editando || agregando || loading}
                              className="bg-blue-600 hover:bg-blue-500 p-1 rounded transition disabled:opacity-50"
                              title="Editar"
                            >
                              <Edit size={14} />
                            </button>
                            <button
                              onClick={() => setConfirmandoEliminar(tipo.id)}
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
              <p className="mb-4">¿Estás seguro de que quieres eliminar este tipo de documento?</p>
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
        {tiposDocumento.length > 0 && (
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
                        onNotificacion("exito", "Todos los tipos de documento han sido eliminados");
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

export default ModalTipoDocumentoCRUD;
