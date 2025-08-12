// Este componente re-exporta LibroMayorCard con rutas actualizadas
import { lazy } from 'react';

const LibroMayorCard = lazy(() => import('../../../../components/TarjetasCierreContabilidad/LibroMayorCard'));

export default LibroMayorCard;
