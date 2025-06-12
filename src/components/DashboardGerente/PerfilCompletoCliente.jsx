import { useState, useEffect } from 'react';
import { obtenerPerfilCompletoCliente } from '../../api/gerente';
import { formatMoney } from '../../utils/format';

const PerfilCompletoCliente = ({ clienteId }) => {
  const [perfil, setPerfil] = useState(null);
  const [seccionActiva, setSeccionActiva] = useState('general');
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    cargarPerfil();
  }, [clienteId]);

  const cargarPerfil = async () => {
    try {
      const data = await obtenerPerfilCompletoCliente(clienteId);
      setPerfil(data);
    } catch (error) {
      console.error('Error cargando perfil:', error);
    }
    setCargando(false);
  };

  if (cargando) {
    return <div className="text-white">Cargando perfil del cliente...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header del Cliente */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">{perfil.nombre}</h1>
            <div className="flex items-center gap-4 text-gray-300">
              <span>RUT: {perfil.rut}</span>
              <span>•</span>
              <span>Industria: {perfil.industria?.nombre || 'No especificada'}</span>
              <span>•</span>
              <span className={`px-3 py-1 rounded-full text-sm ${
                perfil.estado_general === 'activo' 
                  ? 'bg-green-600 text-white'
                  : 'bg-red-600 text-white'
              }`}>
                {perfil.estado_general}
              </span>
            </div>
          </div>
          
          <div className="text-right">
            <div className="text-2xl font-bold text-green-500">
              {formatMoney(perfil.valor_total_servicios)} CLP/mes
            </div>
            <div className="text-sm text-gray-400">Valor total servicios</div>
          </div>
        </div>
      </div>

      {/* Navegación de secciones */}
      <div className="flex space-x-1 bg-gray-800 p-1 rounded-lg">
        {[
          { id: 'general', label: 'Vista General', icon: '📊' },
          { id: 'servicios', label: 'Servicios & Facturación', icon: '💰' },
          { id: 'performance', label: 'Performance & SLA', icon: '📈' },
          { id: 'comunicaciones', label: 'Comunicaciones', icon: '📧' },
          { id: 'riesgos', label: 'Análisis de Riesgos', icon: '⚠️' },
          { id: 'oportunidades', label: 'Oportunidades', icon: '🎯' }
        ].map(seccion => (
          <button
            key={seccion.id}
            onClick={() => setSeccionActiva(seccion.id)}
            className={`flex-1 py-3 px-4 rounded-lg text-sm font-medium transition-all ${
              seccionActiva === seccion.id
                ? 'bg-blue-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            <span className="mr-2">{seccion.icon}</span>
            {seccion.label}
          </button>
        ))}
      </div>

      {/* Contenido por sección */}
      <div className="bg-gray-800 rounded-lg p-6">
        {seccionActiva === 'general' && <VistaGeneral perfil={perfil} />}
        {seccionActiva === 'servicios' && <ServiciosFacturacion perfil={perfil} />}
        {seccionActiva === 'performance' && <PerformanceSLA perfil={perfil} />}
        {seccionActiva === 'comunicaciones' && <Comunicaciones perfil={perfil} />}
        {seccionActiva === 'riesgos' && <AnalisisRiesgos perfil={perfil} />}
        {seccionActiva === 'oportunidades' && <Oportunidades perfil={perfil} />}
      </div>
    </div>
  );
};

const VistaGeneral = ({ perfil }) => (
  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
    {/* KPIs Principales */}
    <div className="lg:col-span-2">
      <h3 className="text-xl font-semibold text-white mb-4">Métricas Clave</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-700 p-4 rounded-lg">
          <div className="text-2xl font-bold text-blue-500">{perfil.cierres_completados}</div>
          <div className="text-sm text-gray-400">Cierres este año</div>
        </div>
        <div className="bg-gray-700 p-4 rounded-lg">
          <div className="text-2xl font-bold text-green-500">{perfil.tiempo_promedio_cierre}d</div>
          <div className="text-sm text-gray-400">Tiempo promedio</div>
        </div>
        <div className="bg-gray-700 p-4 rounded-lg">
          <div className="text-2xl font-bold text-yellow-500">{perfil.sla_cumplimiento}%</div>
          <div className="text-sm text-gray-400">SLA cumplido</div>
        </div>
        <div className="bg-gray-700 p-4 rounded-lg">
          <div className="text-2xl font-bold text-purple-500">{perfil.satisfaccion_score}/10</div>
          <div className="text-sm text-gray-400">Satisfacción</div>
        </div>
      </div>
    </div>

    {/* Analistas Asignados */}
    <div>
      <h3 className="text-xl font-semibold text-white mb-4">Equipo Asignado</h3>
      <div className="space-y-3">
        {perfil.analistas_asignados?.map(asignacion => (
          <div key={asignacion.id} className="bg-gray-700 p-3 rounded-lg">
            <div className="font-semibold text-white">{asignacion.analista_nombre}</div>
            <div className="text-sm text-gray-400">{asignacion.area}</div>
            <div className="text-xs text-gray-500">Desde: {asignacion.fecha_asignacion}</div>
          </div>
        ))}
      </div>
    </div>
  </div>
);

const ServiciosFacturacion = ({ perfil }) => (
  <div className="space-y-6">
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Servicios Contratados */}
      <div>
        <h3 className="text-xl font-semibold text-white mb-4">Servicios Activos</h3>
        <div className="space-y-3">
          {perfil.servicios_contratados?.map(servicio => (
            <div key={servicio.id} className="bg-gray-700 p-4 rounded-lg">
              <div className="flex justify-between items-start">
                <div>
                  <div className="font-semibold text-white">{servicio.nombre}</div>
                  <div className="text-sm text-gray-400">{servicio.area}</div>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-green-500">
                    {formatMoney(servicio.valor)} {servicio.moneda}
                  </div>
                  <div className="text-xs text-gray-400">mensual</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Historial de Facturación */}
      <div>
        <h3 className="text-xl font-semibold text-white mb-4">Facturación Reciente</h3>
        <div className="space-y-3">
          {perfil.historial_facturacion?.map(factura => (
            <div key={factura.id} className="bg-gray-700 p-4 rounded-lg">
              <div className="flex justify-between items-center">
                <div>
                  <div className="font-semibold text-white">{factura.periodo}</div>
                  <div className="text-sm text-gray-400">{factura.concepto}</div>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-white">
                    {formatMoney(factura.monto)} {factura.moneda}
                  </div>
                  <div className={`text-xs px-2 py-1 rounded ${
                    factura.estado === 'pagado' 
                      ? 'bg-green-600 text-white'
                      : 'bg-yellow-600 text-white'
                  }`}>
                    {factura.estado}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  </div>
);

const AnalisisRiesgos = ({ perfil }) => (
  <div className="space-y-6">
    <h3 className="text-xl font-semibold text-white mb-4">Análisis de Riesgos</h3>
    
    {/* Alertas Activas */}
    <div className="bg-red-900 border border-red-600 p-4 rounded-lg">
      <h4 className="font-semibold text-red-200 mb-3">🚨 Alertas Activas</h4>
      <div className="space-y-2">
        {perfil.alertas_riesgo?.map(alerta => (
          <div key={alerta.id} className="text-red-100 text-sm">
            • {alerta.descripcion} ({alerta.nivel})
          </div>
        ))}
      </div>
    </div>

    {/* Métricas de Riesgo */}
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="bg-gray-700 p-4 rounded-lg">
        <div className="text-2xl font-bold text-red-500">{perfil.retrasos_ultimos_6_meses}</div>
        <div className="text-sm text-gray-400">Retrasos últimos 6 meses</div>
      </div>
      <div className="bg-gray-700 p-4 rounded-lg">
        <div className="text-2xl font-bold text-yellow-500">{perfil.incidencias_abiertas}</div>
        <div className="text-sm text-gray-400">Incidencias abiertas</div>
      </div>
      <div className="bg-gray-700 p-4 rounded-lg">
        <div className="text-2xl font-bold text-orange-500">{perfil.score_riesgo}/100</div>
        <div className="text-sm text-gray-400">Score de riesgo</div>
      </div>
    </div>
  </div>
);

const Oportunidades = ({ perfil }) => (
  <div className="space-y-6">
    <h3 className="text-xl font-semibold text-white mb-4">Oportunidades de Mejora</h3>
    
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Oportunidades de Venta */}
      <div>
        <h4 className="font-semibold text-green-400 mb-3">💰 Oportunidades de Venta</h4>
        <div className="space-y-3">
          {perfil.oportunidades_venta?.map(oportunidad => (
            <div key={oportunidad.id} className="bg-green-900 p-3 rounded-lg">
              <div className="font-semibold text-green-200">{oportunidad.servicio}</div>
              <div className="text-sm text-green-300">
                Potencial: {formatMoney(oportunidad.valor_potencial)} CLP/mes
              </div>
              <div className="text-xs text-green-400">{oportunidad.justificacion}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Mejoras Operacionales */}
      <div>
        <h4 className="font-semibold text-blue-400 mb-3">⚡ Mejoras Operacionales</h4>
        <div className="space-y-3">
          {perfil.mejoras_operacionales?.map(mejora => (
            <div key={mejora.id} className="bg-blue-900 p-3 rounded-lg">
              <div className="font-semibold text-blue-200">{mejora.area}</div>
              <div className="text-sm text-blue-300">{mejora.descripcion}</div>
              <div className="text-xs text-blue-400">
                Impacto: {mejora.impacto} • Esfuerzo: {mejora.esfuerzo}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  </div>
);

export default PerfilCompletoCliente;
