import { useState, useCallback } from 'react';

/**
 * Hook personalizado para manejo de subida de archivos en el módulo payroll
 * @param {Object} config - Configuración del hook
 * @param {string} config.tipo - Tipo de archivo (libro_remuneraciones, ausentismos, etc.)
 * @param {Object} config.cierre - Objeto del cierre actual
 * @param {Function} config.onEstadoChange - Callback para notificar cambios de estado
 * @param {Array} config.formatosPermitidos - Formatos de archivo permitidos
 * @param {number} config.tamaanoMaximo - Tamaño máximo en bytes
 */
const useArchivoUpload = ({ 
  tipo, 
  cierre, 
  onEstadoChange,
  formatosPermitidos = ['.xlsx', '.xls', '.csv'],
  tamaanoMaximo = 50 * 1024 * 1024 // 50MB por defecto
}) => {
  const [archivo, setArchivo] = useState(null);
  const [estado, setEstado] = useState('pendiente'); // pendiente, subiendo, subido, procesando, error
  const [error, setError] = useState(null);
  const [progreso, setProgreso] = useState(0);

  // Validar archivo antes de subir
  const validarArchivo = useCallback((file) => {
    if (!file) {
      throw new Error('No se seleccionó ningún archivo');
    }

    // Validar tamaño
    if (file.size > tamaanoMaximo) {
      const tamaanoMB = Math.round(tamaanoMaximo / (1024 * 1024));
      throw new Error(`Archivo muy grande. Máximo ${tamaanoMB}MB permitido`);
    }

    // Validar formato
    const extension = '.' + file.name.split('.').pop().toLowerCase();
    if (!formatosPermitidos.includes(extension)) {
      throw new Error(`Formato no válido. Permitidos: ${formatosPermitidos.join(', ')}`);
    }

    return true;
  }, [formatosPermitidos, tamaanoMaximo]);

  // Función principal de subida
  const subirArchivo = useCallback(async (file) => {
    try {
      // Limpiar errores previos
      setError(null);
      setProgreso(0);

      // Validar archivo
      validarArchivo(file);

      // Cambiar estado a subiendo
      setEstado('subiendo');

      // Crear FormData
      const formData = new FormData();
      formData.append('archivo', file);
      formData.append('cierre_id', cierre.id);
      formData.append('tipo_archivo', tipo);

      console.log(`[ARCHIVO ${tipo}] Iniciando subida:`, {
        nombre: file.name,
        tamaño: file.size,
        tipo: file.type,
        cierre_id: cierre.id
      });

      // Realizar petición con seguimiento de progreso
      const response = await fetch('/api/payroll/archivos/upload/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          // NO incluir Content-Type, FormData lo maneja automáticamente
        },
        body: formData
      });

      if (response.ok) {
        const resultado = await response.json();
        
        console.log(`[ARCHIVO ${tipo}] Subida exitosa:`, resultado);

        // Actualizar estado
        setArchivo(resultado);
        setEstado('subido');
        setProgreso(100);

        // Notificar al padre
        onEstadoChange?.({
          tipo,
          estado: 'subido',
          archivo: resultado,
          error: null
        });

        return resultado;
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || errorData.message || 'Error en la subida');
      }

    } catch (err) {
      console.error(`[ARCHIVO ${tipo}] Error en subida:`, err);
      
      setError(err.message);
      setEstado('error');
      setProgreso(0);

      // Notificar error al padre
      onEstadoChange?.({
        tipo,
        estado: 'error',
        error: err.message,
        archivo: null
      });

      throw err;
    }
  }, [tipo, cierre, validarArchivo, onEstadoChange]);

  // Función para eliminar archivo
  const eliminarArchivo = useCallback(async () => {
    if (!archivo) return;

    try {
      setEstado('eliminando');

      const response = await fetch(`/api/payroll/archivos/${archivo.id}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        console.log(`[ARCHIVO ${tipo}] Eliminado exitosamente`);

        // Reset del estado
        setArchivo(null);
        setEstado('pendiente');
        setProgreso(0);
        setError(null);

        // Notificar al padre
        onEstadoChange?.({
          tipo,
          estado: 'pendiente',
          archivo: null,
          error: null
        });
      } else {
        throw new Error('Error al eliminar el archivo');
      }

    } catch (err) {
      console.error(`[ARCHIVO ${tipo}] Error eliminando:`, err);
      setError(err.message);
      setEstado('error');
    }
  }, [archivo, tipo, onEstadoChange]);

  // Función para abrir selector de archivos
  const abrirSelectorArchivos = useCallback(() => {
    return new Promise((resolve, reject) => {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = formatosPermitidos.join(',');
      
      input.onchange = async (event) => {
        try {
          const file = event.target.files[0];
          if (file) {
            const resultado = await subirArchivo(file);
            resolve(resultado);
          } else {
            reject(new Error('No se seleccionó ningún archivo'));
          }
        } catch (error) {
          reject(error);
        }
      };

      input.onclick = () => {
        // Reset del input para permitir seleccionar el mismo archivo
        input.value = '';
      };

      input.click();
    });
  }, [formatosPermitidos, subirArchivo]);

  return {
    // Estado
    archivo,
    estado,
    error,
    progreso,
    
    // Funciones
    subirArchivo,
    eliminarArchivo,
    abrirSelectorArchivos,
    
    // Helpers
    estaSubido: estado === 'subido',
    estaProcesando: ['subiendo', 'procesando', 'eliminando'].includes(estado),
    tieneError: estado === 'error'
  };
};

export default useArchivoUpload;
