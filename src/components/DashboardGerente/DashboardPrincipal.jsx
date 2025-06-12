// src/components/DashboardGerente/DashboardPrincipal.jsx
import { useState, useEffect } from 'react';
import { obtenerMetricasAvanzadas } from '../../api/gerente';
import { obtenerUsuario } from '../../api/auth';
import MetricasAvanzadas from './MetricasAvanzadas';
import GestionClientesAvanzada from './GestionClientesAvanzada';
import AnalisisPortafolioClientes from './AnalisisPortafolioClientes';
import SistemaAlertas from './SistemaAlertas';
import SistemaReportes from './SistemaReportes';
import GestionAnalistas from './GestionAnalistas';

const DashboardPrincipal = () => {
  const [usuario, setUsuario] = useState(null);
  const [vistaActiva, setVistaActiva] = useState('metricas');
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    cargarUsuario();
  }, []);

  const cargarUsuario = async () => {
    try {
      const userData = await obtenerUsuario();
      setUsuario(userData);
    } catch (error) {
      console.error('Error cargando usuario:', error);
    } finally {
      setCargando(false);
    }
  };

  const vistas = [
    { 
      id: 'metricas', 
      nombre: 'Métricas', 
      icono: '📊',
      descripcion: 'KPIs y métricas del equipo'
    },
    { 
      id: 'clientes', 
      nombre: 'Clientes', 
      icono: '👥',
      descripcion: 'Gestión avanzada de clientes'
    },
    { 
      id: 'portafolio', 
      nombre: 'Portafolio', 
      icono: '💼',
      descripcion: 'Análisis de portafolio'
    },
    { 
      id: 'analistas', 
      nombre: 'Equipo', 
      icono: '👨‍💼',
      descripcion: 'Gestión de analistas'
    },
    { 
      id: 'alertas', 
      nombre: 'Alertas', 
      icono: '🔔',
      descripcion: 'Sistema de alertas'
    },
    { 
      id: 'reportes', 
      nombre: 'Reportes', 
      icono: '📋',
      descripcion: 'Generación de reportes'
    }
  ];

  const renderVistaActiva = () => {
    const props = { areas: usuario?.areas || [] };

    switch (vistaActiva) {
      case 'metricas':
        return <MetricasAvanzadas {...props} />;
      case 'clientes':
        return <GestionClientesAvanzada {...props} />;
      case 'portafolio':
        return <AnalisisPortafolioClientes {...props} />;
      case 'analistas':
        return <GestionAnalistas {...props} />;
      case 'alertas':
        return <SistemaAlertas {...props} />;
      case 'reportes':
        return <SistemaReportes {...props} />;
      default:
        return <MetricasAvanzadas {...props} />;
    }
  };

  if (cargando) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p className="text-white text-lg">Cargando Dashboard...</p>
        </div>
      </div>
    );
  }

  if (!usuario) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center text-white">
          <h1 className="text-2xl font-bold mb-4">Error de Acceso</h1>
          <p>No se pudo cargar la información del usuario.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-white">
                Dashboard Gerente
              </h1>
              <p className="text-gray-400">
                Bienvenido, {usuario.nombre} {usuario.apellido}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-sm text-gray-400">
                Áreas: {usuario.areas?.map(area => area.nombre || area).join(', ')}
              </div>
              <div className="h-8 w-8 bg-blue-600 rounded-full flex items-center justify-center">
                <span className="text-white font-semibold">
                  {usuario.nombre?.charAt(0)}{usuario.apellido?.charAt(0)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8 overflow-x-auto">
            {vistas.map((vista) => (
              <button
                key={vista.id}
                onClick={() => setVistaActiva(vista.id)}
                className={`flex items-center gap-2 py-4 px-2 border-b-2 font-medium text-sm whitespace-nowrap ${
                  vistaActiva === vista.id
                    ? 'border-blue-500 text-blue-500'
                    : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                }`}
              >
                <span className="text-lg">{vista.icono}</span>
                <div className="text-left">
                  <div>{vista.nombre}</div>
                  <div className="text-xs opacity-75">{vista.descripcion}</div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderVistaActiva()}
      </div>

      {/* Quick Actions Floating Button */}
      <div className="fixed bottom-6 right-6">
        <div className="bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-lg cursor-pointer transition-all">
          <span className="text-2xl">⚡</span>
        </div>
      </div>
    </div>
  );
};

export default DashboardPrincipal;
