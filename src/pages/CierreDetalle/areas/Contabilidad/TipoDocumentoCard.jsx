// Este componente re-exporta TipoDocumentoCard con rutas actualizadas
import { lazy } from 'react';

// Importación lazy del componente original
const TipoDocumentoCard = lazy(() => import('../../../../components/TarjetasCierreContabilidad/TipoDocumentoCard'));

export default TipoDocumentoCard;
