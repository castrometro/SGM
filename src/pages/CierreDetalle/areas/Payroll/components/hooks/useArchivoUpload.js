import { useState, useCallback } from 'react';

/**
 * Hook personalizado para manejar la subida de archivos en el módulo payroll
 * @param {Object} cierre - Objeto del cierre actual
 * @param {string} tipo - Tipo de archivo a subir
 * @param {Object} configuracion - Configuración de validación
 * @returns {Object} Estado y funciones para manejo de archivos
 */
const useArchivoUpload = (cierre, tipo, configuracion = {}) => {
  const [estado, setEstado] = useState({
    archivo: null,
    progreso: 0,
    subiendo: false,
    error: null,
    exitoso: false
  });

  // Configuración por defecto
  const config = {
    formatosPermitidos: ['.xlsx', '.xls'],
    tamaanoMaximo: 50 * 1024 * 1024, // 50MB por defecto
    validacionesEspeciales: [],
    ...configuracion
  };

  // Validar archivo
  const validarArchivo = useCallback((archivo) => {
    const errores = [];

    // Validar tamaño
    if (archivo.size > config.tamaanoMaximo) {
      const tamaanoMB = Math.round(config.tamaanoMaximo / (1024 * 1024));
      errores.push(`El archivo debe ser menor a ${tamaanoMB}MB`);
    }

    // Validar formato
    const extension = '.' + archivo.name.split('.').pop().toLowerCase();
    if (!config.formatosPermitidos.includes(extension)) {
      errores.push(`Formato no permitido. Use: ${config.formatosPermitidos.join(', ')}`);
    }

    return errores;
  }, [config]);

  // Función para subir archivo
  const subirArchivo = useCallback(async (archivo) => {
    if (!archivo || !cierre?.id) return;

    // Validar archivo
    const errores = validarArchivo(archivo);
    if (errores.length > 0) {
      setEstado(prev => ({
        ...prev,
        error: errores.join('. '),
        exitoso: false
      }));
      return;
    }

    // Iniciar subida
    setEstado(prev => ({
      ...prev,
      subiendo: true,
      error: null,
      progreso: 0,
      exitoso: false
    }));

    try {
      // Simular progreso de subida
      const intervalos = [20, 40, 60, 80, 95];
      for (let i = 0; i < intervalos.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 300));
        setEstado(prev => ({ ...prev, progreso: intervalos[i] }));
      }

      // TODO: Reemplazar con llamada real al backend
      const formData = new FormData();
      formData.append('archivo', archivo);
      formData.append('tipo', tipo);
      formData.append('cierre_id', cierre.id);

      // Simulación de respuesta exitosa
      await new Promise(resolve => setTimeout(resolve, 500));

      const archivoSubido = {
        id: Math.random().toString(36).substr(2, 9),
        nombre: archivo.name,
        tamaño: archivo.size,
        tipo: tipo,
        fechaSubida: new Date().toISOString(),
        url: URL.createObjectURL(archivo) // URL temporal para preview
      };

      setEstado({
        archivo: archivoSubido,
        progreso: 100,
        subiendo: false,
        error: null,
        exitoso: true
      });

      console.log(`[UPLOAD] Archivo ${tipo} subido exitosamente:`, archivoSubido);

      // En producción aquí iría:
      // const response = await fetch(`/api/payroll/cierres/${cierre.id}/archivos/`, {
      //   method: 'POST',
      //   body: formData
      // });
      // const data = await response.json();

    } catch (error) {
      console.error('[UPLOAD] Error subiendo archivo:', error);
      setEstado(prev => ({
        ...prev,
        subiendo: false,
        error: 'Error al subir el archivo. Intente nuevamente.',
        exitoso: false,
        progreso: 0
      }));
    }
  }, [cierre?.id, tipo, validarArchivo]);

  // Función para eliminar archivo
  const eliminarArchivo = useCallback(async () => {
    if (!estado.archivo?.id) return;

    try {
      setEstado(prev => ({ ...prev, subiendo: true }));

      // TODO: Llamada real al backend para eliminar
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setEstado({
        archivo: null,
        progreso: 0,
        subiendo: false,
        error: null,
        exitoso: false
      });

      console.log(`[UPLOAD] Archivo ${tipo} eliminado`);

      // En producción:
      // await fetch(`/api/payroll/archivos/${estado.archivo.id}/`, {
      //   method: 'DELETE'
      // });

    } catch (error) {
      console.error('[UPLOAD] Error eliminando archivo:', error);
      setEstado(prev => ({
        ...prev,
        subiendo: false,
        error: 'Error al eliminar el archivo.'
      }));
    }
  }, [estado.archivo?.id, tipo]);

  // Función para reiniciar estado
  const reiniciar = useCallback(() => {
    setEstado({
      archivo: null,
      progreso: 0,
      subiendo: false,
      error: null,
      exitoso: false
    });
  }, []);

  return {
    // Estado
    archivo: estado.archivo,
    progreso: estado.progreso,
    subiendo: estado.subiendo,
    error: estado.error,
    exitoso: estado.exitoso,
    
    // Funciones
    subirArchivo,
    eliminarArchivo,
    reiniciar,
    validarArchivo,
    
    // Computed
    tieneArchivo: !!estado.archivo,
    puedeSubir: !estado.subiendo && !estado.archivo,
    configuracion: config
  };
};

export default useArchivoUpload;
