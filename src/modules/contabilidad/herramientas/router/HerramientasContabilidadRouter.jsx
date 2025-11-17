// src/modules/contabilidad/herramientas/router/HerramientasContabilidadRouter.jsx
import { Routes, Route, Navigate } from 'react-router-dom';
import HerramientasContabilidadPage from '../pages/HerramientasContabilidadPage';

/**
 * Router del módulo de Herramientas de Contabilidad
 * 
 * Gestiona las rutas del módulo de herramientas.
 * 
 * @component
 */
const HerramientasContabilidadRouter = () => {
  return (
    <Routes>
      <Route index element={<HerramientasContabilidadPage />} />
      {/* Rutas futuras para herramientas específicas */}
      {/* <Route path="clasificacion" element={<ClasificacionPage />} /> */}
      <Route path="*" element={<Navigate to="/menu/contabilidad/tools" replace />} />
    </Routes>
  );
};

export default HerramientasContabilidadRouter;
