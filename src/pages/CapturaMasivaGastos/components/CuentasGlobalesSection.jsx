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
  Cuentas Globales (obligatorias)
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm text-gray-300 mb-1">Cuenta IVA (1xxx)</label>
          <input
            type="text"
            value={cuentasGlobales.cuentaIVA}
            onChange={(e) => handleChange('cuentaIVA', e.target.value)}
            placeholder="1191001"
            className={`w-full bg-gray-700 border ${cuentasGlobales.cuentaIVA?.trim() ? 'border-gray-600' : 'border-red-500'} text-white px-3 py-2 rounded-lg focus:outline-none focus:border-emerald-500`}
            required
          />
        </div>

        <div>
          <label className="block text-sm text-gray-300 mb-1">Cuenta Gasto (5xxx)</label>
          <input
            type="text"
            value={cuentasGlobales.cuentaGasto}
            onChange={(e) => handleChange('cuentaGasto', e.target.value)}
            placeholder="5111001"
            className={`w-full bg-gray-700 border ${cuentasGlobales.cuentaGasto?.trim() ? 'border-gray-600' : 'border-red-500'} text-white px-3 py-2 rounded-lg focus:outline-none focus:border-emerald-500`}
            required
          />
        </div>

        <div>
          <label className="block text-sm text-gray-300 mb-1">Cuenta Proveedores (2xxx)</label>
          <input
            type="text"
            value={cuentasGlobales.cuentaProveedores}
            onChange={(e) => handleChange('cuentaProveedores', e.target.value)}
            placeholder="2111001"
            className={`w-full bg-gray-700 border ${cuentasGlobales.cuentaProveedores?.trim() ? 'border-gray-600' : 'border-red-500'} text-white px-3 py-2 rounded-lg focus:outline-none focus:border-emerald-500`}
            required
          />
        </div>
      </div>

  <p className="text-xs mt-3 ${(!cuentasGlobales.cuentaIVA||!cuentasGlobales.cuentaProveedores||!cuentasGlobales.cuentaGasto)?'text-red-400':'text-gray-400'}">Debes completar las tres cuentas antes de procesar.</p>
    </div>
  );
};

export default CuentasGlobalesSection;
