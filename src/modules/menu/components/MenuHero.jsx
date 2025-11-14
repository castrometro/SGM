// src/modules/menu/components/MenuHero.jsx
import PropTypes from 'prop-types';
import { USER_ROLES } from '../constants/menu.constants';
import './MenuAnimations.css';

const ROLE_COPY = {
  [USER_ROLES.ANALISTA]: 'Explora las herramientas y clientes asignados a tu cartera.',
  [USER_ROLES.SUPERVISOR]: 'Gestiona a tus analistas y valida los cierres pendientes.',
  [USER_ROLES.GERENTE]: 'Visualiza los tableros clave para tus áreas y equipos.',
};

const MenuHero = ({ usuario, totalOpciones }) => {
  const roleMessage = ROLE_COPY[usuario?.tipo_usuario] ?? 'Selecciona una opción para continuar.';
  const subtitle = totalOpciones
    ? `${totalOpciones} opciones disponibles`
    : 'Sin opciones disponibles por ahora.';

  return (
    <header className="space-y-2 animate-menu-fade-in">
      <h1 className="text-3xl font-bold">Menú Principal</h1>
      <p className="text-gray-300 text-sm sm:text-base">{roleMessage}</p>
      <p className="text-xs uppercase tracking-wide text-gray-500">{subtitle}</p>
    </header>
  );
};

MenuHero.propTypes = {
  usuario: PropTypes.shape({
    tipo_usuario: PropTypes.string,
  }),
  totalOpciones: PropTypes.number,
};

MenuHero.defaultProps = {
  usuario: null,
  totalOpciones: 0,
};

export default MenuHero;
