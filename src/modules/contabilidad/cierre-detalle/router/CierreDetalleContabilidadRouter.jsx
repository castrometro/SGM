// src/modules/contabilidad/cierre-detalle/router/CierreDetalleContabilidadRouter.jsx
import { Routes, Route } from 'react-router-dom';
import CierreDetalleContabilidadPage from '../pages/CierreDetalleContabilidadPage';

/**
 * Router para el módulo de cierre detalle de contabilidad
 */
const CierreDetalleContabilidadRouter = () => {
  return (
    <Routes>
      <Route index element={<CierreDetalleContabilidadPage />} />
      <Route path=":cierreId" element={<CierreDetalleContabilidadPage />} />
    </Routes>
  );
};

export default CierreDetalleContabilidadRouter;
