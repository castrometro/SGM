// Re-exportación con lazy loading del modal de historial
import { lazy } from 'react';

const ModalHistorialReprocesamiento = lazy(() => 
  import('../../../../../components/TarjetasCierreContabilidad/ModalHistorialReprocesamiento')
);

export default ModalHistorialReprocesamiento;
