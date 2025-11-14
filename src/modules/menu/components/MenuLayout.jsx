// src/modules/menu/components/MenuLayout.jsx
import PropTypes from 'prop-types';

const MenuLayout = ({ children }) => (
  <section className="text-white space-y-8" data-module="menu">
    {children}
  </section>
);

MenuLayout.propTypes = {
  children: PropTypes.node.isRequired,
};

export default MenuLayout;
