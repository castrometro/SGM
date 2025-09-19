import { Settings } from "lucide-react";
import { STYLES_CONFIG } from "../config/capturaConfig";

const CuentasGlobalesSection = ({ cuentasGlobales, setCuentasGlobales }) => {
  const { containers } = STYLES_CONFIG;

  const handleChange = (field, value) => {
    setCuentasGlobales((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className={containers.section}>
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <Settings className="w-5 h-5" />
        Cuentas Globales (opcional por ahora)
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm text-gray-300 mb-1">Cuenta IVA (1xxx)</label>
          <input
            type="text"
            value={cuentasGlobales.cuentaIVA}
            onChange={(e) => handleChange('cuentaIVA', e.target.value)}
            placeholder="1191001"
            className="w-full bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded-lg focus:outline-none focus:border-emerald-500"
          />
        </div>

        <div>
          <label className="block text-sm text-gray-300 mb-1">Cuenta Gasto (5xxx)</label>
          <input
            type="text"
            value={cuentasGlobales.cuentaGasto}
            onChange={(e) => handleChange('cuentaGasto', e.target.value)}
            placeholder="5111001"
            className="w-full bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded-lg focus:outline-none focus:border-emerald-500"
          />
        </div>

        <div>
          <label className="block text-sm text-gray-300 mb-1">Cuenta Proveedores (2xxx)</label>
          <input
            type="text"
            value={cuentasGlobales.cuentaProveedores}
            onChange={(e) => handleChange('cuentaProveedores', e.target.value)}
            placeholder="2111001"
            className="w-full bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded-lg focus:outline-none focus:border-emerald-500"
          />
        </div>
      </div>

      <p className="text-xs text-gray-400 mt-3">Estos campos se usarán en fases siguientes del procesamiento. Hoy son sólo de referencia.</p>
    </div>
  );
};

export default CuentasGlobalesSection;
