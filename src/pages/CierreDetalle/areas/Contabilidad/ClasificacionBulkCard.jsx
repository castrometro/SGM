// Este componente re-exporta ClasificacionBulkCard con rutas actualizadas
import { lazy } from 'react';

const ClasificacionBulkCard = lazy(() => import('../../../../components/TarjetasCierreContabilidad/ClasificacionBulkCard'));

export default ClasificacionBulkCard;
