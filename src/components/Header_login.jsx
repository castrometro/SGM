import React from 'react';
import { Link } from 'react-router-dom';
import logo from '../assets/BDO_LOGO.png'; // Asegúrate de tener un logo en `src/assets/`

const Header_login = () => {
    return (
        <header className="w-full bg-white shadow-md px-8 py-4">
            <div className="container mx-auto flex justify-between items-center">
                {/* Logo */}
                <Link to="/">
                    <img src={logo} alt="BDO Logo" className="h-12" />
                </Link>

                {/* Menú (pendiente de definir opciones) */}
                {/* <nav className="hidden md:flex space-x-6">
                    <Link to="#" className="text-gray-700 hover:text-red-600">Servicios</Link>
                    <Link to="#" className="text-gray-700 hover:text-red-600">Industrias</Link>
                    <Link to="#" className="text-gray-700 hover:text-red-600">Publicaciones</Link>
                    <Link to="#" className="text-gray-700 hover:text-red-600">Acerca de BDO</Link>
                </nav> */}
            </div>
        </header>
    );
};

export default Header_login;
