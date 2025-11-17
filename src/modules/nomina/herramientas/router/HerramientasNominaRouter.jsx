// src/modules/nomina/herramientas/router/HerramientasNominaRouter.jsx
import { Routes, Route, Navigate } from 'react-router-dom';
import HerramientasNominaPage from '../pages/HerramientasNominaPage';

/**
 * Router del módulo de Herramientas de Nómina
 * 
 * Gestiona las rutas del módulo de herramientas.
 * 
 * @component
 */
const HerramientasNominaRouter = () => {
  return (
    <Routes>
      <Route index element={<HerramientasNominaPage />} />
      {/* Rutas futuras para herramientas específicas */}
      {/* <Route path="captura-masiva" element={<CapturaMasivaPage />} /> */}
      <Route path="*" element={<Navigate to="/menu/nomina/tools" replace />} />
    </Routes>
  );
};

export default HerramientasNominaRouter;
