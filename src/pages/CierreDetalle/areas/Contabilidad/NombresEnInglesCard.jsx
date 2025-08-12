// Este componente re-exporta NombresEnInglesCard con rutas actualizadas
import { lazy } from 'react';

const NombresEnInglesCard = lazy(() => import('../../../../components/TarjetasCierreContabilidad/NombresEnInglesCard'));

export default NombresEnInglesCard;
