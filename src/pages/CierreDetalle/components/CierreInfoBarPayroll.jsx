import CierreInfoBarGenerico from "./CierreInfoBarGenerico";
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';

const CierreInfoBarPayroll = ({ cierre, cliente, onCierreActualizado }) => {
  const navigate = useNavigate();
  const [procesandoPayroll, setProcesandoPayroll] = useState(false);

  // Función para manejar actualización específica de payroll
  const manejarActualizarPayroll = async () => {
    setProcesandoPayroll(true);
    try {
      // TODO: Implementar API específica de payroll
      console.log('Actualizando estado de cierre payroll:', cierre.id);
      
      // Simulación de llamada API
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // TODO: Cuando se implemente la API real, reemplazar esto
      alert('Estado del cierre payroll actualizado (simulado)');
      
      if (onCierreActualizado) {
        onCierreActualizado({
          ...cierre,
          estado: getNextEstado(cierre.estado)
        });
      }
    } catch (error) {
      console.error('Error actualizando estado payroll:', error);
      alert('Error al actualizar el estado del cierre payroll');
    } finally {
      setProcesandoPayroll(false);
    }
  };

  // Determinar el siguiente estado en el flujo de payroll
  const getNextEstado = (estadoActual) => {
    const flujoPayroll = {
      'pendiente': 'procesando',
      'procesando': 'validando',
      'validando': 'validado',
      'validado': 'finalizado'
    };
    return flujoPayroll[estadoActual] || estadoActual;
  };

  // Botones específicos para payroll con mejor lógica
  const botonesPayroll = [
    {
      texto: "Ver Dashboard Payroll",
      onClick: () => navigate(`/menu/clientes/${cliente?.id}/cierres-payroll/${cierre.id}/dashboard`),
      className: "bg-emerald-600 hover:bg-emerald-700 text-white",
      icono: (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      mostrarEn: ['procesando', 'validando', 'validado', 'finalizado']
    },
    {
      texto: "Ver Detalle Empleados",
      onClick: () => navigate(`/menu/clientes/${cliente?.id}/cierres-payroll/${cierre.id}/empleados`),
      className: "bg-blue-600 hover:bg-blue-700 text-white",
      icono: (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      ),
      mostrarEn: ['procesando', 'validando', 'validado', 'finalizado']
    },
    {
      texto: "Exportar Reportes",
      onClick: () => navigate(`/menu/clientes/${cliente?.id}/cierres-payroll/${cierre.id}/exportar`),
      className: "bg-purple-600 hover:bg-purple-700 text-white",
      icono: (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      mostrarEn: ['validado', 'finalizado']
    }
  ];

  // Filtrar botones según el estado del cierre
  const botonesFiltrados = botonesPayroll.filter(boton => 
    !boton.mostrarEn || boton.mostrarEn.includes(cierre?.estado)
  );

  return (
    <CierreInfoBarGenerico
      cierre={cierre}
      cliente={cliente}
      onCierreActualizado={onCierreActualizado}
      tipoModulo="payroll"
      botonesPersonalizados={botonesFiltrados}
      manejarActualizarCustom={manejarActualizarPayroll}
      procesandoCustom={procesandoPayroll}
    />
  );
};

export default CierreInfoBarPayroll;
