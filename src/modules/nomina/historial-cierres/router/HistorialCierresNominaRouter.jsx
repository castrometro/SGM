// src/modules/nomina/historial-cierres/router/HistorialCierresNominaRouter.jsx
import { Routes, Route, Navigate } from 'react-router-dom';
import HistorialCierresNominaPage from '../pages/HistorialCierresNominaPage';

/**
 * Router del módulo de Historial de Cierres de Nómina
 */
const HistorialCierresNominaRouter = () => {
  return (
    <Routes>
      <Route index element={<HistorialCierresNominaPage />} />
      <Route path="*" element={<Navigate to="/menu/clientes" replace />} />
    </Routes>
  );
};

export default HistorialCierresNominaRouter;
