// Re-exportación con lazy loading del modal de tipo documento
import { lazy } from 'react';

const ModalTipoDocumentoCRUD = lazy(() => 
  import('../../../../../components/TarjetasCierreContabilidad/ModalTipoDocumentoCRUD')
);

export default ModalTipoDocumentoCRUD;
