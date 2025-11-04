import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import logo from '../assets/BDO_LOGO.png';

const Header_login = () => {
    return (
        <motion.header 
            initial={{ y: -100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="w-full bg-white/95 backdrop-blur-md shadow-lg px-4 sm:px-6 lg:px-8 py-3 sm:py-4 sticky top-0 z-50"
        >
            <div className="flex justify-between items-center">
                {/* Logo y Título */}
                <Link 
                    to="/" 
                    className="flex items-center gap-3 group"
                    aria-label="BDO Chile - Sistema de Gestión y Monitoreo"
                >
                    <img 
                        src={logo} 
                        alt="BDO Logo" 
                        className="h-8 sm:h-10 transition-transform group-hover:scale-105" 
                    />
                    <span className="hidden sm:block text-gray-900 font-semibold text-sm sm:text-base lg:text-lg">
                        Sistema de Gestión y Monitoreo SGM
                    </span>
                </Link>

                {/* Indicador de ambiente (desarrollo/producción) */}
                {process.env.NODE_ENV === 'development' && (
                    <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-yellow-100 text-yellow-800 rounded-full text-xs font-medium">
                        <span className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></span>
                        Desarrollo
                    </div>
                )}

                {/* Info adicional - solo desktop */}
                <div className="hidden lg:flex items-center gap-4 text-sm text-gray-600">
                    <a 
                        href="https://www.bdo.cl" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="hover:text-red-600 transition-colors font-medium"
                    >
                        Sitio Web
                    </a>
                    <span className="text-gray-300">|</span>
                    <a 
                        href="#" 
                        className="hover:text-red-600 transition-colors font-medium"
                    >
                        Soporte
                    </a>
                </div>
            </div>
        </motion.header>
    );
};

export default Header_login;
