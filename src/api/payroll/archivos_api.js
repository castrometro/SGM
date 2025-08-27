// src/api/payroll/archivos_api.js
// APIs específicas para manejo de archivos de payroll

import api from "../config";

/**
 * Sube un archivo de payroll al backend
 * 
 * @param {Object} params - Parámetros de subida
 * @param {File} params.archivo - Archivo a subir
 * @param {string} params.tipoArchivo - Tipo de archivo (libro_remuneraciones, movimientos_mes, etc.)
 * @param {number} params.cierreId - ID del cierre de payroll
 * @param {function} params.onProgress - Callback para progreso de subida (opcional)
 * @returns {Promise<Object>} Respuesta del servidor
 */
export const subirArchivoPayroll = async ({ archivo, tipoArchivo, cierreId, onProgress }) => {
  try {
    // Crear FormData para enviar archivo
    const formData = new FormData();
    formData.append('archivo', archivo);
    formData.append('tipo_archivo', tipoArchivo);
    formData.append('cierre', cierreId);
    formData.append('nombre_original', archivo.name);
    
    console.log(`📤 Subiendo archivo ${tipoArchivo}:`, {
      nombre: archivo.name,
      tamaño: archivo.size,
      cierreId
    });
    
    // Configurar request con progreso
    const config = {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    };
    
    // Agregar callback de progreso si se proporciona
    if (onProgress) {
      config.onUploadProgress = (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        onProgress(percentCompleted);
      };
    }
    
    const response = await api.post('/payroll/archivos/upload/', formData, config);
    
    console.log('✅ Archivo subido exitosamente:', response.data);
    return response.data;
    
  } catch (error) {
    console.error('❌ Error subiendo archivo:', error);
    
    // Extraer mensaje de error específico
    if (error.response?.data) {
      const errorData = error.response.data;
      
      // Si hay detalles específicos, construir mensaje completo
      if (errorData.detalles && Array.isArray(errorData.detalles)) {
        const mensajesDetalle = errorData.detalles.join('; ');
        const mensajeCompleto = errorData.error ? 
          `${errorData.error}: ${mensajesDetalle}` : 
          mensajesDetalle;
        throw new Error(mensajeCompleto);
      }
      
      // Fallback al mensaje de error básico
      throw new Error(errorData.error || 'Error al subir archivo');
    }
    throw new Error('Error de conexión al subir archivo');
  }
};

/**
 * Verifica si existe un archivo específico para un cierre y tipo
 * 
 * @param {number} cierreId - ID del cierre
 * @param {string} tipoArchivo - Tipo de archivo a verificar
 * @returns {Promise<Object>} Información sobre la existencia del archivo
 */
export const verificarExistenciaArchivo = async (cierreId, tipoArchivo) => {
  try {
    console.log(`🔍 Verificando existencia de archivo ${tipoArchivo} para cierre ${cierreId}`);
    
    const response = await api.get('/payroll/verificar-archivo/', {
      params: {
        cierre_id: cierreId,
        tipo_archivo: tipoArchivo
      }
    });
    
    console.log(`✅ Verificación completada:`, response.data);
    return response.data;
    
  } catch (error) {
    console.error('❌ Error verificando existencia de archivo:', error);
    
    if (error.response?.data) {
      throw new Error(error.response.data.error || 'Error al verificar archivo');
    }
    throw new Error('Error de conexión al verificar archivo');
  }
};

/**
 * Obtiene información detallada de un archivo específico
 * 
 * @param {number} archivoId - ID del archivo
 * @returns {Promise<Object>} Información detallada del archivo
 */
export const obtenerDetalleArchivo = async (archivoId) => {
  try {
    console.log(`📄 Obteniendo detalle de archivo ${archivoId}`);
    
    const response = await api.get(`/payroll/archivos/${archivoId}/`);
    
    console.log('✅ Detalle obtenido:', response.data);
    return response.data;
    
  } catch (error) {
    console.error('❌ Error obteniendo detalle de archivo:', error);
    
    if (error.response?.data) {
      throw new Error(error.response.data.error || 'Error al obtener detalle');
    }
    throw new Error('Error de conexión al obtener detalle');
  }
};

/**
 * Lista todos los archivos de un cierre específico
 * 
 * @param {number} cierreId - ID del cierre
 * @returns {Promise<Array>} Lista de archivos del cierre
 */
export const listarArchivosDelCierre = async (cierreId) => {
  try {
    console.log(`📋 Listando archivos del cierre ${cierreId}`);
    
    const response = await api.get('/payroll/archivos/', {
      params: {
        cierre: cierreId
      }
    });
    
    console.log(`✅ Encontrados ${response.data.length} archivos`);
    return response.data;
    
  } catch (error) {
    console.error('❌ Error listando archivos:', error);
    
    if (error.response?.data) {
      throw new Error(error.response.data.error || 'Error al listar archivos');
    }
    throw new Error('Error de conexión al listar archivos');
  }
};

/**
 * Elimina un archivo específico
 * 
 * @param {number} archivoId - ID del archivo a eliminar
 * @returns {Promise<void>}
 */
export const eliminarArchivo = async (archivoId) => {
  try {
    console.log(`🗑️ Eliminando archivo ${archivoId}`);
    
    await api.delete(`/payroll/archivos/${archivoId}/`);
    
    console.log('✅ Archivo eliminado exitosamente');
    
  } catch (error) {
    console.error('❌ Error eliminando archivo:', error);
    
    if (error.response?.data) {
      throw new Error(error.response.data.error || 'Error al eliminar archivo');
    }
    throw new Error('Error de conexión al eliminar archivo');
  }
};

/**
 * Consulta el estado de procesamiento de un archivo específico
 * 
 * @param {number} archivoId - ID del archivo
 * @returns {Promise<Object>} Estado del procesamiento
 */
export const consultarEstadoProcesamiento = async (archivoId) => {
  try {
    console.log(`📊 Consultando estado de procesamiento del archivo ${archivoId}`);
    
    const response = await api.get(`/payroll/archivos/${archivoId}/estado_procesamiento/`);
    
    console.log('✅ Estado obtenido:', response.data);
    return response.data;
    
  } catch (error) {
    console.error('❌ Error consultando estado de procesamiento:', error);
    
    if (error.response?.data) {
      throw new Error(error.response.data.error || 'Error al consultar estado');
    }
    throw new Error('Error de conexión al consultar estado');
  }
};

// Tipos de archivo disponibles (debe coincidir con el backend)
export const TIPOS_ARCHIVO_PAYROLL = {
  LIBRO_REMUNERACIONES: 'libro_remuneraciones',
  MOVIMIENTOS_MES: 'movimientos_mes',
  AUSENTISMOS: 'ausentismos',
  INGRESOS: 'ingresos',
  FINIQUITOS: 'finiquitos',
  NOVEDADES: 'novedades'
};

// Nombres amigables para mostrar en UI
export const NOMBRES_TIPOS_ARCHIVO = {
  [TIPOS_ARCHIVO_PAYROLL.LIBRO_REMUNERACIONES]: 'Libro de Remuneraciones',
  [TIPOS_ARCHIVO_PAYROLL.MOVIMIENTOS_MES]: 'Movimientos del Mes',
  [TIPOS_ARCHIVO_PAYROLL.AUSENTISMOS]: 'Ausentismos',
  [TIPOS_ARCHIVO_PAYROLL.INGRESOS]: 'Ingresos',
  [TIPOS_ARCHIVO_PAYROLL.FINIQUITOS]: 'Finiquitos',
  [TIPOS_ARCHIVO_PAYROLL.NOVEDADES]: 'Novedades'
};
