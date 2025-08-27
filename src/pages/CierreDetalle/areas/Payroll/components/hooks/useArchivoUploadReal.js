// src/pages/CierreDetalle/areas/Payroll/components/hooks/useArchivoUploadReal.js
// Hook para manejar archivos de payroll con integración real al backend

import { useState, useEffect } from 'react';
import { 
  subirArchivoPayroll, 
  verificarExistenciaArchivo,
  TIPOS_ARCHIVO_PAYROLL 
} from '../../../../../../api/payroll';

const useArchivoUploadReal = (tipoArchivo, cierreId) => {
  const [estado, setEstado] = useState({
    archivo: null,
    subiendo: false,
    progreso: 0,
    error: null,
    verificando: false
  });

  // Verificar existencia del archivo al montar el componente
  useEffect(() => {
    if (cierreId && tipoArchivo) {
      verificarExistencia();
    }
  }, [cierreId, tipoArchivo]);

  const verificarExistencia = async () => {
    if (!cierreId || !tipoArchivo) return;
    
    setEstado(prev => ({ ...prev, verificando: true, error: null }));
    
    try {
      console.log('🔍 Verificando existencia de archivo:', { cierreId, tipoArchivo });
      const respuesta = await verificarExistenciaArchivo(cierreId, tipoArchivo);
      
      console.log('📋 Respuesta de verificación:', respuesta);
      
      if (respuesta.success && respuesta.exists) {
        console.log('✅ Archivo encontrado:', respuesta.archivo);
        setEstado(prev => ({
          ...prev,
          archivo: respuesta.archivo,
          verificando: false
        }));
      } else {
        console.log('📭 No se encontró archivo del tipo:', tipoArchivo);
        setEstado(prev => ({
          ...prev,
          archivo: null,
          verificando: false
        }));
      }
    } catch (error) {
      console.error('❌ Error verificando existencia:', error);
      setEstado(prev => ({
        ...prev,
        error: `Error verificando archivo: ${error.message}`,
        verificando: false
      }));
    }
  };

  const subirArchivo = async (archivo) => {
    if (!archivo || !cierreId || !tipoArchivo) {
      setEstado(prev => ({
        ...prev,
        error: 'Faltan parámetros requeridos para subir archivo'
      }));
      return false;
    }

    setEstado(prev => ({
      ...prev,
      subiendo: true,
      progreso: 0,
      error: null
    }));

    try {
      // Callback para actualizar progreso
      const onProgress = (progreso) => {
        setEstado(prev => ({ ...prev, progreso }));
      };

      const respuesta = await subirArchivoPayroll({
        archivo,
        tipoArchivo,
        cierreId,
        onProgress
      });

      if (respuesta.success) {
        setEstado({
          archivo: respuesta.archivo,
          subiendo: false,
          progreso: 100,
          error: null,
          verificando: false
        });
        return true;
      } else {
        throw new Error(respuesta.error || 'Error desconocido al subir archivo');
      }
    } catch (error) {
      console.error('Error subiendo archivo:', error);
      setEstado(prev => ({
        ...prev,
        subiendo: false,
        progreso: 0,
        error: error.message || 'Error al subir archivo'
      }));
      return false;
    }
  };

  const limpiarError = () => {
    setEstado(prev => ({ ...prev, error: null }));
  };

  const reiniciar = () => {
    setEstado({
      archivo: null,
      subiendo: false,
      progreso: 0,
      error: null,
      verificando: false
    });
  };

  // Validaciones específicas por tipo de archivo
  const validarArchivo = (archivo) => {
    const errores = [];
    
    // Validaciones generales
    if (!archivo) {
      errores.push('No se seleccionó ningún archivo');
      return errores;
    }

    // Validar extensión
    const extensionesPermitidas = ['.xlsx', '.xls'];
    const extension = archivo.name.toLowerCase().split('.').pop();
    if (!extensionesPermitidas.includes(`.${extension}`)) {
      errores.push(`Extensión no válida. Solo se permiten: ${extensionesPermitidas.join(', ')}`);
    }

    // Validar tamaño (máximo 10MB por defecto)
    const tamañoMaximo = 10 * 1024 * 1024; // 10MB en bytes
    if (archivo.size > tamañoMaximo) {
      errores.push(`El archivo es demasiado grande. Máximo permitido: 10MB`);
    }

    // Validaciones específicas por tipo
    const validacionesPorTipo = {
      [TIPOS_ARCHIVO_PAYROLL.LIBRO_REMUNERACIONES]: () => {
        // Validaciones específicas para libro de remuneraciones
        const nombreLower = archivo.name.toLowerCase();
        
        // Debe contener "libro" Y "remuneraciones" (o "remuneracion")
        const tieneLibro = nombreLower.includes('libro');
        const tieneRemuneraciones = nombreLower.includes('remuneraciones') || nombreLower.includes('remuneracion');
        
        if (!tieneLibro || !tieneRemuneraciones) {
          errores.push('El archivo debe contener "libro" Y "remuneraciones" en el nombre');
        }
        
        // No debe contener palabras prohibidas
        const palabrasProhibidas = ['mayor', 'balance', 'diario', 'movimientos'];
        const tienePalabrasProhibidas = palabrasProhibidas.some(palabra => 
          nombreLower.includes(palabra)
        );
        
        if (tienePalabrasProhibidas) {
          errores.push('El archivo no puede contener: mayor, balance, diario, movimientos');
        }
      },
      [TIPOS_ARCHIVO_PAYROLL.MOVIMIENTOS_MES]: () => {
        // Validaciones específicas para movimientos del mes
        const nombreLower = archivo.name.toLowerCase();
        if (!nombreLower.includes('movimientos')) {
          errores.push('El nombre del archivo debería contener "movimientos"');
        }
      }
      // Agregar más validaciones específicas según sea necesario
    };

    if (validacionesPorTipo[tipoArchivo]) {
      validacionesPorTipo[tipoArchivo]();
    }

    return errores;
  };

  return {
    estado,
    subirArchivo,
    validarArchivo,
    verificarExistencia,
    limpiarError,
    reiniciar,
    // Estados derivados para facilitar uso
    tieneArchivo: !!estado.archivo,
    estaSubiendo: estado.subiendo,
    tieneError: !!estado.error,
    estaVerificando: estado.verificando
  };
};

export default useArchivoUploadReal;
