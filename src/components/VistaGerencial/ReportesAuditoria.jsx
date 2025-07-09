import { useState } from "react";
import { 
  FileText, 
  Download, 
  Calendar, 
  Filter,
  Search,
  Eye,
  Clock,
  CheckCircle,
  BarChart3,
  Archive,
  Shield
} from "lucide-react";

const ReportesAuditoria = ({ cierres }) => {
  const [tipoReporte, setTipoReporte] = useState("trazabilidad");
  const [fechaInicio, setFechaInicio] = useState("");
  const [fechaFin, setFechaFin] = useState("");
  const [clienteFiltro, setClienteFiltro] = useState("");

  // Obtener clientes únicos para el filtro
  const clientesUnicos = [...new Set(cierres.map(c => c.cliente_nombre))].sort();

  // Tipos de reportes disponibles
  const tiposReporte = [
    {
      id: "trazabilidad",
      nombre: "Trazabilidad Completa",
      descripcion: "Historial detallado de cada proceso",
      icono: FileText,
      disponible: true
    },
    {
      id: "performance",
      nombre: "Performance de Analistas",
      descripcion: "Métricas de rendimiento por analista",
      icono: BarChart3,
      disponible: true
    },
    {
      id: "cumplimiento",
      nombre: "Cumplimiento de Plazos",
      descripcion: "Análisis de tiempos por cliente y período",
      icono: Clock,
      disponible: true
    },
    {
      id: "incidencias",
      nombre: "Reporte de Incidencias",
      descripcion: "Consolidado de incidencias y resoluciones",
      icono: Shield,
      disponible: true
    },
    {
      id: "auditoria",
      nombre: "Auditoría Completa",
      descripcion: "Reporte completo para auditorías internas",
      icono: Archive,
      disponible: false // Solo diseño
    }
  ];

  // Simular datos de reportes recientes
  const reportesRecientes = [
    {
      id: 1,
      nombre: "Trazabilidad_Nomina_Junio2025.pdf",
      tipo: "Trazabilidad Completa",
      fechaGeneracion: "2025-07-08T10:30:00Z",
      tamaño: "2.4 MB",
      estado: "completado"
    },
    {
      id: 2,
      nombre: "Performance_Analistas_Q2_2025.xlsx",
      tipo: "Performance de Analistas", 
      fechaGeneracion: "2025-07-07T15:45:00Z",
      tamaño: "856 KB",
      estado: "completado"
    },
    {
      id: 3,
      nombre: "Cumplimiento_Plazos_Mayo2025.pdf",
      tipo: "Cumplimiento de Plazos",
      fechaGeneracion: "2025-07-05T09:15:00Z",
      tamaño: "1.8 MB",
      estado: "completado"
    }
  ];

  const handleGenerarReporte = () => {
    // Simulación de generación de reporte
    alert(`Generando reporte: ${tiposReporte.find(t => t.id === tipoReporte)?.nombre}\n\nFiltros aplicados:\n- Período: ${fechaInicio || 'No especificado'} - ${fechaFin || 'No especificado'}\n- Cliente: ${clienteFiltro || 'Todos'}\n\n⚠️ Funcionalidad en desarrollo`);
  };

  const formatearFecha = (fecha) => {
    return new Date(fecha).toLocaleDateString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center gap-3 mb-6">
        <div className="flex items-center justify-center w-10 h-10 bg-blue-600 rounded-lg">
          <FileText size={20} className="text-white" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-white">
            Reportes y Auditoría
          </h2>
          <p className="text-gray-400 text-sm">
            Generar reportes con trazabilidad completa
          </p>
        </div>
      </div>

      {/* Sección de generación de reportes */}
      <div className="bg-gray-700 rounded-lg p-4 mb-6">
        <h3 className="text-white font-medium mb-4">Generar Nuevo Reporte</h3>
        
        {/* Selector de tipo de reporte */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
          {tiposReporte.map(tipo => {
            const IconoTipo = tipo.icono;
            return (
              <button
                key={tipo.id}
                onClick={() => setTipoReporte(tipo.id)}
                disabled={!tipo.disponible}
                className={`p-3 rounded-lg border transition-colors text-left ${
                  tipoReporte === tipo.id
                    ? 'border-blue-500 bg-blue-600/20'
                    : 'border-gray-600 hover:border-gray-500'
                } ${!tipo.disponible ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <IconoTipo size={16} className={tipoReporte === tipo.id ? 'text-blue-400' : 'text-gray-400'} />
                  <span className="text-white text-sm font-medium">{tipo.nombre}</span>
                  {!tipo.disponible && (
                    <span className="text-xs bg-orange-600 text-white px-2 py-1 rounded">
                      Próximo
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-400">{tipo.descripcion}</p>
              </button>
            );
          })}
        </div>

        {/* Filtros */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Fecha Inicio</label>
            <input
              type="date"
              value={fechaInicio}
              onChange={(e) => setFechaInicio(e.target.value)}
              className="w-full bg-gray-600 border border-gray-500 rounded px-3 py-2 text-white text-sm"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Fecha Fin</label>
            <input
              type="date"
              value={fechaFin}
              onChange={(e) => setFechaFin(e.target.value)}
              className="w-full bg-gray-600 border border-gray-500 rounded px-3 py-2 text-white text-sm"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Cliente</label>
            <select
              value={clienteFiltro}
              onChange={(e) => setClienteFiltro(e.target.value)}
              className="w-full bg-gray-600 border border-gray-500 rounded px-3 py-2 text-white text-sm"
            >
              <option value="">Todos los clientes</option>
              {clientesUnicos.map(cliente => (
                <option key={cliente} value={cliente}>{cliente}</option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={handleGenerarReporte}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Download size={16} />
              Generar
            </button>
          </div>
        </div>
      </div>

      {/* Reportes recientes */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white font-medium">Reportes Recientes</h3>
          <div className="flex items-center gap-2">
            <Search size={16} className="text-gray-400" />
            <input
              type="text"
              placeholder="Buscar reportes..."
              className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-white text-sm placeholder-gray-400 w-48"
            />
          </div>
        </div>

        <div className="space-y-3">
          {reportesRecientes.map(reporte => (
            <div key={reporte.id} className="bg-gray-700 rounded-lg p-4 hover:bg-gray-650 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-8 h-8 bg-green-600 rounded-lg">
                    <CheckCircle size={16} className="text-white" />
                  </div>
                  <div>
                    <h4 className="text-white font-medium">{reporte.nombre}</h4>
                    <div className="flex items-center gap-4 text-sm text-gray-400">
                      <span>{reporte.tipo}</span>
                      <span>•</span>
                      <span>{formatearFecha(reporte.fechaGeneracion)}</span>
                      <span>•</span>
                      <span>{reporte.tamaño}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button className="flex items-center gap-1 px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition-colors">
                    <Eye size={14} />
                    Ver
                  </button>
                  <button className="flex items-center gap-1 px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700 transition-colors">
                    <Download size={14} />
                    Descargar
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Nota informativa */}
        <div className="mt-6 bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
          <div className="flex items-start gap-2">
            <FileText className="w-4 h-4 text-blue-400 mt-0.5" />
            <div className="text-sm text-blue-300">
              <strong>Trazabilidad Completa:</strong> Todos los reportes incluyen timestamps, 
              usuarios responsables, cambios de estado y documentación completa para auditorías internas.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportesAuditoria;
