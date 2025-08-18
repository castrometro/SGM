import CierreInfoBarGenerico from "./CierreInfoBarGenerico";
import { useNavigate } from 'react-router-dom';

const CierreInfoBarRRHH = ({ cierre, cliente, onCierreActualizado }) => {
  const navigate = useNavigate();

  // Botones específicos para RRHH
  const botonesRRHH = [
    {
      texto: "Ver Indicadores RRHH",
      onClick: () => navigate(`/menu/cierres-rrhh/${cierre.id}/indicadores`),
      className: "bg-purple-600 hover:bg-purple-700 text-white",
      icono: (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      mostrarEn: ['datos_disponibles', 'analisis_completo', 'finalizado']
    },
    {
      texto: "Generar Reportes",
      onClick: () => navigate(`/menu/cierres-rrhh/${cierre.id}/reportes`),
      className: "bg-indigo-600 hover:bg-indigo-700 text-white",
      icono: (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      mostrarEn: ['analisis_completo', 'finalizado']
    }
  ];

  // Filtrar botones según el estado del cierre
  const botonesFiltrados = botonesRRHH.filter(boton => 
    !boton.mostrarEn || boton.mostrarEn.includes(cierre?.estado)
  );

  return (
    <CierreInfoBarGenerico
      cierre={cierre}
      cliente={cliente}
      onCierreActualizado={onCierreActualizado}
      tipoModulo="rrhh"
      botonesPersonalizados={botonesFiltrados}
    />
  );
};

export default CierreInfoBarRRHH;
