import { useState } from "react";
import { motion } from "framer-motion";
import { FiMail, FiLock, FiEye, FiEyeOff, FiAlertCircle, FiCheck, FiX } from "react-icons/fi";

/**
 * Componente de demostración de las mejoras del Login
 * Muestra lado a lado: Antes vs Después
 */
export default function LoginComparison() {
  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-center mb-12 text-gray-900">
          🎨 Mejoras del Login - Comparación
        </h1>

        {/* Comparación Visual */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          {/* ANTES */}
          <ComparisonCard
            title="❌ Antes"
            features={[
              { label: "Sin validación en tiempo real", status: "bad" },
              { label: "Alert() para errores", status: "bad" },
              { label: "Sin estados de loading", status: "bad" },
              { label: "No responsive en móvil", status: "bad" },
              { label: "Checkbox no funcional", status: "bad" },
              { label: "Sin iconos", status: "bad" },
              { label: "Sin toggle de contraseña", status: "bad" },
            ]}
            color="red"
          />

          {/* DESPUÉS */}
          <ComparisonCard
            title="✅ Después"
            features={[
              { label: "Validación en tiempo real", status: "good" },
              { label: "Errores visuales elegantes", status: "good" },
              { label: "Loading states animados", status: "good" },
              { label: "100% responsive", status: "good" },
              { label: "Checkbox funcional", status: "good" },
              { label: "Iconografía moderna", status: "good" },
              { label: "Toggle de contraseña", status: "good" },
            ]}
            color="green"
          />
        </div>

        {/* Mejoras por Categoría */}
        <div className="space-y-6">
          <CategoryCard
            icon="📱"
            title="Responsive Design"
            description="Mobile-first approach con breakpoints optimizados"
            improvements={[
              "Padding adaptativo: px-6 sm:px-10",
              "Texto escalable: text-3xl sm:text-4xl",
              "Formulario ocupa 90% en móvil, max-w-md en desktop",
              "Header compacto en móvil (h-8) vs desktop (h-12)",
            ]}
          />

          <CategoryCard
            icon="✅"
            title="Validación de Formulario"
            description="Feedback instantáneo para mejor UX"
            improvements={[
              "Email: formato válido + dominio @bdo.cl",
              "Contraseña: mínimo 6 caracteres",
              "Errores solo después de onBlur o submit",
              "Iconos de alerta en campos inválidos",
            ]}
          />

          <CategoryCard
            icon="🎭"
            title="Estados Visuales"
            description="Loading, error y success states"
            improvements={[
              "Spinner animado durante login",
              "Deshabilitación de formulario en loading",
              "Mensajes de error específicos por código HTTP",
              "Verificación de sesión con pantalla de carga",
            ]}
          />

          <CategoryCard
            icon="🎨"
            title="Diseño Visual"
            description="Interfaz moderna y profesional"
            improvements={[
              "Background con gradientes animados (blob)",
              "Efectos glass con backdrop-blur",
              "Animaciones suaves con Framer Motion",
              "Paleta de colores BDO consistente",
            ]}
          />

          <CategoryCard
            icon="♿"
            title="Accesibilidad"
            description="Experiencia inclusiva para todos"
            improvements={[
              "Labels semánticos con iconos descriptivos",
              "autoComplete en inputs",
              "aria-label en elementos interactivos",
              "Navegación por teclado (Enter para submit)",
            ]}
          />

          <CategoryCard
            icon="🔧"
            title="Funcionalidad"
            description="Características nuevas implementadas"
            improvements={[
              "Toggle para mostrar/ocultar contraseña",
              "Checkbox 'Recordar sesión' funcional",
              "Gestión de refresh tokens",
              "Validación de sesión existente al cargar",
            ]}
          />
        </div>

        {/* Breakpoints */}
        <div className="mt-12 bg-white rounded-xl shadow-lg p-8">
          <h2 className="text-2xl font-bold mb-6 text-gray-900">
            📐 Breakpoints Responsive
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <BreakpointCard
              device="📱 Mobile"
              range="320px - 640px"
              changes={[
                "px-6, py-8",
                "text-3xl",
                "Logo h-8",
                "Stack vertical",
              ]}
            />
            <BreakpointCard
              device="📱 Tablet"
              range="640px - 1024px"
              changes={[
                "px-10, py-10",
                "text-4xl",
                "Logo h-10",
                "Inline elements",
              ]}
            />
            <BreakpointCard
              device="💻 Desktop"
              range="1024px+"
              changes={[
                "Full padding",
                "text-4xl",
                "Logo h-12",
                "Extra info visible",
              ]}
            />
          </div>
        </div>

        {/* Código Destacado */}
        <div className="mt-12 bg-gradient-to-br from-gray-900 to-gray-800 rounded-xl shadow-2xl p-8">
          <h2 className="text-2xl font-bold mb-6 text-white">
            💻 Código Destacado
          </h2>
          
          <div className="space-y-4">
            <CodeBlock
              title="Validación de Email"
              language="javascript"
              code={`const validateEmail = (email) => {
  if (!email) return "El correo es requerido";
  if (!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email)) 
    return "Formato inválido";
  if (!email.endsWith("@bdo.cl")) 
    return "Debe usar correo @bdo.cl";
  return "";
};`}
            />

            <CodeBlock
              title="Responsive Styling"
              language="jsx"
              code={`className="px-6 py-8 sm:px-10 sm:py-10 
  rounded-2xl sm:rounded-3xl 
  max-w-md w-full mx-4 sm:mx-auto"`}
            />

            <CodeBlock
              title="Error Handling"
              language="javascript"
              code={`if (error.response?.status === 401) {
  setError("Correo o contraseña incorrectos");
} else if (error.response?.status === 403) {
  setError("Acceso denegado");
} else if (!error.response) {
  setError("No se pudo conectar al servidor");
}`}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

// Componentes auxiliares
function ComparisonCard({ title, features, color }) {
  const bgColor = color === "red" ? "bg-red-50" : "bg-green-50";
  const borderColor = color === "red" ? "border-red-200" : "border-green-200";

  return (
    <div className={`${bgColor} ${borderColor} border-2 rounded-xl p-6 shadow-lg`}>
      <h2 className="text-2xl font-bold mb-4 text-gray-900">{title}</h2>
      <ul className="space-y-3">
        {features.map((feature, idx) => (
          <li key={idx} className="flex items-start gap-3">
            {feature.status === "good" ? (
              <FiCheck className="text-green-600 flex-shrink-0 mt-1" size={20} />
            ) : (
              <FiX className="text-red-600 flex-shrink-0 mt-1" size={20} />
            )}
            <span className="text-gray-700">{feature.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function CategoryCard({ icon, title, description, improvements }) {
  return (
    <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
      <div className="flex items-start gap-4 mb-4">
        <span className="text-4xl">{icon}</span>
        <div className="flex-1">
          <h3 className="text-xl font-bold text-gray-900">{title}</h3>
          <p className="text-gray-600 text-sm mt-1">{description}</p>
        </div>
      </div>
      <ul className="space-y-2 ml-14">
        {improvements.map((improvement, idx) => (
          <li key={idx} className="flex items-start gap-2 text-gray-700">
            <span className="text-blue-600 font-bold">•</span>
            <span className="text-sm">{improvement}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function BreakpointCard({ device, range, changes }) {
  return (
    <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg p-6 border border-blue-200">
      <h3 className="text-lg font-bold text-gray-900 mb-2">{device}</h3>
      <p className="text-sm text-gray-600 mb-4 font-mono">{range}</p>
      <ul className="space-y-2">
        {changes.map((change, idx) => (
          <li key={idx} className="text-sm text-gray-700 flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-blue-600 rounded-full"></span>
            {change}
          </li>
        ))}
      </ul>
    </div>
  );
}

function CodeBlock({ title, language, code }) {
  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      <div className="bg-gray-700 px-4 py-2 flex items-center justify-between">
        <span className="text-gray-300 text-sm font-medium">{title}</span>
        <span className="text-gray-400 text-xs font-mono">{language}</span>
      </div>
      <pre className="p-4 overflow-x-auto">
        <code className="text-green-400 text-sm font-mono whitespace-pre">
          {code}
        </code>
      </pre>
    </div>
  );
}
