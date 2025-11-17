// src/modules/contabilidad/clientes/router/ClientesContabilidadRouter.jsx
import { Routes, Route, Navigate } from 'react-router-dom';
import ClientesContabilidadPage from '../pages/ClientesContabilidadPage';

/**
 * Router del módulo de Clientes de Contabilidad
 * 
 * Gestiona las rutas del módulo de clientes.
 * 
 * @component
 */
const ClientesContabilidadRouter = () => {
  return (
    <Routes>
      <Route index element={<ClientesContabilidadPage />} />
      {/* Rutas futuras para funcionalidades específicas */}
      <Route path="*" element={<Navigate to="/menu/clientes" replace />} />
    </Routes>
  );
};

export default ClientesContabilidadRouter;
