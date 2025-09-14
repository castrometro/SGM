import React, { useMemo, useState } from "react";
import IncidenciasAgregadasTable from "./IncidenciasAgregadasTable";

export default function IncidenciasTabs({ incidencias = [] }) {
  const [tab, setTab] = useState('empleado');

  const stats = useMemo(() => {
    const indiv = incidencias.filter(i => i.tipo_comparacion === 'individual');
    const suma = incidencias.filter(i => i.tipo_comparacion === 'suma_total');
    const total = incidencias.length;
    return { total, indiv: indiv.length, suma: suma.length };
  }, [incidencias]);

  const btnCls = (k) => `px-3 py-1 rounded text-sm ${tab === k ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-200 hover:bg-gray-600'}`;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between bg-gray-900/60 rounded-xl p-3 border border-gray-800">
        <div className="flex gap-2">
          <button className={btnCls('empleado')} onClick={() => setTab('empleado')}>Por empleado</button>
          <button className={btnCls('item')} onClick={() => setTab('item')}>Por ítem (agregado)</button>
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-400">
          <span>Total: <span className="text-gray-200 font-medium">{stats.total}</span></span>
          <span>Individual: <span className="text-gray-200 font-medium">{stats.indiv}</span></span>
          <span>Agregado: <span className="text-gray-200 font-medium">{stats.suma}</span></span>
        </div>
      </div>

      {tab === 'empleado' && (
        <div className="text-sm text-gray-400">
          Usa la lista de incidencias para filtrar por empleado/ítem y revisar variaciones puntuales.
        </div>
      )}

      {tab === 'item' && (
        <IncidenciasAgregadasTable incidencias={incidencias} />
      )}
    </div>
  );
}
