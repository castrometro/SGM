// src/modules/auth/components/PrivateRoute.jsx
import { Navigate } from "react-router-dom";

/**
 * Componente de protección de rutas privadas
 * Redirige a login si no hay token de autenticación
 * @component
 * @param {Object} props
 * @param {React.ReactNode} props.children - Componentes hijo a proteger
 */
export default function PrivateRoute({ children }) {
  const token = localStorage.getItem("token");
  return token ? children : <Navigate to="/" />;
}
