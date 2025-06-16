import { useState, useRef, useEffect } from 'react';
import EstadoBadge from '../EstadoBadge';
import ModalClasificacionRegistrosRaw from '../ModalClasificacionRegistrosRaw';
import { Download, FileText, Trash2, RefreshCw, Settings, Database } from 'lucide-react';
import { 
  subirClasificacionBulk, 
  obtenerBulkClasificaciones, 
  descargarPlantillaClasificacionBulk,
  eliminarBulkClasificacion,
  eliminarTodosBulkClasificacion,
  reprocesarBulkClasificacionUpload,
  obtenerClasificacionesArchivo
} from '../../api/contabilidad';

const ClasificacionBulkCard = ({ clienteId, onCompletado, disabled, numeroPaso }) => {
  const [archivo, setArchivo] = useState(null);
  const [estado, setEstado] = useState('pendiente');
  const [subiendo, setSubiendo] = useState(false);
  const [uploads, setUploads] = useState([]);
  const [error, setError] = useState("");
  const [ultimoUpload, setUltimoUpload] = useState(null);
  const [eliminando, setEliminando] = useState(false);
  const [errorEliminando, setErrorEliminando] = useState("");
  const [registrosRaw, setRegistrosRaw] = useState([]);
  const [modalRegistrosRaw, setModalRegistrosRaw] = useState(false);
  const fileInputRef = useRef();

  useEffect(() => { cargar(); }, []);
  
  // Polling para actualizar estado cuando está procesando
  useEffect(() => {
    let interval;
    if (estado === 'procesando') {
      interval = setInterval(() => {
        cargar();
      }, 3000); // Cada 3 segundos
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [estado]);
  
  const cargar = async () => {
    try {
      const data = await obtenerBulkClasificaciones(clienteId);
      setUploads(data);
      const last = data && data.length > 0 ? data[0] : null;
      setUltimoUpload(last);
      if (last) {
        setEstado(last.estado);
        // Cargar registros raw si existe el upload
        if (last.id) {
          try {
            const registros = await obtenerClasificacionesArchivo(last.id);
            setRegistrosRaw(registros);
            // Considerar "completado" si hay registros raw (archivo procesado)
            // independientemente del estado de mapeo
            const tieneRegistros = registros.length > 0;
            if (onCompletado) onCompletado(tieneRegistros);
          } catch (err) {
            console.log("No hay registros raw o error cargándolos:", err);
            setRegistrosRaw([]);
            if (onCompletado) onCompletado(false);
          }
        } else {
          // Si no hay ID del upload, no hay registros
          if (onCompletado) onCompletado(false);
        }
      } else {
        setEstado('pendiente');
        setRegistrosRaw([]);
        if (onCompletado) onCompletado(false);
      }
    } catch (e) {
      console.error('Error al cargar uploads:', e);
    }
  };

  const handleSubir = async () => {
    if (!archivo) return;
    setSubiendo(true);
    setError("");
    
    const form = new FormData();
    form.append('cliente', clienteId);
    form.append('archivo', archivo);
    
    try {
      const response = await subirClasificacionBulk(form);
      console.log('Archivo subido exitosamente:', response);
      setArchivo(null);
      setEstado('procesando'); // Cambiar estado inmediatamente
      // Recargar datos en 1 segundo para dar tiempo al backend
      setTimeout(() => {
        cargar();
      }, 1000);
    } catch (e) {
      console.error('Error al subir archivo:', e);
      
      // Manejo específico para error 409 (datos ya existentes)
      if (e.response?.status === 409) {
        setError(
          "⚠️ Ya hay clasificaciones existentes para este cliente. " +
          "Para subir un nuevo archivo, primero debe eliminar las clasificaciones anteriores " +
          "usando el botón 'Eliminar todos' del historial."
        );
      } else {
        setError('Error al subir el archivo. Verifique el formato.');
      }
    } finally {
      setSubiendo(false);
    }
  };

  // Handler para eliminar todos los uploads
  const handleEliminarTodos = async () => {
    setEliminando(true);
    setErrorEliminando("");
    try {
      await eliminarTodosBulkClasificacion(clienteId);
      setEstado("pendiente");
      setUploads([]);
      setRegistrosRaw([]);
      // Recargar el estado de la tarjeta
      await cargar();
      if (onCompletado) onCompletado(false);
    } catch (err) {
      setErrorEliminando("Error al eliminar los archivos.");
    } finally {
      setEliminando(false);
    }
  };

  return (
    <div className={`bg-gray-800 p-4 rounded-xl shadow-lg flex flex-col gap-3 ${disabled ? 'opacity-60 pointer-events-none' : ''}`}>
      <h3 className="text-lg font-semibold mb-3">{numeroPaso}. Subir Clasificaciones de Cuentas</h3>
      <div className="flex items-center gap-2 mb-2">
        <span className="font-semibold">Estado:</span>
        <EstadoBadge estado={estado === 'completado' ? 'subido' : estado} />
      </div>
      <a
        href={descargarPlantillaClasificacionBulk()}
        download
        className={`flex items-center gap-2 bg-gray-700 hover:bg-blue-600 px-3 py-1 rounded !text-white text-sm font-medium transition shadow w-fit mb-2 ${disabled ? 'opacity-60 pointer-events-none' : ''}`}
      >
        <Download size={16} />
        Descargar Estructura
      </a>
      <div className="flex gap-3 items-center">
        <button
          type="button"
          onClick={() => fileInputRef.current.click()}
          disabled={subiendo || disabled}
          className={`bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded text-sm font-medium transition ${subiendo ? 'opacity-60 cursor-not-allowed' : ''}`}
        >
          {subiendo ? 'Subiendo...' : 'Elegir archivo .xlsx'}
        </button>
        {archivo && (
          <button
            type="button"
            onClick={handleSubir}
            disabled={subiendo || disabled}
            className={`bg-green-600 hover:bg-green-500 px-3 py-1 rounded text-sm font-medium transition ${subiendo ? 'opacity-60 cursor-not-allowed' : ''}`}
          >
            Subir
          </button>
        )}
        <span className="text-gray-300 text-xs italic truncate max-w-xs">
          {archivo ? archivo.name : 'Ningún archivo seleccionado'}
        </span>
      </div>
      <input
        type="file"
        accept=".xlsx"
        ref={fileInputRef}
        style={{ display: 'none' }}
        onChange={e => setArchivo(e.target.files[0])}
      />
      {error && <div className="text-xs text-red-400 mt-1">{error}</div>}
      
      {/* Botones de acciones */}
      <div className="flex gap-2 mt-2">
        <button
          onClick={() => setModalRegistrosRaw(true)}
          className="px-3 py-1 rounded text-sm font-medium transition bg-blue-700 hover:bg-blue-600 text-white flex items-center gap-2"
          disabled={!ultimoUpload?.id}
        >
          <Settings size={16} />
          Ver clasificaciones
        </button>
      </div>
      
      {/* Información del estado y resumen */}
      <div className="text-xs text-gray-400 italic mt-2">
        {estado === 'completado' && ultimoUpload?.resumen ? (
          <div className="space-y-2">
            <div className="text-green-400">✔ Archivo procesado correctamente</div>
            <div>
              📊 {ultimoUpload.resumen.registros_guardados || 0} registros guardados de {ultimoUpload.resumen.total_filas || 0} filas
              {ultimoUpload.resumen.filas_vacias > 0 && (
                <span className="text-gray-500"> • {ultimoUpload.resumen.filas_vacias} filas vacías omitidas</span>
              )}
            </div>
            <div>
              📋 Sets encontrados: {ultimoUpload.resumen.sets_encontrados?.join(', ') || 'Ninguno'}
            </div>
            
            {/* Mostrar información de registros raw */}
            {registrosRaw.length > 0 && (
              <div className="flex items-center gap-2">
                <span>📋 {registrosRaw.length} registros cargados</span>
              </div>
            )}
            
            {ultimoUpload.resumen.errores_count > 0 && (
              <div className="text-yellow-400">
                ⚠ {ultimoUpload.resumen.errores_count} errores encontrados en el procesamiento
              </div>
            )}
          </div>
        ) : estado === 'procesando' ? (
          <div className="text-blue-400">🔄 Procesando clasificaciones…</div>
        ) : estado === 'error' && ultimoUpload?.errores ? (
          <div className="text-red-400">❌ Error: {ultimoUpload.errores}</div>
        ) : (
          <div>Aún no se ha subido el archivo.</div>
        )}

      </div>

      {/* Modal de registros raw */}
      <ModalClasificacionRegistrosRaw
        isOpen={modalRegistrosRaw}
        onClose={() => setModalRegistrosRaw(false)}
        uploadId={ultimoUpload?.id}
        clienteId={clienteId}
        onDataChanged={() => {
          cargar(); // Recargar datos después de cambios CRUD
        }}
      />

    </div>
  );
};

export default ClasificacionBulkCard;
