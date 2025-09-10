import React, { useState, useMemo } from 'react';

/*
 Componente comparador de conceptos/métricas.
 Props:
  - activeChartData: array de { name, value, ... }
  - selectedCard: string clave de métrica seleccionada o null
*/
export default function ComparadorMovimientos({ activeChartData = [], selectedCard }) {
  const [seleccion, setSeleccion] = useState([]); // nombres seleccionados para comparar

  const toggle = (name) => {
    setSeleccion(prev => prev.includes(name) ? prev.filter(n => n !== name) : [...prev, name]);
  };

  const datosSeleccionados = useMemo(() => {
    return activeChartData.filter(d => seleccion.includes(d.name));
  }, [activeChartData, seleccion]);

  const total = useMemo(() => datosSeleccionados.reduce((acc, d) => acc + (Number(d.value) || 0), 0), [datosSeleccionados]);

  return (
    <div className="flex flex-col h-full">
      <h3 className="text-sm font-semibold text-teal-400 mb-3">Comparador</h3>
      <p className="text-xs text-gray-400 mb-4">Selecciona elementos del gráfico (o lista) para comparar entre sí.</p>
      <div className="flex-1 overflow-y-auto space-y-2 pr-1">
        {activeChartData.length === 0 && (
          <p className="text-gray-500 text-sm">Sin datos</p>
        )}
        {activeChartData.map(item => {
          const activo = seleccion.includes(item.name);
          return (
            <button
              key={item.name}
              onClick={() => toggle(item.name)}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg border text-xs transition-colors ${activo ? 'bg-teal-600/20 border-teal-500 text-teal-200' : 'bg-gray-800/50 border-gray-700 text-gray-300 hover:border-gray-600'}`}
            >
              <span className="truncate text-left">{item.name}</span>
              <span className="font-mono ml-2">{item.value}</span>
            </button>
          );
        })}
      </div>
      <div className="mt-4 pt-3 border-t border-gray-800 text-xs text-gray-300 space-y-1">
        <div className="flex justify-between"><span>Seleccionados:</span><span className="font-semibold">{seleccion.length}</span></div>
        <div className="flex justify-between"><span>Total combinado:</span><span className="font-semibold">{total}</span></div>
        {selectedCard && (
          <div className="flex justify-between"><span>Métrica base:</span><span className="font-semibold">{selectedCard}</span></div>
        )}
        {seleccion.length > 1 && total > 0 && (
          <div className="pt-2 space-y-1">
            {datosSeleccionados.map(d => (
              <div key={d.name} className="flex justify-between text-[11px] text-gray-400">
                <span className="truncate mr-2">{d.name}</span>
                <span>{((Number(d.value)||0)/total*100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        )}
        <div className="pt-2 flex gap-2">
          <button onClick={() => setSeleccion([])} className="flex-1 px-2 py-1 rounded-md bg-gray-800 text-gray-300 text-xs border border-gray-700 hover:border-gray-600">Limpiar</button>
        </div>
      </div>
    </div>
  );
}
