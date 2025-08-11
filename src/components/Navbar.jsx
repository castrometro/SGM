// src/components/Navbar.jsx
import { Link } from 'react-router-dom';

const Navbar = () => {
    return (
        <nav className="bg-blue-600 text-white p-4 shadow-md">
            <div className="container mx-auto flex justify-between items-center">
                {/* Logo o Título */}
                <Link to="/" className="text-xl font-bold">
                    SGM Contabilidad
                </Link>

                {/* Menú de Navegación */}
                <div className="space-x-4">
                    <Link to="/" className="hover:underline">
                        Dashboard
                    </Link>
                    <Link to="/upload" className="hover:underline">
                        Cargar Novedades
                    </Link>
                    <Link to="/incidencias" className="hover:underline">
                        Incidencias
                    </Link>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
