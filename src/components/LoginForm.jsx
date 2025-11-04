import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FiMail, FiLock, FiEye, FiEyeOff, FiAlertCircle } from "react-icons/fi";

export default function LoginForm({ onLogin, isLoading = false, error = null }) {
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [recordar, setRecordar] = useState(false);
  const [errors, setErrors] = useState({ correo: "", password: "" });
  const [touched, setTouched] = useState({ correo: false, password: false });

  // Validación de email
  const validateEmail = (email) => {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email) return "El correo es requerido";
    if (!regex.test(email)) return "Formato de correo inválido";
    if (!email.endsWith("@bdo.cl")) return "Debe usar un correo @bdo.cl";
    return "";
  };

  // Validación de contraseña
  const validatePassword = (pass) => {
    if (!pass) return "La contraseña es requerida";
    if (pass.length < 6) return "Mínimo 6 caracteres";
    return "";
  };

  const handleEmailChange = (e) => {
    const value = e.target.value;
    setCorreo(value);
    if (touched.correo) {
      setErrors({ ...errors, correo: validateEmail(value) });
    }
  };

  const handlePasswordChange = (e) => {
    const value = e.target.value;
    setPassword(value);
    if (touched.password) {
      setErrors({ ...errors, password: validatePassword(value) });
    }
  };

  const handleBlur = (field) => {
    setTouched({ ...touched, [field]: true });
    if (field === "correo") {
      setErrors({ ...errors, correo: validateEmail(correo) });
    } else if (field === "password") {
      setErrors({ ...errors, password: validatePassword(password) });
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validar todo antes de enviar
    const correoError = validateEmail(correo);
    const passwordError = validatePassword(password);
    
    setTouched({ correo: true, password: true });
    setErrors({ correo: correoError, password: passwordError });

    if (!correoError && !passwordError) {
      onLogin(correo, password, recordar);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleSubmit(e);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="bg-white/95 backdrop-blur-sm px-6 py-6 sm:px-8 sm:py-8 rounded-2xl sm:rounded-3xl border border-gray-200 shadow-2xl max-w-sm w-full mx-4 sm:mx-auto"
    >
      {/* Header */}
      <div className="text-center">
        <motion.h1 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-2xl sm:text-3xl font-bold text-gray-900"
        >
          Iniciar Sesión
        </motion.h1>
        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="text-gray-600 text-xs sm:text-sm mt-1"
        >
          Ingrese sus datos de cuenta BDO
        </motion.p>
      </div>

      {/* Error global */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2"
          >
            <FiAlertCircle className="text-red-600 flex-shrink-0 mt-0.5" size={18} />
            <div className="flex-1">
              <p className="text-xs text-red-800 font-medium">Error de autenticación</p>
              <p className="text-xs text-red-600 mt-0.5">{error}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Formulario */}
      <form onSubmit={handleSubmit} className="mt-4 sm:mt-5 space-y-4">
        {/* Campo Email */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
        >
          <label className="text-xs sm:text-sm font-medium text-gray-700 flex items-center gap-2">
            <FiMail className="text-gray-500" size={16} />
            Email Corporativo
          </label>
          <div className="relative mt-1.5">
            <input
              className={`w-full border-2 rounded-xl p-2.5 sm:p-3 pr-10 bg-white text-gray-900 placeholder-gray-400 
                focus:outline-none transition-colors text-sm
                ${errors.correo && touched.correo 
                  ? "border-red-400 focus:border-red-500" 
                  : "border-gray-300 focus:border-blue-500"
                }`}
              type="email"
              placeholder="nombre@bdo.cl"
              value={correo}
              onChange={handleEmailChange}
              onBlur={() => handleBlur("correo")}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              autoComplete="email"
            />
            {errors.correo && touched.correo && (
              <FiAlertCircle className="absolute right-3 top-1/2 transform -translate-y-1/2 text-red-500" size={18} />
            )}
          </div>
          <AnimatePresence>
            {errors.correo && touched.correo && (
              <motion.p
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="text-red-600 text-xs mt-1 flex items-center gap-1"
              >
                {errors.correo}
              </motion.p>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Campo Contraseña */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
        >
          <label className="text-xs sm:text-sm font-medium text-gray-700 flex items-center gap-2">
            <FiLock className="text-gray-500" size={16} />
            Contraseña
          </label>
          <div className="relative mt-1.5">
            <input
              className={`w-full border-2 rounded-xl p-2.5 sm:p-3 pr-12 bg-white text-gray-900 placeholder-gray-400 
                focus:outline-none transition-colors text-sm
                ${errors.password && touched.password 
                  ? "border-red-400 focus:border-red-500" 
                  : "border-gray-300 focus:border-blue-500"
                }`}
              type={showPassword ? "text" : "password"}
              placeholder="••••••••"
              value={password}
              onChange={handlePasswordChange}
              onBlur={() => handleBlur("password")}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              autoComplete="current-password"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700 focus:outline-none"
              tabIndex={-1}
            >
              {showPassword ? <FiEyeOff size={18} /> : <FiEye size={18} />}
            </button>
          </div>
          <AnimatePresence>
            {errors.password && touched.password && (
              <motion.p
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="text-red-600 text-xs mt-1"
              >
                {errors.password}
              </motion.p>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Recordar y Olvidó contraseña */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-0"
        >
          <div className="flex items-center">
            <input
              type="checkbox"
              id="remember"
              checked={recordar}
              onChange={(e) => setRecordar(e.target.checked)}
              className="w-3.5 h-3.5 text-red-600 focus:ring-2 focus:ring-red-500 border-gray-300 rounded cursor-pointer"
              disabled={isLoading}
            />
            <label htmlFor="remember" className="ml-2 text-gray-700 text-xs cursor-pointer select-none">
              Recordar mi sesión
            </label>
          </div>
          <button
            type="button"
            className="text-blue-600 hover:text-blue-700 hover:underline text-xs font-medium transition-colors text-left sm:text-right"
            disabled={isLoading}
          >
            ¿Olvidó su contraseña?
          </button>
        </motion.div>

        {/* Botón Submit */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="pt-1"
        >
          <button
            type="submit"
            disabled={isLoading || (touched.correo && errors.correo) || (touched.password && errors.password)}
            className={`w-full bg-gradient-to-r from-red-600 to-red-700 text-white text-sm sm:text-base font-semibold 
              py-2.5 sm:py-3 rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl
              focus:outline-none focus:ring-4 focus:ring-red-300
              disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-lg
              flex items-center justify-center gap-2
              ${isLoading ? "animate-pulse" : "hover:scale-[1.02] active:scale-[0.98]"}`}
          >
            {isLoading ? (
              <>
                <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Iniciando sesión...
              </>
            ) : (
              "Iniciar Sesión"
            )}
          </button>
        </motion.div>
      </form>

      {/* Footer info */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="mt-4 text-center"
      >
        <p className="text-xs text-gray-500">
          Al iniciar sesión, aceptas los{" "}
          <button className="text-blue-600 hover:underline font-medium">
            términos de uso
          </button>{" "}
          y la{" "}
          <button className="text-blue-600 hover:underline font-medium">
            política de privacidad
          </button>
        </p>
      </motion.div>
    </motion.div>
  );
}
// src/components/LoginForm.jsx