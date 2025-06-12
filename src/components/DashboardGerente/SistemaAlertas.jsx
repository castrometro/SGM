import { useState, useEffect } from 'react';
import { obtenerAlertas, marcarAlertaLeida, configurarAlertas, obtenerConfiguracionAlertas } from '../../api/gerente';
import { formatDateTime } from '../../utils/format';

const SistemaAlertas = () => {
  const [alertasData, setAlertasData] = useState({ alertas: [], resumen: {} });
  const [configuracion, setConfiguracion] = useState({
    cierre_atrasado_dias: 3,
    sobrecarga_clientes: 12,
    sla_critico: 85,
    notificaciones_email: true,
    notificaciones_push: true
  });
  const [filtros, setFiltros] = useState({
    tipo: 'todas',
    prioridad: 'todas',
    no_leidas: false
  });
  const [mostrarConfiguracion, setMostrarConfiguracion] = useState(false);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    cargarDatos();
    
    // Polling cada 30 segundos para alertas en tiempo real
    const interval = setInterval(cargarAlertas, 30000);
    return () => clearInterval(interval);
  }, [filtros]);

  const cargarDatos = async () => {
    setCargando(true);
    await Promise.all([cargarAlertas(), cargarConfiguracion()]);
    setCargando(false);
  };

  const cargarAlertas = async () => {
    try {
      const params = {};
      if (filtros.tipo !== 'todas') params.tipo = filtros.tipo;
      if (filtros.prioridad !== 'todas') params.prioridad = filtros.prioridad;
      if (filtros.no_leidas) params.no_leidas = 'true';
      
      const data = await obtenerAlertas(params);
      setAlertasData(data);
    } catch (error) {
      console.error('Error cargando alertas:', error);
    }
  };

  const cargarConfiguracion = async () => {
    try {
      const config = await obtenerConfiguracionAlertas();
      setConfiguracion(prevConfig => ({ ...prevConfig, ...config }));
    } catch (error) {
      console.error('Error cargando configuración:', error);
    }
  };

  const manejarAlertaLeida = async (alertaId) => {
    try {
      await marcarAlertaLeida(alertaId);
      setAlertasData(prev => ({
        ...prev,
        alertas: prev.alertas.map(alerta => 
          alerta.id === alertaId ? { ...alerta, leida: true } : alerta
        )
      }));
    } catch (error) {
      console.error('Error marcando alerta como leída:', error);
    }
  };

  const guardarConfiguracion = async () => {
    try {
      await configurarAlertas(configuracion);
      setMostrarConfiguracion(false);
    } catch (error) {
      console.error('Error guardando configuración:', error);
    }
  };

  const getPrioridadColor = (prioridad) => {
    switch (prioridad) {
      case 'alta': return 'bg-red-600 text-white';
      case 'media': return 'bg-yellow-600 text-white';
      case 'baja': return 'bg-blue-600 text-white';
      default: return 'bg-gray-600 text-white';
    }
  };

  const getTipoIcon = (tipo) => {
    switch (tipo) {
      case 'cierre_atrasado': return '⏰';
      case 'sobrecarga_analista': return '⚠️';
      case 'nuevo_cliente': return '👤';
      case 'sla_critico': return '📊';
      case 'error_sistema': return '🔧';
      default: return '📢';
    }
  };

  if (cargando) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
        <span className="ml-2 text-white">Cargando alertas...</span>
      </div>
    );
  }

  const alertasNoLeidas = alertas.filter(alerta => !alerta.leida);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white">Centro de Alertas</h2>
          <p className="text-gray-400">
            {alertasNoLeidas.length} alertas no leídas de {alertas.length} totales
          </p>
        </div>
        
        <div className="flex gap-4">
          <select
            value={filtroTipo}
            onChange={(e) => setFiltroTipo(e.target.value)}
            className="bg-gray-700 text-white p-2 rounded"
          >
            <option value="todas">Todas las alertas</option>
            <option value="sla">SLA</option>
            <option value="cliente">Cliente</option>
            <option value="equipo">Equipo</option>
            <option value="sistema">Sistema</option>
            <option value="financiero">Financiero</option>
          </select>
          
          <button
            onClick={() => setMostrarConfiguracion(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
          >
            ⚙️ Configurar
          </button>
        </div>
      </div>

      {/* Resumen de Alertas por Tipo */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[
          { tipo: 'sla', label: 'SLA', color: 'red', icon: '⏰' },
          { tipo: 'cliente', label: 'Cliente', color: 'yellow', icon: '🏢' },
          { tipo: 'equipo', label: 'Equipo', color: 'blue', icon: '👥' },
          { tipo: 'sistema', label: 'Sistema', color: 'purple', icon: '⚙️' },
          { tipo: 'financiero', label: 'Financiero', color: 'green', icon: '💰' }
        ].map(categoria => {
          const count = alertas.filter(a => a.tipo === categoria.tipo && !a.leida).length;
          return (
            <div key={categoria.tipo} className="bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl">{categoria.icon}</div>
                  <div className="text-sm text-gray-400">{categoria.label}</div>
                </div>
                <div className={`text-2xl font-bold text-${categoria.color}-500`}>
                  {count}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Lista de Alertas */}
      <div className="bg-gray-800 rounded-lg">
        <div className="p-4 border-b border-gray-700">
          <h3 className="text-lg font-semibold text-white">Alertas Activas</h3>
        </div>
        
        <div className="divide-y divide-gray-700">
          {alertasFiltradas.length === 0 ? (
            <div className="p-8 text-center text-gray-400">
              No hay alertas para mostrar
            </div>
          ) : (
            alertasFiltradas.map(alerta => (
              <AlertaItem
                key={alerta.id}
                alerta={alerta}
                onMarcarLeida={manejarAlertaLeida}
              />
            ))
          )}
        </div>
      </div>

      {/* Modal de Configuración */}
      {mostrarConfiguracion && (
        <ConfiguracionAlertas
          configuracion={configuracion}
          onGuardar={async (nuevaConfig) => {
            await configurarAlertas(nuevaConfig);
            setConfiguracion(nuevaConfig);
            setMostrarConfiguracion(false);
          }}
          onCerrar={() => setMostrarConfiguracion(false)}
        />
      )}
    </div>
  );
};

const AlertaItem = ({ alerta, onMarcarLeida }) => {
  const getIconoTipo = (tipo) => {
    const iconos = {
      sla: '⏰',
      cliente: '🏢',
      equipo: '👥',
      sistema: '⚙️',
      financiero: '💰'
    };
    return iconos[tipo] || '🔔';
  };

  const getColorPrioridad = (prioridad) => {
    const colores = {
      critica: 'border-red-500 bg-red-900',
      alta: 'border-orange-500 bg-orange-900',
      media: 'border-yellow-500 bg-yellow-900',
      baja: 'border-blue-500 bg-blue-900'
    };
    return colores[prioridad] || 'border-gray-500 bg-gray-900';
  };

  return (
    <div className={`p-4 border-l-4 ${getColorPrioridad(alerta.prioridad)} ${
      !alerta.leida ? 'bg-gray-750' : 'bg-gray-800'
    }`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3">
          <div className="text-2xl">{getIconoTipo(alerta.tipo)}</div>
          
          <div>
            <div className="flex items-center gap-2">
              <h4 className="font-semibold text-white">{alerta.titulo}</h4>
              {!alerta.leida && (
                <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
              )}
            </div>
            
            <p className="text-gray-300 text-sm mt-1">{alerta.descripcion}</p>
            
            <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
              <span>Tipo: {alerta.tipo}</span>
              <span>Prioridad: {alerta.prioridad}</span>
              <span>{new Date(alerta.fecha_creacion).toLocaleString()}</span>
            </div>
            
            {alerta.acciones_sugeridas && (
              <div className="mt-3">
                <div className="text-sm font-semibold text-gray-300">Acciones sugeridas:</div>
                <ul className="text-sm text-gray-400 mt-1">
                  {alerta.acciones_sugeridas.map((accion, index) => (
                    <li key={index}>• {accion}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
        
        <div className="flex flex-col gap-2">
          {!alerta.leida && (
            <button
              onClick={() => onMarcarLeida(alerta.id)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
            >
              Marcar como leída
            </button>
          )}
          
          {alerta.enlace_accion && (
            <a
              href={alerta.enlace_accion}
              className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm text-center"
            >
              Ver detalles
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

const ConfiguracionAlertas = ({ configuracion, onGuardar, onCerrar }) => {
  const [config, setConfig] = useState(configuracion);

  const tiposAlerta = [
    { id: 'sla_vencimiento', label: 'Vencimientos de SLA', tipo: 'sla' },
    { id: 'cliente_inactivo', label: 'Clientes inactivos', tipo: 'cliente' },
    { id: 'sobrecarga_analista', label: 'Sobrecarga de analistas', tipo: 'equipo' },
    { id: 'error_sistema', label: 'Errores del sistema', tipo: 'sistema' },
    { id: 'meta_ingresos', label: 'Metas de ingresos', tipo: 'financiero' }
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 p-6 rounded-lg max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <h3 className="text-xl font-bold text-white mb-4">Configuración de Alertas</h3>
        
        <div className="space-y-4">
          {tiposAlerta.map(tipo => (
            <div key={tipo.id} className="bg-gray-700 p-4 rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <label className="text-white font-semibold">{tipo.label}</label>
                <input
                  type="checkbox"
                  checked={config[tipo.id]?.activo || false}
                  onChange={(e) => setConfig({
                    ...config,
                    [tipo.id]: { ...config[tipo.id], activo: e.target.checked }
                  })}
                  className="w-4 h-4"
                />
              </div>
              
              {config[tipo.id]?.activo && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-gray-300 text-sm mb-1">
                      Umbral de activación
                    </label>
                    <input
                      type="number"
                      value={config[tipo.id]?.umbral || ''}
                      onChange={(e) => setConfig({
                        ...config,
                        [tipo.id]: { ...config[tipo.id], umbral: e.target.value }
                      })}
                      className="w-full p-2 bg-gray-600 text-white rounded"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-gray-300 text-sm mb-1">
                      Frecuencia de verificación
                    </label>
                    <select
                      value={config[tipo.id]?.frecuencia || 'diaria'}
                      onChange={(e) => setConfig({
                        ...config,
                        [tipo.id]: { ...config[tipo.id], frecuencia: e.target.value }
                      })}
                      className="w-full p-2 bg-gray-600 text-white rounded"
                    >
                      <option value="tiempo_real">Tiempo real</option>
                      <option value="cada_hora">Cada hora</option>
                      <option value="diaria">Diaria</option>
                      <option value="semanal">Semanal</option>
                    </select>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
        
        <div className="flex gap-4 pt-6">
          <button
            onClick={() => onGuardar(config)}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded"
          >
            Guardar Configuración
          </button>
          <button
            onClick={onCerrar}
            className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 rounded"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
};

export default SistemaAlertas;
