// src/modules/nomina/crear-cierre/components/ChecklistTareas.jsx
import { useState } from 'react';
import { MENSAJES } from '../constants/crearCierre.constants';

/**
 * Componente para gestionar el checklist de tareas del cierre
 */
const ChecklistTareas = ({ tareas, onTareasChange }) => {
  const handleAddTarea = () => {
    onTareasChange([...tareas, { descripcion: '' }]);
  };

  const handleRemoveTarea = (index) => {
    if (tareas.length === 1) return; // Mantener al menos una tarea
    onTareasChange(tareas.filter((_, i) => i !== index));
  };

  const handleChangeTarea = (index, value) => {
    const nuevasTareas = tareas.map((t, i) => 
      i === index ? { ...t, descripcion: value } : t
    );
    onTareasChange(nuevasTareas);
  };

  return (
    <div>
      <label className="block text-gray-300 font-semibold mb-1">
        {MENSAJES.TITULO_CHECKLIST}
      </label>
      
      <div className="space-y-2">
        {tareas.map((tarea, index) => (
          <div key={index} className="flex gap-2">
            <input
              type="text"
              className="flex-1 p-2 rounded bg-gray-900 text-white"
              placeholder={MENSAJES.PLACEHOLDER_TAREA}
              value={tarea.descripcion}
              onChange={(e) => handleChangeTarea(index, e.target.value)}
              required
            />
            <button
              type="button"
              onClick={() => handleRemoveTarea(index)}
              disabled={tareas.length === 1}
              className="px-2 text-red-400 hover:text-red-600 disabled:opacity-30"
              tabIndex={-1}
            >
              X
            </button>
          </div>
        ))}
        
        <button
          type="button"
          onClick={handleAddTarea}
          className="text-blue-400 mt-2"
        >
          {MENSAJES.AGREGAR_TAREA}
        </button>
      </div>
    </div>
  );
};

export default ChecklistTareas;
