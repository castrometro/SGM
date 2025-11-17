// src/pages/MenuModuleDemo.jsx
import { Link, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { MenuUsuarioPage as MenuContabilidad } from '../modules/contabilidad/menu';
import { MenuUsuarioPage as MenuNomina } from '../modules/nomina/menu';
import { DevModulesButton } from '../modules/shared/auth';
import { Header, Footer } from '../modules/shared/common';
import { FiArrowLeft, FiCheckCircle, FiUser, FiBriefcase, FiAlertCircle } from 'react-icons/fi';

/**
 * Demo del módulo Menu refactorizado
 * Usa el token real del usuario autenticado
 */
const MenuModuleDemo = () => {
  const navigate = useNavigate();
  const [usuario, setUsuario] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Leer usuario real del localStorage
    const token = localStorage.getItem('token');
    const usuarioData = localStorage.getItem('usuario');

    if (!token || !usuarioData) {
      // Si no hay sesión, redirigir al login
      setLoading(false);
      return;
    }

    try {
      const user = JSON.parse(usuarioData);
      setUsuario(user);
    } catch (error) {
      console.error('Error al parsear usuario:', error);
    }
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-lg">Cargando...</div>
      </div>
    );
  }

  if (!usuario) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-6 max-w-md">
          <div className="flex items-center gap-3 mb-4">
            <FiAlertCircle className="text-red-400" size={24} />
            <h2 className="text-xl font-bold text-red-400">Sesión requerida</h2>
          </div>
          <p className="text-gray-300 mb-4">
            Debes iniciar sesión para ver el demo del menú con tu usuario real.
          </p>
          <div className="flex gap-3">
            <Link
              to="/"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium transition-colors"
            >
              Ir al Login
            </Link>
            <Link
              to="/dev/modules"
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-white font-medium transition-colors"
            >
              Volver al Showcase
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Determinar qué menú mostrar según las áreas del usuario
  const userAreas = usuario.areas || [];
  console.log('🔍 MenuModuleDemo - Áreas del usuario:', userAreas);
  
  // Helper para normalizar nombres (sin tildes, lowercase)
  const normalizar = (str) => str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  
  // Soportar áreas como strings o como objetos
  const hasNomina = userAreas.some(area => {
    const nombreArea = typeof area === 'string' ? area : area.nombre;
    return normalizar(nombreArea) === 'nomina';
  });
  
  const hasContabilidad = userAreas.some(area => {
    const nombreArea = typeof area === 'string' ? area : area.nombre;
    return normalizar(nombreArea) === 'contabilidad';
  });
  
  console.log('📊 MenuModuleDemo - hasNomina:', hasNomina, 'hasContabilidad:', hasContabilidad);
  
  // Determinar el área activa (la primera en la lista)
  let areaActiva = 'Sin área';
  if (userAreas.length > 0) {
    const primeraArea = userAreas[0];
    areaActiva = typeof primeraArea === 'string' ? primeraArea : primeraArea.nombre;
  }
  
  // Seleccionar el menú según el área activa (normalizando)
  const MenuComponent = normalizar(areaActiva) === 'nomina' ? MenuNomina : MenuContabilidad;
  
  console.log('✅ MenuModuleDemo - Área activa:', areaActiva, '- Componente:', normalizar(areaActiva) === 'nomina' ? 'MenuNomina' : 'MenuContabilidad');

  return (
    <div className="flex flex-col min-h-screen bg-gray-900 text-gray-100">
      {/* Banner de Demo */}
      <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 w-full max-w-4xl px-4">
        <div className="bg-yellow-100 border-2 border-yellow-400 rounded-lg shadow-lg p-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <FiCheckCircle className="text-green-600" size={20} />
              <div>
                <span className="text-sm font-semibold text-gray-900 block">
                  DEMO: Módulo Menu Refactorizado
                </span>
                <span className="text-xs text-gray-700">
                  Usuario: {usuario.nombre} ({usuario.tipo_usuario})
                </span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Info de Áreas */}
              <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-100 border border-blue-300 rounded-md">
                <FiBriefcase className="text-blue-700" size={14} />
                <span className="text-xs font-medium text-blue-900">
                  Área: {areaActiva}
                </span>
              </div>

              {/* Botón Volver */}
              <Link
                to="/dev/modules"
                className="inline-flex items-center gap-2 px-3 py-1.5 bg-white border border-gray-300 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-50 transition-colors"
              >
                <FiArrowLeft size={14} />
                Volver
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Fondo con gradiente */}
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 opacity-80"></div>
        <div className="absolute inset-0 backdrop-blur-sm"></div>
      </div>

      {/* Contenedor principal con Header, Content y Footer */}
      <div className="relative z-10 flex flex-col min-h-screen">
        <Header />
        
        {/* Contenido - MenuUsuarioPage según área del usuario */}
        <main className="flex-grow container mx-auto p-6 pt-32">
          <MenuComponent />
        </main>

        <Footer />
      </div>

      {/* Botón flotante de desarrollo */}
      <DevModulesButton />
    </div>
  );
};

export default MenuModuleDemo;
