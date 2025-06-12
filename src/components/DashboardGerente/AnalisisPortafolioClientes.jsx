import { useState, useEffect } from 'react';
import { obtenerAnalisisPortafolio } from '../../api/gerente';
import { formatMoney } from '../../utils/format';

const AnalisisPortafolioClientes = ({ areas }) => {
  const [analisis, setAnalisis] = useState(null);
  const [filtroSegmento, setFiltroSegmento] = useState('todos');
  const [vistaTipo, setVistaTipo] = useState('valor');

  useEffect(() => {
    cargarAnalisis();
  }, []);

  const cargarAnalisis = async () => {
    try {
      const data = await obtenerAnalisisPortafolio();
      setAnalisis(data);
    } catch (error) {
      console.error('Error cargando análisis:', error);
    }
  };

  if (!analisis) {
    return <div className="text-white">Cargando análisis de portafolio...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white">Análisis de Portafolio</h2>
        <div className="flex gap-4">
          <select
            value={filtroSegmento}
            onChange={(e) => setFiltroSegmento(e.target.value)}
            className="bg-gray-700 text-white p-2 rounded"
          >
            <option value="todos">Todos los segmentos</option>
            <option value="premium">Premium (&gt;$500K)</option>
            <option value="medio">Medio ($100K-$500K)</option>
            <option value="basico">Básico (&lt;$100K)</option>
          </select>
          
          <select
            value={vistaTipo}
            onChange={(e) => setVistaTipo(e.target.value)}
            className="bg-gray-700 text-white p-2 rounded"
          >
            <option value="valor">Por Valor</option>
            <option value="rentabilidad">Por Rentabilidad</option>
            <option value="riesgo">Por Riesgo</option>
            <option value="crecimiento">Por Crecimiento</option>
          </select>
        </div>
      </div>

      {/* Resumen Ejecutivo */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-white font-semibold mb-2">Valor Total Portafolio</h3>
          <p className="text-3xl font-bold text-green-500">
            {formatMoney(analisis.valor_total_portafolio)} CLP
          </p>
          <p className="text-sm text-gray-400">Facturación mensual</p>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-white font-semibold mb-2">Clientes Activos</h3>
          <p className="text-3xl font-bold text-blue-500">{analisis.total_clientes_activos}</p>
          <p className="text-sm text-gray-400">
            {analisis.crecimiento_clientes > 0 ? '+' : ''}{analisis.crecimiento_clientes}% vs mes anterior
          </p>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-white font-semibold mb-2">Rentabilidad Promedio</h3>
          <p className="text-3xl font-bold text-yellow-500">{analisis.rentabilidad_promedio}%</p>
          <p className="text-sm text-gray-400">Margen neto</p>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-white font-semibold mb-2">Riesgo Promedio</h3>
          <p className="text-3xl font-bold text-red-500">{analisis.riesgo_promedio}/10</p>
          <p className="text-sm text-gray-400">Score ponderado</p>
        </div>
      </div>

      {/* Matriz de Segmentación */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h3 className="text-xl font-semibold text-white mb-4">Matriz de Segmentación</h3>
        <MatrizSegmentacion analisis={analisis} vistaTipo={vistaTipo} />
      </div>

      {/* Top Clientes por Categoría */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TopClientes
          titulo="🏆 Top Clientes por Valor"
          clientes={analisis.top_clientes_valor}
          metrica="valor_mensual"
          formato="dinero"
        />
        
        <TopClientes
          titulo="📈 Top Clientes por Crecimiento"
          clientes={analisis.top_clientes_crecimiento}
          metrica="crecimiento_anual"
          formato="porcentaje"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TopClientes
          titulo="💰 Top Clientes por Rentabilidad"
          clientes={analisis.top_clientes_rentabilidad}
          metrica="rentabilidad"
          formato="porcentaje"
        />
        
        <TopClientes
          titulo="⚠️ Clientes de Alto Riesgo"
          clientes={analisis.clientes_alto_riesgo}
          metrica="score_riesgo"
          formato="score"
          esRiesgo={true}
        />
      </div>

      {/* Análisis de Concentración */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h3 className="text-xl font-semibold text-white mb-4">Análisis de Concentración</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <h4 className="font-semibold text-gray-300 mb-2">Por Industria</h4>
            <div className="space-y-2">
              {analisis.concentracion_industria?.map(item => (
                <div key={item.industria} className="flex justify-between">
                  <span className="text-white">{item.industria}</span>
                  <span className="text-gray-400">{item.porcentaje}%</span>
                </div>
              ))}
            </div>
          </div>
          
          <div>
            <h4 className="font-semibold text-gray-300 mb-2">Por Tamaño</h4>
            <div className="space-y-2">
              {analisis.concentracion_tamano?.map(item => (
                <div key={item.segmento} className="flex justify-between">
                  <span className="text-white">{item.segmento}</span>
                  <span className="text-gray-400">{item.porcentaje}%</span>
                </div>
              ))}
            </div>
          </div>
          
          <div>
            <h4 className="font-semibold text-gray-300 mb-2">Por Área de Servicio</h4>
            <div className="space-y-2">
              {analisis.concentracion_area?.map(item => (
                <div key={item.area} className="flex justify-between">
                  <span className="text-white">{item.area}</span>
                  <span className="text-gray-400">{item.porcentaje}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const MatrizSegmentacion = ({ analisis, vistaTipo }) => {
  const getColorScore = (valor, tipo) => {
    switch (tipo) {
      case 'valor':
        return valor > 500000 ? 'bg-green-600' : valor > 100000 ? 'bg-yellow-600' : 'bg-red-600';
      case 'rentabilidad':
        return valor > 30 ? 'bg-green-600' : valor > 15 ? 'bg-yellow-600' : 'bg-red-600';
      case 'riesgo':
        return valor < 3 ? 'bg-green-600' : valor < 6 ? 'bg-yellow-600' : 'bg-red-600';
      case 'crecimiento':
        return valor > 20 ? 'bg-green-600' : valor > 0 ? 'bg-yellow-600' : 'bg-red-600';
      default:
        return 'bg-gray-600';
    }
  };

  const getValorFormateado = (segmento, tipo) => {
    const valor = segmento[tipo];
    switch (tipo) {
      case 'valor':
        return formatMoney(valor);
      case 'rentabilidad':
      case 'crecimiento':
        return `${valor}%`;
      case 'riesgo':
        return `${valor}/10`;
      default:
        return valor;
    }
  };

  if (!analisis.matriz_segmentacion) {
    return <div className="text-gray-400">Cargando matriz de segmentación...</div>;
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {analisis.matriz_segmentacion.map((segmento, index) => (
        <div
          key={index}
          className={`p-4 rounded-lg text-white text-center transition-all hover:scale-105 ${getColorScore(
            segmento[vistaTipo],
            vistaTipo
          )}`}
        >
          <div className="font-semibold text-sm mb-1">{segmento.nombre}</div>
          <div className="text-xs opacity-75 mb-2">{segmento.clientes_count} clientes</div>
          <div className="text-lg font-bold">
            {getValorFormateado(segmento, vistaTipo)}
          </div>
          
          {/* Información adicional en hover */}
          <div className="mt-2 text-xs opacity-0 hover:opacity-100 transition-opacity">
            <div>Valor: {formatMoney(segmento.valor)}</div>
            <div>Rent: {segmento.rentabilidad}%</div>
            <div>Riesgo: {segmento.riesgo}/10</div>
            <div>Crec: {segmento.crecimiento}%</div>
          </div>
        </div>
      ))}
    </div>
  );
};

const TopClientes = ({ titulo, clientes, metrica, formato, esRiesgo = false }) => (
  <div className="bg-gray-800 p-6 rounded-lg">
    <h3 className="text-xl font-semibold text-white mb-4">{titulo}</h3>
    <div className="space-y-3">
      {clientes?.map((cliente, index) => (
        <div key={cliente.id} className="bg-gray-700 p-3 rounded-lg">
          <div className="flex justify-between items-center">
            <div>
              <div className="font-semibold text-white">
                #{index + 1} {cliente.nombre}
              </div>
              <div className="text-sm text-gray-400">{cliente.industria}</div>
            </div>
            <div className="text-right">
              <div className={`font-semibold ${
                esRiesgo ? 'text-red-400' : 'text-green-400'
              }`}>
                {formato === 'dinero' && formatMoney(cliente[metrica])}
                {formato === 'porcentaje' && `${cliente[metrica]}%`}
                {formato === 'score' && `${cliente[metrica]}/10`}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  </div>
);

export default AnalisisPortafolioClientes;
