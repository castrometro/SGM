import { useState } from "react";
import { motion } from "framer-motion";

export default function LoginForm({ onLogin }) {
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = () => {
    onLogin(correo, password);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="bg-gray-100 px-10 py-10 rounded-3xl border-2 border-black max-w-md mx-auto shadow-lg"
    >
      <h1 className="text-4xl font-bold text-black text-center">Iniciar Sesión</h1>
      <p className="text-gray-500 text-center mt-2">Ingrese sus datos de cuenta BDO</p>

      <div className="mt-8 space-y-6">
        <div>
          <label className="text-lg font-medium text-black">Email</label>
          <input
            className="w-full border-2 border-gray-300 rounded-xl p-4 mt-1 bg-white text-black focus:outline-none focus:border-blue-500"
            type="email"
            placeholder="hola@bdo.cl"
            value={correo}
            onChange={(e) => setCorreo(e.target.value)}
          />
        </div>

        <div>
          <label className="text-lg font-medium text-black">Contraseña</label>
          <input
            className="w-full border-2 border-gray-300 rounded-xl p-4 mt-1 bg-white text-black focus:outline-none focus:border-blue-500"
            type="password"
            placeholder="Ingrese su contraseña"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="remember"
              className="w-4 h-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
            />
            <label htmlFor="remember" className="ml-2 text-black text-sm">
              Recordar
            </label>
          </div>
          <button className="text-blue-600 hover:underline text-sm">
            ¿Olvidó su contraseña?
          </button>
        </div>

        <div className="mt-4">
          <button
            className="w-full bg-red-600 text-white text-lg font-semibold py-3 rounded-xl hover:bg-red-700 transition-all"
            onClick={handleSubmit}
          >
            Iniciar Sesión
          </button>
        </div>
      </div>
    </motion.div>
  );
}
// src/components/LoginForm.jsx