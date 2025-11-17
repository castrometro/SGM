// src/modules/nomina/cliente-detalle/router/ClienteDetalleNominaRouter.jsx
import { Routes, Route, Navigate } from 'react-router-dom';
import ClienteDetalleNominaPage from '../pages/ClienteDetalleNominaPage';

/**
 * Router del módulo de Detalle de Cliente de Nómina
 * 
 * Gestiona las rutas del módulo de detalle de cliente.
 * 
 * @component
 */
const ClienteDetalleNominaRouter = () => {
  return (
    <Routes>
      <Route index element={<ClienteDetalleNominaPage />} />
      {/* Rutas futuras para sub-secciones */}
      <Route path="*" element={<Navigate to="/menu/clientes" replace />} />
    </Routes>
  );
};

export default ClienteDetalleNominaRouter;
