// src/components/Header.jsx
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import AreaIndicator from './AreaIndicator';
import logo from '../assets/BDO_LOGO.png';

export default function Header() {
  const { usuario } = useAuth();
  const navigate = useNavigate();

  const logout = () => {
    localStorage.clear();
    navigate('/');
  };

  return (
    <header className="w-full bg-gray-800 px-6 py-4 shadow-md">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-4">
          <img 
            src={logo} 
            alt="BDO Logo" 
            className="h-10 cursor-pointer hover:opacity-80 transition-opacity" 
            onClick={() => navigate('/menu')}
          />
          <span className="text-white font-semibold text-lg">Sistema de Gestion y Monitoreo SGM</span>
        </div>
        <div className="flex items-center gap-6 text-sm text-gray-300">
          {/* Indicador de áreas para gerentes */}
          {usuario?.tipo_usuario === "gerente" && usuario?.areas && Array.isArray(usuario.areas) && usuario.areas.length > 0 && (
            <AreaIndicator 
              areas={usuario.areas} 
              size="sm" 
              className="border-l border-gray-600 pl-4"
            />
          )}
          
          <div className="flex items-center gap-3">
            <span>
              Bienvenido(a), <strong>{usuario?.nombre || '...'}</strong>
            </span>
            <button
              onClick={logout}
              className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-xs transition-colors"
            >
              Cerrar sesión
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
