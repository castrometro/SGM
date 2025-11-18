// src/modules/contabilidad/captura-gastos/router/CapturaGastosRouter.jsx
import { Routes, Route, Navigate } from 'react-router-dom';
import CapturaGastosPage from '../pages/CapturaGastosPage';

/**
 * Router del módulo de Captura Masiva de Gastos
 */
const CapturaGastosRouter = () => {
  return (
    <Routes>
      <Route index element={<CapturaGastosPage />} />
      <Route path="*" element={<Navigate to="/menu/contabilidad/tools" replace />} />
    </Routes>
  );
};

export default CapturaGastosRouter;
