import { useState } from "react";
import { 
  Users, 
  Clock, 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  Filter,
  Search,
  Eye,
  FileText
} from "lucide-react";
import { Link } from "react-router-dom";
import EstadoBadge from "../EstadoBadge";

const ResumenProcesosNomina = ({ cierres, onActualizar }) => {
  const [filtroEstado, setFiltroEstado] = useState("");
  const [busqueda, setBusqueda] = useState("");

  // Filtrar cierres según búsqueda y filtros
  const cierresFiltrados = cierres.filter(cierre => {
    const matchBusqueda = !busqueda || 
      cierre.cliente_nombre?.toLowerCase().includes(busqueda.toLowerCase()) ||
      cierre.periodo?.includes(busqueda);
    
    const matchEstado = !filtroEstado || cierre.estado === filtroEstado;
    
    return matchBusqueda && matchEstado;
  });

  // Estadísticas rápidas
  const estadisticas = {
    total: cierres.length,
    pendientes: cierres.filter(c => c.estado === 'pendiente' || c.estado === 'en_proceso').length,
    completados: cierres.filter(c => c.estado === 'completado' || c.estado === 'sin_incidencias').length,
    conIncidencias: cierres.filter(c => c.estado === 'incidencias_abiertas').length,
    atrasados: cierres.filter(c => {
      // Considerar atrasado si lleva más de 5 días desde creación
      const fechaCreacion = new Date(c.fecha_creacion);
      const hoy = new Date();
      const diasTranscurridos = (hoy - fechaCreacion) / (1000 * 60 * 60 * 24);
      return diasTranscurridos > 5 && !['completado', 'sin_incidencias'].includes(c.estado);
    }).length
  };

  const estados = [
    { value: "", label: "Todos los estados" },
    { value: "pendiente", label: "Pendiente" },
    { value: "en_proceso", label: "En Proceso" },
    { value: "datos_consolidados", label: "Datos Consolidados" },
    { value: "completado", label: "Completado" },
    { value: "incidencias_abiertas", label: "Con Incidencias" },
    { value: "sin_incidencias", label: "Sin Incidencias" },
  ];

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 bg-blue-600 rounded-lg">
            <Users size={20} className="text-white" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-white">
              Procesos de Nómina por Cliente
            </h2>
            <p className="text-gray-400 text-sm">
              Visión general de todos los cierres de nómina
            </p>
          </div>
        </div>
        <button
          onClick={onActualizar}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
        >
          Actualizar
        </button>
      </div>

      {/* Tarjetas de estadísticas rápidas */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <div className="bg-gray-700 p-4 rounded-lg text-center">
          <div className="text-2xl font-bold text-white">{estadisticas.total}</div>
          <div className="text-sm text-gray-400">Total Procesos</div>
        </div>
        <div className="bg-yellow-600 p-4 rounded-lg text-center">
          <div className="text-2xl font-bold text-white">{estadisticas.pendientes}</div>
          <div className="text-sm text-yellow-100">En Proceso</div>
        </div>
        <div className="bg-green-600 p-4 rounded-lg text-center">
          <div className="text-2xl font-bold text-white">{estadisticas.completados}</div>
          <div className="text-sm text-green-100">Completados</div>
        </div>
        <div className="bg-red-600 p-4 rounded-lg text-center">
          <div className="text-2xl font-bold text-white">{estadisticas.conIncidencias}</div>
          <div className="text-sm text-red-100">Con Incidencias</div>
        </div>
        <div className="bg-orange-600 p-4 rounded-lg text-center">
          <div className="text-2xl font-bold text-white">{estadisticas.atrasados}</div>
          <div className="text-sm text-orange-100">Posible Atraso</div>
        </div>
      </div>

      {/* Filtros */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="flex items-center gap-2 flex-1">
          <Search size={20} className="text-gray-400" />
          <input
            type="text"
            placeholder="Buscar por cliente o período..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter size={20} className="text-gray-400" />
          <select
            value={filtroEstado}
            onChange={(e) => setFiltroEstado(e.target.value)}
            className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
          >
            {estados.map(estado => (
              <option key={estado.value} value={estado.value}>
                {estado.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Tabla de cierres */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="text-left py-3 px-4 text-gray-300 font-medium">Cliente</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium">Período</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium">Estado</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium">Analista</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium">Días</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {cierresFiltrados.length === 0 ? (
              <tr>
                <td colSpan="6" className="text-center py-8 text-gray-400">
                  No se encontraron procesos con los filtros aplicados
                </td>
              </tr>
            ) : (
              cierresFiltrados.map(cierre => {
                const fechaCreacion = new Date(cierre.fecha_creacion);
                const hoy = new Date();
                const diasTranscurridos = Math.floor((hoy - fechaCreacion) / (1000 * 60 * 60 * 24));
                
                return (
                  <tr key={cierre.id} className="border-b border-gray-700 hover:bg-gray-750">
                    <td className="py-3 px-4">
                      <div className="font-medium text-white">{cierre.cliente_nombre}</div>
                      <div className="text-sm text-gray-400">ID: {cierre.cliente_id}</div>
                    </td>
                    <td className="py-3 px-4 text-white">{cierre.periodo}</td>
                    <td className="py-3 px-4">
                      <EstadoBadge estado={cierre.estado} size="sm" />
                    </td>
                    <td className="py-3 px-4">
                      <div className="text-white">
                        {cierre.usuario_analista || "Sin asignar"}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className={`text-sm ${diasTranscurridos > 5 ? 'text-red-400' : 'text-gray-400'}`}>
                        {diasTranscurridos} días
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex gap-2">
                        <Link
                          to={`/menu/nomina/cierres/${cierre.id}`}
                          className="flex items-center gap-1 px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition-colors"
                        >
                          <Eye size={14} />
                          Ver
                        </Link>
                        <button className="flex items-center gap-1 px-3 py-1 bg-gray-600 text-white rounded text-sm hover:bg-gray-700 transition-colors">
                          <FileText size={14} />
                          Reporte
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {cierresFiltrados.length > 0 && (
        <div className="mt-4 text-sm text-gray-400 text-center">
          Mostrando {cierresFiltrados.length} de {cierres.length} procesos
        </div>
      )}
    </div>
  );
};

export default ResumenProcesosNomina;
