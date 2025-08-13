// Re-exportación con lazy loading del modal más complejo
import { lazy } from 'react';

const ModalClasificacionRegistrosRaw = lazy(() => 
  import('../../../../../components/TarjetasCierreContabilidad/ModalClasificacionRegistrosRaw')
);

export default ModalClasificacionRegistrosRaw;
