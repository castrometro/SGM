import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { PlusCircle, List, CheckCircle } from "lucide-react";
import {
  obtenerCuentasPendientesPorSet,
  obtenerSetsClasificacion,
  obtenerOpcionesClasificacion,
  clasificarCuenta,
  crearSetClasificacion,
  crearOpcionClasificacion,
} from "../api/contabilidad";

const PaginaClasificacion = ({ clienteId: propClienteId }) => {
  const { clienteId: paramClienteId } = useParams();
  const clienteId = propClienteId || paramClienteId;

  const [sets, setSets] = useState([]);
  const [selectedSet, setSelectedSet] = useState(null);
  const [options, setOptions] = useState([]);
  const [unclassified, setUnclassified] = useState([]);
  const [selectedAccts, setSelectedAccts] = useState([]);
  const [selectedOpt, setSelectedOpt] = useState(null);

  const [newSetName, setNewSetName] = useState("");
  const [newOptValor, setNewOptValor] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState({ type: null, msg: "" });

  // Fetch sets on mount
  useEffect(() => {
    fetchSets();
    // eslint-disable-next-line
  }, [clienteId]);

  // Fetch options and cuentas pendientes when set changes
  useEffect(() => {
    if (selectedSet?.id) {
      fetchOptions(selectedSet.id);
      fetchUnclassified(selectedSet.id);
    } else {
      setOptions([]);
      setUnclassified([]);
      setSelectedAccts([]);
    }
    setSelectedOpt(null);
  }, [selectedSet?.id]); // <- dependemos del ID para robustez

  async function fetchSets() {
    setLoading(true);
    try {
      const data = await obtenerSetsClasificacion(clienteId);
      setSets(data);
      if (data.length > 0) setSelectedSet(data[0]);
      else setSelectedSet(null);
    } catch {
      setMensaje("Error cargando conjuntos de clasificación.");
    }
    setLoading(false);
  }

  async function fetchOptions(setId) {
    setLoading(true);
    try {
      const data = await obtenerOpcionesClasificacion(setId);
      setOptions(data);
    } catch {
      setMensaje("Error cargando opciones.");
    }
    setLoading(false);
  }

  async function fetchUnclassified(setId) {
    setLoading(true);
    try {
      const data = await obtenerCuentasPendientesPorSet(clienteId, setId);
      setUnclassified(Array.isArray(data.cuentas_faltantes) ? data.cuentas_faltantes : []);
    } catch {
      setUnclassified([]);
      setMensaje("Error cargando cuentas sin clasificar.");
    }
    setLoading(false);
  }

  async function handleCreateSet(e) {
    e.preventDefault();
    if (!newSetName) return;
    try {
      const s = await crearSetClasificacion(clienteId, { nombre: newSetName });
      const nuevosSets = [...sets, s];
      setSets(nuevosSets);
      // Busca el nuevo set por ID para evitar referencias problemáticas
      setSelectedSet(nuevosSets.find(_s => _s.id === s.id));
      setNewSetName("");
      setMensaje("Set creado correctamente.");
    } catch {
      setMensaje("Error creando set.");
    }
  }

  async function handleCreateOption(e) {
    e.preventDefault();
    if (!selectedSet || !newOptValor) return;
    try {
      const o = await crearOpcionClasificacion(selectedSet.id, { valor: newOptValor });
      setOptions((prev) => [...prev, o]);
      setNewOptValor("");
      setMensaje("Opción creada correctamente.");
    } catch {
      setMensaje("Error creando opción.");
    }
  }

  async function handleAssignBulk() {
    if (!selectedAccts.length || !selectedOpt || !selectedSet) return;
    try {
      await Promise.all(selectedAccts.map(
        acctId => clasificarCuenta(acctId, selectedSet.id, selectedOpt.id)
      ));
      setUnclassified((prev) => prev.filter((c) => !selectedAccts.includes(c.id)));
      setSelectedAccts([]);
      setSelectedOpt(null);
      setAlert({ type: "success", msg: "Cuentas clasificadas correctamente." });
      setTimeout(() => setAlert({ type: null, msg: "" }), 2000);
    } catch {
      setAlert({ type: "error", msg: "Error al clasificar cuentas." });
    }
  }

  return (
    <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6 bg-gray-900 text-white min-h-screen">
      {/* Panel de Sets */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Conjuntos de Clasificación</h2>
        <ul className="border border-gray-700 rounded p-2 max-h-64 overflow-auto bg-gray-800">
          {sets.map((s) => (
            <li
              key={s.id}
              className={`p-2 cursor-pointer rounded hover:bg-indigo-800 ${selectedSet?.id === s.id ? "bg-indigo-700" : ""}`}
              onClick={() => setSelectedSet(sets.find(_s => _s.id === s.id))}
            >
              <List size={16} className="inline mr-1" /> {s.nombre}
            </li>
          ))}
          {sets.length === 0 && <p className="text-sm text-gray-400">Sin conjuntos</p>}
        </ul>
        <form onSubmit={handleCreateSet} className="space-y-2">
          <input
            type="text"
            placeholder="Nombre del Set"
            value={newSetName}
            onChange={(e) => setNewSetName(e.target.value)}
            className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1 text-white"
            required
          />
          <button type="submit" className="flex items-center bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1 rounded">
            <PlusCircle size={16} className="mr-1" /> Nuevo Set
          </button>
        </form>
        {sets.length === 0 && (
          <div className="bg-yellow-900 text-yellow-200 p-3 rounded mt-2">
            Debes crear al menos un conjunto de clasificación antes de poder clasificar cuentas.
          </div>
        )}
      </div>

      {/* Panel de Cuentas Sin Clasificar */}
      {sets.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Cuentas Sin Clasificar</h2>
          {unclassified.length === 0 ? (
            <div className="bg-green-900 text-green-200 p-4 rounded-lg flex items-center justify-center text-lg font-semibold">
              <CheckCircle className="mr-2" /> ¡Todas clasificadas!
            </div>
          ) : (
            <ul className="border border-gray-700 rounded p-2 max-h-96 overflow-auto bg-gray-800">
              {unclassified.map((c) => (
                <li
                  key={c.id}
                  className={
                    `p-2 cursor-pointer rounded hover:bg-blue-900 ` +
                    (selectedAccts.includes(c.id) ? "bg-blue-800 font-semibold" : "")
                  }
                  onClick={() => {
                    setSelectedAccts((prev) =>
                      prev.includes(c.id)
                        ? prev.filter((id) => id !== c.id)
                        : [...prev, c.id]
                    );
                  }}
                >
                  <input
                    type="checkbox"
                    checked={selectedAccts.includes(c.id)}
                    readOnly
                    className="mr-2"
                  />
                  <span className="font-mono text-xs">{c.codigo}</span> — {c.nombre}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Panel de Opciones y Asignación */}
      {sets.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Opciones</h2>
          {selectedSet ? (
            <>
              <ul className="border border-gray-700 rounded p-2 max-h-48 overflow-auto bg-gray-800">
                {options.map((o) => (
                  <li
                    key={o.id}
                    className={`p-2 cursor-pointer rounded hover:bg-green-900 ${selectedOpt?.id === o.id ? "bg-green-800" : ""}`}
                    onClick={() => setSelectedOpt(o)}
                  >
                    {o.valor}
                  </li>
                ))}
                {options.length === 0 && <p className="text-sm text-gray-400">Sin opciones</p>}
              </ul>
              <form onSubmit={handleCreateOption} className="space-y-2">
                <input
                  type="text"
                  placeholder="Nueva opción"
                  value={newOptValor}
                  onChange={(e) => setNewOptValor(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1 text-white"
                  required
                />
                <button type="submit" className="flex items-center bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded">
                  <PlusCircle size={16} className="mr-1" /> Crear Opción
                </button>
              </form>
              <button
                onClick={handleAssignBulk}
                disabled={!selectedAccts.length || !selectedOpt}
                className="flex items-center bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded"
              >
                <CheckCircle size={16} className="mr-1" /> Asignar Clasificación a Seleccionadas
              </button>
            </>
          ) : (
            <p className="text-sm text-gray-400">Selecciona un conjunto primero</p>
          )}
          {alert.type && (
            <div className={`mt-2 text-${alert.type === "success" ? "green" : "red"}-400`}>
              {alert.msg}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PaginaClasificacion;
