import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { obtenerMovimientosMes } from '../../api/nomina';
import { formatearMonedaChilena } from '../../utils/formatters';
import { 
  ArrowLeft, 
  Users, 
  UserPlus, 
  UserMinus,
  Calendar,
  Search,
  Filter,
  Download,
  AlertCircle,
  CheckCircle,
  Clock
} from 'lucide-react';

const MovimientosMes = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [datos, setDatos] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [filtros, setFiltros] = useState({
    busqueda: '',
    tipo: 'todos',
    fechaDesde: '',
    fechaHasta: ''
  });

  useEffect(() => {
    cargarDatos();
  }, [id]);

  const cargarDatos = async () => {
    try {
      setCargando(true);
      const respuesta = await obtenerMovimientosMes(id);
      setDatos(respuesta);
    } catch (error) {
      console.error('Error cargando movimientos del mes:', error);
      setError('Error al cargar los movimientos del mes');
    } finally {
      setCargando(false);
    }
  };

  const movimientosFiltrados = datos?.movimientos?.filter(movimiento => {
    const cumpleBusqueda = !filtros.busqueda || 
      movimiento.empleado.nombre.toLowerCase().includes(filtros.busqueda.toLowerCase()) ||
      movimiento.empleado.rut.includes(filtros.busqueda);
    
    const cumpleTipo = filtros.tipo === 'todos' || movimiento.tipo_movimiento === filtros.tipo;
    
    let cumpleFecha = true;
    if (filtros.fechaDesde && movimiento.fecha_movimiento) {
      cumpleFecha = cumpleFecha && new Date(movimiento.fecha_movimiento) >= new Date(filtros.fechaDesde);
    }
    if (filtros.fechaHasta && movimiento.fecha_movimiento) {
      cumpleFecha = cumpleFecha && new Date(movimiento.fecha_movimiento) <= new Date(filtros.fechaHasta);
    }
    
    return cumpleBusqueda && cumpleTipo && cumpleFecha;
  }) || [];

  const formatearMonto = (valor) => {
    return formatearMonedaChilena(valor);
  };

  const formatearFecha = (fecha) => {
    if (!fecha) return '-';
    return new Date(fecha).toLocaleDateString('es-CL');
  };

  const obtenerIconoTipo = (tipo) => {
    switch (tipo) {
      case 'ingreso':
        return <UserPlus className="w-5 h-5 text-green-500" />;
      case 'finiquito':
        return <UserMinus className="w-5 h-5 text-red-500" />;
      case 'ausentismo':
        return <Calendar className="w-5 h-5 text-yellow-500" />;
      case 'reincorporacion':
        return <CheckCircle className="w-5 h-5 text-blue-500" />;
      case 'cambio_datos':
        return <AlertCircle className="w-5 h-5 text-purple-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-500" />;
    }
  };

  const obtenerColorFondo = (tipo) => {
    switch (tipo) {
      case 'ingreso':
        return 'bg-green-900 border-green-700';
      case 'finiquito':
        return 'bg-red-900 border-red-700';
      case 'ausentismo':
        return 'bg-yellow-900 border-yellow-700';
      case 'reincorporacion':
        return 'bg-blue-900 border-blue-700';
      case 'cambio_datos':
        return 'bg-purple-900 border-purple-700';
      default:
        return 'bg-gray-800 border-gray-700';
    }
  };

  if (cargando) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500 mx-auto"></div>
          <p className="text-gray-400 mt-4">Cargando movimientos del mes...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="bg-red-600 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="text-white" size={24} />
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">Error al cargar</h3>
          <p className="text-gray-400 mb-4">{error}</p>
          <button
            onClick={() => navigate(-1)}
            className="bg-amber-600 hover:bg-amber-700 text-white px-4 py-2 rounded-lg transition-colors"
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
                <h1 className="text-2xl font-bold text-amber-400">Movimientos del Mes</h1>
                <p className="text-gray-400">
                  {datos?.cierre?.cliente} - {datos?.cierre?.periodo}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <button
                onClick={() => window.print()}
                className="bg-amber-600 hover:bg-amber-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
              >
                <Download size={16} />
                Exportar
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Resumen por tipo */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
          {Object.entries(datos?.resumen?.por_tipo || {}).map(([tipo, info]) => (
            <div key={tipo} className={`rounded-lg p-4 border ${obtenerColorFondo(tipo)}`}>
              <div className="flex items-center justify-between mb-2">
                {obtenerIconoTipo(tipo)}
                <span className="text-2xl font-bold text-white">{info.count}</span>
              </div>
              <p className="text-sm text-gray-300">{info.display}</p>
            </div>
          ))}
          
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <Users className="w-5 h-5 text-gray-400" />
              <span className="text-2xl font-bold text-white">{datos?.resumen?.total_movimientos || 0}</span>
            </div>
            <p className="text-sm text-gray-300">Total Movimientos</p>
          </div>
        </div>

        {/* Filtros */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
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
                  className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Tipo de Movimiento
              </label>
              <select
                value={filtros.tipo}
                onChange={(e) => setFiltros(prev => ({ ...prev, tipo: e.target.value }))}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-amber-500 focus:border-transparent"
              >
                <option value="todos">Todos</option>
                <option value="ingreso">Ingreso</option>
                <option value="finiquito">Finiquito</option>
                <option value="ausentismo">Ausentismo</option>
                <option value="reincorporacion">Reincorporación</option>
                <option value="cambio_datos">Cambio de Datos</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Fecha Desde
              </label>
              <input
                type="date"
                value={filtros.fechaDesde}
                onChange={(e) => setFiltros(prev => ({ ...prev, fechaDesde: e.target.value }))}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-amber-500 focus:border-transparent"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Fecha Hasta
              </label>
              <input
                type="date"
                value={filtros.fechaHasta}
                onChange={(e) => setFiltros(prev => ({ ...prev, fechaHasta: e.target.value }))}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-amber-500 focus:border-transparent"
              />
            </div>
            
            <div className="flex items-end justify-end">
              <p className="text-sm text-gray-400">
                {movimientosFiltrados.length} de {datos?.movimientos?.length || 0} movimientos
              </p>
            </div>
          </div>
        </div>

        {/* Lista de movimientos */}
        <div className="space-y-4">
          {movimientosFiltrados.map((movimiento) => (
            <div 
              key={movimiento.id} 
              className={`rounded-lg border p-6 ${obtenerColorFondo(movimiento.tipo_movimiento)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4 flex-1">
                  {obtenerIconoTipo(movimiento.tipo_movimiento)}
                  
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-white">
                        {movimiento.empleado.nombre}
                      </h3>
                      <span className="text-sm text-gray-400">
                        {movimiento.empleado.rut}
                      </span>
                      <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-gray-700 text-gray-300">
                        {movimiento.tipo_display}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-400">Cargo:</span>
                        <span className="ml-2 text-white">{movimiento.empleado.cargo || '-'}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Centro de Costo:</span>
                        <span className="ml-2 text-white">{movimiento.empleado.centro_costo || '-'}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Líquido a Pagar:</span>
                        <span className="ml-2 text-white font-medium">
                          {formatearMonto(movimiento.empleado.liquido_pagar)}
                        </span>
                      </div>
                    </div>
                    
                    {movimiento.motivo && (
                      <div className="mt-3">
                        <span className="text-gray-400">Motivo:</span>
                        <span className="ml-2 text-white">{movimiento.motivo}</span>
                      </div>
                    )}
                    
                    {movimiento.dias_ausencia && (
                      <div className="mt-2">
                        <span className="text-gray-400">Días de Ausencia:</span>
                        <span className="ml-2 text-white font-medium">{movimiento.dias_ausencia}</span>
                      </div>
                    )}
                    
                    {movimiento.observaciones && (
                      <div className="mt-3 p-3 bg-gray-700 rounded-lg">
                        <span className="text-gray-400 text-sm">Observaciones:</span>
                        <p className="text-white text-sm mt-1">{movimiento.observaciones}</p>
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="text-right text-sm text-gray-400 ml-4">
                  {movimiento.fecha_movimiento && (
                    <div className="mb-1">
                      <Calendar className="inline w-4 h-4 mr-1" />
                      {formatearFecha(movimiento.fecha_movimiento)}
                    </div>
                  )}
                  <div>
                    Detectado: {new Date(movimiento.fecha_deteccion).toLocaleDateString('es-CL')}
                  </div>
                  <div className="text-xs">
                    Por: {movimiento.detectado_por_sistema}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {movimientosFiltrados.length === 0 && (
            <div className="text-center py-12">
              <Users className="w-12 h-12 text-gray-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-400 mb-2">
                No se encontraron movimientos
              </h3>
              <p className="text-gray-500">
                {filtros.busqueda || filtros.tipo !== 'todos' || filtros.fechaDesde || filtros.fechaHasta
                  ? 'Intenta ajustar los filtros de búsqueda'
                  : 'No hay movimientos registrados para este periodo'
                }
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MovimientosMes;
