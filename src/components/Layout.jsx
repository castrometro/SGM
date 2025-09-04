import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Header from './Header';
import Footer from './Footer';

const Layout = () => {
    const location = useLocation();
    // Rutas que requieren layout a pantalla completa (sin container centrado)
    const fullWidthRe = /\/menu\/cierres-nomina\/[^/]+\/(libro-remuneraciones|movimientos)(\/)??$/;
    const isLibroRemuneraciones = fullWidthRe.test(location.pathname) && location.pathname.includes('libro-remuneraciones');
    const isMovimientosMes = fullWidthRe.test(location.pathname) && location.pathname.includes('movimientos');
    const mainClass = (isLibroRemuneraciones || isMovimientosMes)
        ? 'flex-grow w-full p-0'
        : 'flex-grow container mx-auto p-6';
    return (
        <div className="flex flex-col min-h-screen bg-gray-900 text-gray-100">
            {/* Fondo con gradiente y desenfoque */}
            <div className="fixed inset-0 z-0">
                <div className="absolute inset-0 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 opacity-80"></div>
                <div className="absolute inset-0 backdrop-blur-sm"></div>
            </div>

            {/* Contenedor principal */}
            <div className="relative z-10 flex flex-col min-h-screen">
                <Header />

                {/* Asegura que el contenido crezca para empujar el footer */}
                <main className={mainClass}>
                    <Outlet />
                </main>                <Footer />
            </div>
        </div>
    );
};

export default Layout;
