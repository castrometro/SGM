// src/components/Header.jsx
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
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
          <img src={logo} alt="BDO Logo" className="h-10" />
          <span className="text-white font-semibold text-lg">Sistema de Gestion y Monitoreo SGM</span>
        </div>

        <div className="flex items-center gap-4 text-sm text-gray-300">
          <span>
            Bienvenido(a), <strong>{usuario?.nombre || '...'}</strong>
          </span>
          <button
            onClick={logout}
            className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-xs"
          >
            Cerrar sesión
          </button>
        </div>
      </div>
    </header>
  );
}
