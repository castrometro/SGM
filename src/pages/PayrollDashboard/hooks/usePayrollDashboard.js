import { useState, useEffect } from 'react';
import { obtenerUsuario } from '../../../api/auth';
import { PAYROLL_USER_CONFIG, getUserWidgets, MESSAGES } from '../config/dashboardConfig';

export const usePayrollDashboard = () => {
  const [usuario, setUsuario] = useState(null);
  const [areaActiva, setAreaActiva] = useState(null);
  const [dashboardData, setDashboardData] = useState({});
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const cargarDatos = async () => {
      setCargando(true);
      setError("");
      
      try {
        const userData = await obtenerUsuario();
        setUsuario(userData);

        // Determinar área activa
        let area = null;
        if (userData.area_activa) {
          area = userData.area_activa;
        } else if (userData.areas && userData.areas.length > 0) {
          area = userData.areas.find(a => (a.nombre || a) === 'Payroll')?.nombre || 
                 userData.areas.find(a => (a.nombre || a) === 'RRHH')?.nombre ||
                 userData.areas[0].nombre || userData.areas[0];
        } else {
          setError("No tienes acceso al área de Payroll.");
          setCargando(false);
          return;
        }
        
        setAreaActiva(area);

        // Verificar si tiene acceso a payroll
        const hasPayrollAccess = userData.areas?.some(a => 
          (a.nombre || a).toLowerCase().includes('payroll') || 
          (a.nombre || a).toLowerCase().includes('rrhh') ||
          (a.nombre || a).toLowerCase().includes('nomina')
        );

        if (!hasPayrollAccess) {
          setError("No tienes acceso al módulo de Payroll.");
          setCargando(false);
          return;
        }

        // Cargar datos del dashboard (simulados por ahora)
        const mockData = await cargarDashboardData(userData.tipo_usuario, area);
        setDashboardData(mockData);

        console.log('=== DEBUG: Dashboard Payroll ===');
        console.log('Usuario:', userData.nombre, userData.apellido);
        console.log('Tipo:', userData.tipo_usuario);
        console.log('Área activa:', area);
        console.log('Widgets disponibles:', getUserWidgets(userData.tipo_usuario));
        console.log('================================');

      } catch (err) {
        setError(MESSAGES.error);
        console.error("Error al cargar dashboard payroll:", err);
      }
      
      setCargando(false);
    };

    cargarDatos();
  }, []);

  // Función para cargar datos del dashboard (mock por ahora)
  const cargarDashboardData = async (tipoUsuario, area) => {
    // Simular carga de datos desde API
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    return {
      empleados: {
        total: 150,
        activos: 145,
        inactivos: 5,
        trend: "+2.3%"
      },
      nominasEnProceso: {
        total: 8,
        pendientes: 3,
        revision: 5,
        trend: "-1"
      },
      nominasAprobadas: {
        total: 12,
        esteMes: 12,
        mesAnterior: 11,
        trend: "+8.3%"
      },
      costoMensual: {
        total: 45000000,
        sueldos: 38000000,
        bonos: 4500000,
        descuentos: 2500000,
        trend: "+3.2%"
      },
      alertas: {
        total: 4,
        criticas: 1,
        importantes: 2,
        informativas: 1
      },
      reportes: {
        total: 25,
        generados: 23,
        pendientes: 2,
        trend: "+15%"
      }
    };
  };

  const userConfig = usuario ? PAYROLL_USER_CONFIG[usuario.tipo_usuario] : null;
  const widgets = usuario ? getUserWidgets(usuario.tipo_usuario) : [];

  return {
    usuario,
    areaActiva,
    dashboardData,
    userConfig,
    widgets,
    cargando,
    error
  };
};
