// src/modules/contabilidad/historial-cierres/router/HistorialCierresContabilidadRouter.jsx
import { Routes, Route, Navigate } from 'react-router-dom';
import HistorialCierresContabilidadPage from '../pages/HistorialCierresContabilidadPage';

/**
 * Router del módulo de Historial de Cierres de Contabilidad
 */
const HistorialCierresContabilidadRouter = () => {
  return (
    <Routes>
      <Route index element={<HistorialCierresContabilidadPage />} />
      <Route path="*" element={<Navigate to="/menu/clientes" replace />} />
    </Routes>
  );
};

export default HistorialCierresContabilidadRouter;
