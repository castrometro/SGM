// src/modules/contabilidad/cliente-detalle/router/ClienteDetalleContabilidadRouter.jsx
import { Routes, Route, Navigate } from 'react-router-dom';
import ClienteDetalleContabilidadPage from '../pages/ClienteDetalleContabilidadPage';

/**
 * Router del módulo de Detalle de Cliente de Contabilidad
 * 
 * Gestiona las rutas del módulo de detalle de cliente.
 * 
 * @component
 */
const ClienteDetalleContabilidadRouter = () => {
  return (
    <Routes>
      <Route index element={<ClienteDetalleContabilidadPage />} />
      {/* Rutas futuras para sub-secciones */}
      <Route path="*" element={<Navigate to="/menu/clientes" replace />} />
    </Routes>
  );
};

export default ClienteDetalleContabilidadRouter;
