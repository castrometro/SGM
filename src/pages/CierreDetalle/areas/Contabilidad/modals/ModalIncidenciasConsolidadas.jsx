// Re-exportación con lazy loading del modal de incidencias
import { lazy } from 'react';

const ModalIncidenciasConsolidadas = lazy(() => 
  import('../../../../../components/TarjetasCierreContabilidad/ModalIncidenciasConsolidadas')
);

export default ModalIncidenciasConsolidadas;
