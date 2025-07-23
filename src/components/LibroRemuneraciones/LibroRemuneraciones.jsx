import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { obtenerLibroRemuneraciones } from '../../api/nomina';
import { 
  ArrowLeft, 
  Users, 
  DollarSign, 
  FileText, 
  Search,
  Filter,
  Download,
  Eye,
  EyeOff
} from 'lucide-react';

const LibroRemuneraciones = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [datos, setDatos] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [filtros, setFiltros] = useState({
    busqueda: '',
    estado: 'todos',
    mostrarSoloMontos: false
  });
  const [empleadoExpandido, setEmpleadoExpandido] = useState(null);

  useEffect(() => {
    cargarDatos();
  }, [id]);

  const cargarDatos = async () => {
    try {
      setCargando(true);
      const respuesta = await obtenerLibroRemuneraciones(id);
      setDatos(respuesta);
    } catch (error) {
      console.error('Error cargando libro de remuneraciones:', error);
      setError('Error al cargar los datos del libro de remuneraciones');
    } finally {
      setCargando(false);
    }
  };

  const empleadosFiltrados = datos?.empleados?.filter(empleado => {
    const cumpleBusqueda = !filtros.busqueda || 
      empleado.nombre_empleado.toLowerCase().includes(filtros.busqueda.toLowerCase()) ||
      empleado.rut_empleado.includes(filtros.busqueda);
    
    const cumpleEstado = filtros.estado === 'todos' || empleado.estado_empleado === filtros.estado;
    
    return cumpleBusqueda && cumpleEstado;
  }) || [];

  const headersFiltrados = filtros.mostrarSoloMontos 
    ? datos?.headers?.filter(header => {
        // Buscar si algún empleado tiene un valor numérico para este header
        return datos.empleados.some(emp => {
          const valor = emp.valores_headers[header];
          return valor && !isNaN(parseFloat(valor.replace(/[,$]/g, '')));
        });
      }) || []
    : datos?.headers || [];

  const formatearMonto = (valor) => {
    if (!valor) return '-';
    const numero = parseFloat(valor.toString().replace(/[,$]/g, ''));
    if (isNaN(numero)) return valor;
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0
    }).format(numero);
  };

  const esMontoNumerico = (valor) => {
    if (!valor) return false;
    const numero = parseFloat(valor.toString().replace(/[,$]/g, ''));
    return !isNaN(numero) && numero !== 0;
  };

  if (cargando) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500 mx-auto"></div>
          <p className="text-gray-400 mt-4">Cargando libro de remuneraciones...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="bg-red-600 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
            <FileText className="text-white" size={24} />
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">Error al cargar</h3>
          <p className="text-gray-400 mb-4">{error}</p>
          <button
            onClick={() => navigate(-1)}
            className="bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            Regresar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate(-1)}
                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
              >
                <ArrowLeft size={20} />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-teal-400">Libro de Remuneraciones</h1>
                <p className="text-gray-400">
                  {datos?.cierre?.cliente} - {datos?.cierre?.periodo}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <button
                onClick={() => window.print()}
                className="bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
              >
                <Download size={16} />
                Exportar
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Resumen */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total Empleados</p>
                <p className="text-2xl font-bold text-white">{datos?.resumen?.total_empleados || 0}</p>
              </div>
              <Users className="w-8 h-8 text-teal-500" />
            </div>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total Haberes</p>
                <p className="text-2xl font-bold text-green-400">
                  {formatearMonto(datos?.resumen?.total_haberes)}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-green-500" />
            </div>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total Descuentos</p>
                <p className="text-2xl font-bold text-red-400">
                  {formatearMonto(datos?.resumen?.total_descuentos)}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-red-500" />
            </div>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Líquido Total</p>
                <p className="text-2xl font-bold text-teal-400">
                  {formatearMonto(datos?.resumen?.liquido_total)}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-teal-500" />
            </div>
          </div>
        </div>

        {/* Filtros */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Buscar Empleado
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
                <input
                  type="text"
                  placeholder="Nombre o RUT..."
                  value={filtros.busqueda}
                  onChange={(e) => setFiltros(prev => ({ ...prev, busqueda: e.target.value }))}
                  className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Estado Empleado
              </label>
              <select
                value={filtros.estado}
                onChange={(e) => setFiltros(prev => ({ ...prev, estado: e.target.value }))}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-teal-500 focus:border-transparent"
              >
                <option value="todos">Todos</option>
                <option value="activo">Activo</option>
                <option value="nueva_incorporacion">Nueva Incorporación</option>
                <option value="finiquito">Finiquito</option>
                <option value="ausente_total">Ausente Total</option>
                <option value="ausente_parcial">Ausente Parcial</option>
              </select>
            </div>
            
            <div className="flex items-end">
              <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filtros.mostrarSoloMontos}
                  onChange={(e) => setFiltros(prev => ({ ...prev, mostrarSoloMontos: e.target.checked }))}
                  className="rounded border-gray-600 text-teal-600 focus:ring-teal-500"
                />
                Solo columnas con montos
              </label>
            </div>
            
            <div className="flex items-end justify-end">
              <p className="text-sm text-gray-400">
                {empleadosFiltrados.length} de {datos?.empleados?.length || 0} empleados
              </p>
            </div>
          </div>
        </div>

        {/* Tabla de empleados */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700 border-b border-gray-600">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider sticky left-0 bg-gray-700 z-10">
                    Empleado
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Estado
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Haberes
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Descuentos
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Líquido
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Detalles
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {empleadosFiltrados.map((empleado, index) => (
                  <React.Fragment key={empleado.id}>
                    <tr className={`hover:bg-gray-700 transition-colors ${
                      empleadoExpandido === empleado.id ? 'bg-gray-700' : 'bg-gray-800'
                    }`}>
                      <td className="px-6 py-4 sticky left-0 bg-inherit z-10">
                        <div className="flex flex-col">
                          <div className="text-sm font-medium text-white">
                            {empleado.nombre_empleado}
                          </div>
                          <div className="text-sm text-gray-400">
                            {empleado.rut_empleado}
                          </div>
                          {empleado.cargo && (
                            <div className="text-xs text-gray-500">
                              {empleado.cargo}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                          empleado.estado_empleado === 'activo' ? 'bg-green-900 text-green-300' :
                          empleado.estado_empleado === 'nueva_incorporacion' ? 'bg-blue-900 text-blue-300' :
                          empleado.estado_empleado === 'finiquito' ? 'bg-red-900 text-red-300' :
                          'bg-yellow-900 text-yellow-300'
                        }`}>
                          {empleado.estado_empleado.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right text-sm text-green-400 font-medium">
                        {formatearMonto(empleado.total_haberes)}
                      </td>
                      <td className="px-6 py-4 text-right text-sm text-red-400 font-medium">
                        {formatearMonto(empleado.total_descuentos)}
                      </td>
                      <td className="px-6 py-4 text-right text-sm text-teal-400 font-bold">
                        {formatearMonto(empleado.liquido_pagar)}
                      </td>
                      <td className="px-6 py-4 text-center">
                        <button
                          onClick={() => setEmpleadoExpandido(
                            empleadoExpandido === empleado.id ? null : empleado.id
                          )}
                          className="text-teal-400 hover:text-teal-300 transition-colors"
                        >
                          {empleadoExpandido === empleado.id ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                      </td>
                    </tr>
                    
                    {empleadoExpandido === empleado.id && (
                      <tr>
                        <td colSpan="6" className="px-6 py-4 bg-gray-750">
                          <div className="space-y-4">
                            {/* Headers con valores */}
                            <div>
                              <h4 className="text-sm font-medium text-gray-300 mb-3">
                                Detalles por Concepto ({headersFiltrados.length} conceptos)
                              </h4>
                              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-64 overflow-y-auto">
                                {headersFiltrados.map(header => {
                                  const valor = empleado.valores_headers[header];
                                  const esNumerico = esMontoNumerico(valor);
                                  
                                  return (
                                    <div
                                      key={header}
                                      className={`p-3 rounded-lg border ${
                                        esNumerico 
                                          ? 'bg-gray-800 border-gray-600' 
                                          : 'bg-gray-900 border-gray-700'
                                      }`}
                                    >
                                      <div className="text-xs text-gray-400 mb-1">
                                        {header}
                                      </div>
                                      <div className={`text-sm font-medium ${
                                        esNumerico ? 'text-teal-400' : 'text-gray-300'
                                      }`}>
                                        {esNumerico ? formatearMonto(valor) : (valor || '-')}
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                            
                            {/* Conceptos consolidados */}
                            {empleado.conceptos && empleado.conceptos.length > 0 && (
                              <div>
                                <h4 className="text-sm font-medium text-gray-300 mb-3">
                                  Conceptos Consolidados ({empleado.conceptos.length})
                                </h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                  {empleado.conceptos.map((concepto, idx) => (
                                    <div key={idx} className="p-3 bg-gray-800 rounded-lg border border-gray-600">
                                      <div className="flex justify-between items-start mb-2">
                                        <div className="text-sm font-medium text-white">
                                          {concepto.nombre}
                                        </div>
                                        <div className="text-sm font-bold text-teal-400">
                                          {formatearMonto(concepto.monto_total)}
                                        </div>
                                      </div>
                                      <div className="text-xs text-gray-400">
                                        Clasificación: {concepto.clasificacion?.replace('_', ' ') || 'No clasificado'}
                                      </div>
                                      {concepto.cantidad && (
                                        <div className="text-xs text-gray-400">
                                          Cantidad: {concepto.cantidad}
                                        </div>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LibroRemuneraciones;
