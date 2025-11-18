import { Settings, Info, CheckCircle, AlertCircle } from "lucide-react";
import { STYLES_CONFIG } from "../constants/capturaConfig";

const CuentasGlobalesSection = ({ cuentasGlobales, setCuentasGlobales }) => {
  const { containers } = STYLES_CONFIG;

  const handleChange = (field, value) => {
    // Filtrar solo números y guiones
    const valorLimpio = value.replace(/[^\d-]/g, '');
    setCuentasGlobales((prev) => ({ ...prev, [field]: valorLimpio }));
  };

  // Validar formato de cuenta (solo números y guiones)
  const validarFormatoCuenta = (valor) => {
    if (!valor || !valor.trim()) return { valido: false, mensaje: '' };
    
    // Solo permitir números y guiones (sin espacios ni otros caracteres especiales)
    const soloNumerosYGuiones = /^[\d-]+$/.test(valor);
    
    if (!soloNumerosYGuiones) {
      return { 
        valido: false, 
        mensaje: 'Solo se permiten números y guiones' 
      };
    }
    
    return { valido: true, mensaje: '' };
  };

  const getValidacionEstilo = (campo) => {
    const valor = cuentasGlobales[campo];
    if (!valor || !valor.trim()) {
      return 'border-red-500';
    }
    
    const validacion = validarFormatoCuenta(valor);
    return validacion.valido ? 'border-purple-500' : 'border-red-500';
  };

  const renderValidacionIcono = (campo) => {
    const valor = cuentasGlobales[campo];
    if (!valor || !valor.trim()) return null;
    
    const validacion = validarFormatoCuenta(valor);
    if (validacion.valido) {
      return <CheckCircle className="w-4 h-4 text-purple-500" />;
    } else {
      return <AlertCircle className="w-4 h-4 text-red-500" />;
    }
  };

  return (
    <div className={containers.section}>
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <Settings className="w-5 h-5" />
  Cuentas Globales (obligatorias)
      </h2>

      {/* Mensaje informativo sobre formato de cuentas */}
      <div className="mb-4 p-3 bg-blue-900/20 border border-blue-500/30 rounded-lg">
        <div className="flex items-start gap-2">
          <Info className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-blue-300">
            <p className="font-medium mb-1">Formato permitido para cuentas:</p>
            <p className="text-xs">
              <strong>Solo se permiten números y guiones. No se aceptan espacios ni otros caracteres especiales.</strong>
            </p>
            <div className="mt-2 space-y-1 text-xs">
              <p className="text-purple-400">✓ Correcto: <code className="bg-gray-800 px-1 rounded">1191001</code> o <code className="bg-gray-800 px-1 rounded">1191-001</code></p>
              <p className="text-red-400">✗ Incorrecto: <code className="bg-gray-800 px-1 rounded">1191 001</code>, <code className="bg-gray-800 px-1 rounded">1191.001</code>, <code className="bg-gray-800 px-1 rounded">1191_001</code> o <code className="bg-gray-800 px-1 rounded">1191/001</code></p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm text-gray-300 mb-1">Cuenta IVA (1xxx)</label>
          <div className="relative">
            <input
              type="text"
              value={cuentasGlobales.cuentaIVA}
              onChange={(e) => handleChange('cuentaIVA', e.target.value)}
              placeholder="1191001 o 1191-001"
              className={`w-full bg-gray-700 border ${getValidacionEstilo('cuentaIVA')} text-white px-3 py-2 pr-10 rounded-lg focus:outline-none focus:border-purple-500`}
              required
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              {renderValidacionIcono('cuentaIVA')}
            </div>
          </div>
          {cuentasGlobales.cuentaIVA && !validarFormatoCuenta(cuentasGlobales.cuentaIVA).valido && (
            <p className="text-xs text-red-400 mt-1">
              {validarFormatoCuenta(cuentasGlobales.cuentaIVA).mensaje}
            </p>
          )}
        </div>

        <div>
          <label className="block text-sm text-gray-300 mb-1">Cuenta Gasto (5xxx)</label>
          <div className="relative">
            <input
              type="text"
              value={cuentasGlobales.cuentaGasto}
              onChange={(e) => handleChange('cuentaGasto', e.target.value)}
              placeholder="5111001 o 5111-001"
              className={`w-full bg-gray-700 border ${getValidacionEstilo('cuentaGasto')} text-white px-3 py-2 pr-10 rounded-lg focus:outline-none focus:border-purple-500`}
              required
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              {renderValidacionIcono('cuentaGasto')}
            </div>
          </div>
          {cuentasGlobales.cuentaGasto && !validarFormatoCuenta(cuentasGlobales.cuentaGasto).valido && (
            <p className="text-xs text-red-400 mt-1">
              {validarFormatoCuenta(cuentasGlobales.cuentaGasto).mensaje}
            </p>
          )}
        </div>

        <div>
          <label className="block text-sm text-gray-300 mb-1">Cuenta Proveedores (2xxx)</label>
          <div className="relative">
            <input
              type="text"
              value={cuentasGlobales.cuentaProveedores}
              onChange={(e) => handleChange('cuentaProveedores', e.target.value)}
              placeholder="2111001 o 2111-001"
              className={`w-full bg-gray-700 border ${getValidacionEstilo('cuentaProveedores')} text-white px-3 py-2 pr-10 rounded-lg focus:outline-none focus:border-purple-500`}
              required
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              {renderValidacionIcono('cuentaProveedores')}
            </div>
          </div>
          {cuentasGlobales.cuentaProveedores && !validarFormatoCuenta(cuentasGlobales.cuentaProveedores).valido && (
            <p className="text-xs text-red-400 mt-1">
              {validarFormatoCuenta(cuentasGlobales.cuentaProveedores).mensaje}
            </p>
          )}
        </div>
      </div>

  <p className="text-xs mt-3 ${(!cuentasGlobales.cuentaIVA||!cuentasGlobales.cuentaProveedores||!cuentasGlobales.cuentaGasto)?'text-red-400':'text-gray-400'}">Debes completar las tres cuentas antes de procesar.</p>
    </div>
  );
};

export default CuentasGlobalesSection;
