// Re-exportación con lazy loading del modal de nombres en inglés
import { lazy } from 'react';

const ModalNombresInglesCRUD = lazy(() => 
  import('../../../../../components/TarjetasCierreContabilidad/ModalNombresInglesCRUD')
);

export default ModalNombresInglesCRUD;
