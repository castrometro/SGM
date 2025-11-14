/**
 * DevModulesButton Component
 * 
 * Botón flotante para acceso rápido al showcase de módulos refactorizados.
 * Solo visible en modo desarrollo.
 * 
 * @module auth/components/DevModulesButton
 * @requires react
 * @requires react-router-dom
 * @requires framer-motion
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * Botón flotante de desarrollo con menú expandible
 * 
 * Features:
 * - Solo visible en NODE_ENV === 'development'
 * - Posición fija en esquina inferior derecha
 * - Menú expandible con animaciones
 * - Enlaces a showcase, demo y documentación
 * 
 * @component
 * @returns {JSX.Element|null} Botón flotante o null en producción
 * 
 * @example
 * // En Layout o componente principal
 * import DevModulesButton from './DevModulesButton';
 * 
 * function App() {
 *   return (
 *     <div>
 *       <MainContent />
 *       <DevModulesButton />
 *     </div>
 *   );
 * }
 */
const DevModulesButton = () => {
    const [isOpen, setIsOpen] = useState(false);

    // Solo mostrar en desarrollo
    if (import.meta.env.MODE !== 'development') {
        return null;
    }

    /**
     * Enlaces del menú de desarrollo
     */
    const menuItems = [
        {
            to: '/dev/modules',
            icon: '📦',
            label: 'Ver Módulos',
            description: 'Showcase completo'
        },
        {
            to: '/dev/modules/auth/demo',
            icon: '🔐',
            label: 'Demo Auth',
            description: 'Prueba en vivo'
        },
        {
            to: '/dev/modules/menu/demo',
            icon: '📋',
            label: 'Demo Menu',
            description: 'Prueba en vivo'
        },
        {
            to: '/dev/modules/docs',
            icon: '📚',
            label: 'Documentación',
            description: 'Docs integradas'
        }
    ];

    return (
        <div className="fixed bottom-6 right-6 z-50">
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 20 }}
                        className="absolute bottom-16 right-0 bg-white rounded-lg shadow-2xl border border-gray-200 overflow-hidden"
                        style={{ minWidth: '240px' }}
                    >
                        {/* Header del menú */}
                        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 px-4 py-3 text-white">
                            <div className="flex items-center gap-2">
                                <span className="text-xl">🧩</span>
                                <div>
                                    <h3 className="font-semibold text-sm">Módulos Dev</h3>
                                    <p className="text-xs opacity-90">Refactorización</p>
                                </div>
                            </div>
                        </div>

                        {/* Lista de enlaces */}
                        <div className="py-2">
                            {menuItems.map((item, index) => (
                                <Link
                                    key={index}
                                    to={item.to}
                                    onClick={() => setIsOpen(false)}
                                    className="flex items-start gap-3 px-4 py-3 hover:bg-purple-50 transition-colors"
                                >
                                    <span className="text-2xl">{item.icon}</span>
                                    <div className="flex-1">
                                        <div className="font-medium text-gray-900 text-sm">
                                            {item.label}
                                        </div>
                                        <div className="text-xs text-gray-500">
                                            {item.description}
                                        </div>
                                    </div>
                                </Link>
                            ))}
                        </div>

                        {/* Footer informativo */}
                        <div className="border-t border-gray-200 px-4 py-2 bg-gray-50">
                            <p className="text-xs text-gray-600 text-center">
                                🚀 Solo visible en desarrollo
                            </p>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Botón principal */}
            <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setIsOpen(!isOpen)}
                className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-full p-4 shadow-lg transition-all duration-200 flex items-center justify-center"
                title="Módulos de Desarrollo"
            >
                <motion.span
                    animate={{ rotate: isOpen ? 180 : 0 }}
                    transition={{ duration: 0.3 }}
                    className="text-2xl"
                >
                    {isOpen ? '✕' : '🧩'}
                </motion.span>
            </motion.button>

            {/* Badge de "DEV" */}
            <div className="absolute -top-2 -right-2 bg-yellow-400 text-yellow-900 text-xs font-bold px-2 py-1 rounded-full shadow-md">
                DEV
            </div>
        </div>
    );
};

export default DevModulesButton;
