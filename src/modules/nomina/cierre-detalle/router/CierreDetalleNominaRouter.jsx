// src/modules/nomina/cierre-detalle/router/CierreDetalleNominaRouter.jsx
import { Routes, Route } from 'react-router-dom';
import CierreDetalleNominaPage from '../pages/CierreDetalleNominaPage';

/**
 * Router para el módulo de cierre detalle de nómina
 */
const CierreDetalleNominaRouter = () => {
  return (
    <Routes>
      <Route index element={<CierreDetalleNominaPage />} />
      <Route path=":cierreId" element={<CierreDetalleNominaPage />} />
    </Routes>
  );
};

export default CierreDetalleNominaRouter;
