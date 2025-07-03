import { useState, useEffect } from 'react';
import { X, Check, AlertTriangle, Clock, FileText, Plus, Edit2, Trash2, Save, XCircle, Settings, Database, FolderPlus, Globe, CheckSquare } from 'lucide-react';
import { 
  obtenerClasificacionesArchivo,
  registrarVistaClasificaciones,
  crearClasificacionArchivo,
  actualizarClasificacionArchivo,
  eliminarClasificacionArchivo,
  obtenerSetsCliente,
  crearSet,
  actualizarSet,
  eliminarSet,
  obtenerOpcionesSet,
  crearOpcion,
  actualizarOpcion,
  eliminarOpcion
} from '../api/contabilidad';

const ModalClasificacionRegistrosRaw = ({ isOpen, onClose, uploadId, clienteId, cliente, onDataChanged }) => {
  console.log('🏗️ Modal props recibidos:', { 
    isOpen, 
    uploadId, 
    clienteId, 
    clienteExiste: !!cliente,
    clienteBilingue: cliente?.bilingue,
    onDataChanged: !!onDataChanged 
  });
  const [registros, setRegistros] = useState([]);
  const [loading, setLoading] = useState(false);
  const [estadisticas, setEstadisticas] = useState({});
  
  // Estados para navegación de pestañas
  const [pestanaActiva, setPestanaActiva] = useState('registros'); // 'registros' | 'sets'
  
  // Estados para CRUD de registros
  const [editandoId, setEditandoId] = useState(null);
  const [registroEditando, setRegistroEditando] = useState(null);
  const [creandoNuevo, setCreandoNuevo] = useState(false);
  const [nuevoRegistro, setNuevoRegistro] = useState({
    numero_cuenta: '',
    clasificaciones: {}
  });
  
  // Estados para selección de sets y opciones en creación/edición
  const [setSeleccionado, setSetSeleccionado] = useState('');
  const [opcionSeleccionada, setOpcionSeleccionada] = useState('');

  // Estados para filtros de búsqueda
  const [filtros, setFiltros] = useState({
    busquedaCuenta: '',
    setsSeleccionados: [],
    soloSinClasificar: false,
    soloClasificados: false
  });

  // Estados para gestión de sets y opciones
  const [sets, setSets] = useState([]);
  const [loadingSets, setLoadingSets] = useState(false);
  const [editandoSet, setEditandoSet] = useState(null);
  const [creandoSet, setCreandoSet] = useState(false);
  const [nuevoSet, setNuevoSet] = useState('');
  const [setEditando, setSetEditando] = useState('');
  
  // Estados para opciones (con soporte bilingüe mejorado)
  const [editandoOpcion, setEditandoOpcion] = useState(null);
  const [creandoOpcionPara, setCreandoOpcionPara] = useState(null);
  
  // Estados para manejo de creación/edición bilingüe de opciones
  const [modoCreacionOpcion, setModoCreacionOpcion] = useState('es'); // 'es' | 'en' | 'ambos'
  const [nuevaOpcionBilingue, setNuevaOpcionBilingue] = useState({
    es: '',
    en: '',
    descripcion_es: '',
    descripcion_en: ''
  });
  const [opcionEditandoBilingue, setOpcionEditandoBilingue] = useState({
    es: '',
    en: '',
    descripcion_es: '',
    descripcion_en: ''
  });

  // Estados para manejo bilingüe
  const [idiomaMostrado, setIdiomaMostrado] = useState('es'); // Solo para cambiar la visualización
  const [idiomaPorSet, setIdiomaPorSet] = useState({}); // { setId: 'es' | 'en' }
  const [opcionesBilinguesPorSet, setOpcionesBilinguesPorSet] = useState({});

  // Estados para clasificación masiva
  const [modoClasificacionMasiva, setModoClasificacionMasiva] = useState(false);
  const [registrosSeleccionados, setRegistrosSeleccionados] = useState(new Set());
  const [setMasivo, setSetMasivo] = useState('');
  const [opcionMasiva, setOpcionMasiva] = useState('');

  useEffect(() => {
    console.log('🎯 useEffect ejecutado:', { 
      isOpen, 
      uploadId, 
      clienteId, 
      cliente: !!cliente,
      clienteBilingue: cliente?.bilingue,
      clienteCompleto: cliente ? { id: cliente.id, nombre: cliente.nombre, bilingue: cliente.bilingue } : null
    });
    
    if (isOpen && uploadId && clienteId) {
      console.log('✅ Condiciones cumplidas - iniciando carga');
      
      // Registrar que se abrió el modal manualmente
      registrarVistaClasificaciones(clienteId, uploadId)
        .then(() => {
          console.log('📋 Vista registrada - cargando datos');
          // Después de registrar, cargar los datos
          cargarRegistros();
          // Cargar sets también
          cargarSets();
        })
        .catch((err) => {
          console.error("Error al registrar vista del modal:", err);
          // Aunque falle el registro, cargar los datos igual
          console.log('📋 Error en registro - cargando datos de todos modos');
          cargarRegistros();
          cargarSets();
        });
    } else {
      console.log('❌ Condiciones no cumplidas para carga');
    }
  }, [isOpen, uploadId, clienteId]);

  const cargarRegistros = async () => {
    setLoading(true);
    try {
      const data = await obtenerClasificacionesArchivo(uploadId);
      setRegistros(data);
      calcularEstadisticas(data);
    } catch (error) {
      console.error("Error cargando registros:", error);
    } finally {
      setLoading(false);
    }
  };

  const cargarSets = async () => {
    setLoadingSets(true);
    try {
      console.log('🔄 Iniciando carga de sets con endpoints originales...');
      console.log('👤 Cliente info:', { 
        clienteExiste: !!cliente,
        bilingue: cliente?.bilingue,
        id: cliente?.id || clienteId,
        nombre: cliente?.nombre
      });
      
      if (!clienteId) {
        console.warn('⚠️ No hay clienteId disponible');
        setSets([]);
        setOpcionesBilinguesPorSet({});
        return;
      }
      
      // Usar endpoints originales - primero cargar sets
      const sets = await obtenerSetsCliente(clienteId);
      console.log('📦 Sets cargados:', sets);
      
      setSets(sets);
      
      // Cargar opciones para cada set
      const nuevasOpcionesBilingues = {};
      const nuevoIdiomaPorSet = {};
      
      for (const set of sets) {
        try {
          const opciones = await obtenerOpcionesSet(set.id);
          console.log(`📋 Opciones para set ${set.id} (${set.nombre}):`, opciones);
          
          // Organizar opciones por idioma usando los nuevos campos del serializer
          const opcionesEs = [];
          const opcionesEn = [];
          
          opciones.forEach(opcion => {
            // Agregar a ES si tiene contenido en español
            if (opcion.tiene_es && opcion.valor_es) {
              opcionesEs.push({
                id: opcion.id,
                valor: opcion.valor_es,
                descripcion: opcion.descripcion_es || '',
                set_clas_id: set.id
              });
            }
            
            // Agregar a EN si tiene contenido en inglés
            if (opcion.tiene_en && opcion.valor_en) {
              opcionesEn.push({
                id: opcion.id,
                valor: opcion.valor_en,
                descripcion: opcion.descripcion_en || '',
                set_clas_id: set.id
              });
            }
          });
          
          nuevasOpcionesBilingues[set.id] = {
            es: opcionesEs,
            en: opcionesEn
          };
          
          // Establecer idioma por set (siempre español por defecto)
          nuevoIdiomaPorSet[set.id] = 'es';
          
          console.log(`� Set ${set.id} (${set.nombre}):`, {
            opciones_es: opcionesEs.length,
            opciones_en: opcionesEn.length,
            es_bilingue: set.tiene_opciones_bilingues
          });
        } catch (opcionError) {
          console.error(`❌ Error cargando opciones para set ${set.id}:`, opcionError);
          nuevasOpcionesBilingues[set.id] = { es: [], en: [] };
          nuevoIdiomaPorSet[set.id] = 'es';
        }
      }
      
      setOpcionesBilinguesPorSet(nuevasOpcionesBilingues);
      setIdiomaPorSet(nuevoIdiomaPorSet);
      
      // Establecer idioma del cliente (usar lógica simple basada en la propiedad bilingue)
      const idiomaPreferido = 'es'; // Valor por defecto siempre español
      setIdiomaMostrado(idiomaPreferido);
      
      console.log('✅ Carga completada exitosamente');
      console.log('📊 Resumen:', {
        total_sets: sets.length,
        cliente_bilingue: cliente?.bilingue,
        idioma_preferido: idiomaPreferido
      });
      
    } catch (error) {
      console.error("❌ Error cargando sets con endpoints originales:", error);
      setSets([]);
      setOpcionesBilinguesPorSet({});
    } finally {
      setLoadingSets(false);
    }
  };

  const calcularEstadisticas = (data) => {
    const total = data.length;
    setEstadisticas({ total });
  };

  // Función para cambiar idioma globalmente (solo para clientes bilingües)
  const cambiarIdiomaGlobal = (nuevoIdioma) => {
    if (!cliente?.bilingue) return; // Solo permitir si el cliente es bilingüe
    
    console.log(`🌐 Cambiando idioma GLOBAL a ${nuevoIdioma}`);
    setIdiomaMostrado(nuevoIdioma);
    
    // Actualizar TODOS los sets al mismo idioma
    const nuevoIdiomaPorSet = {};
    sets.forEach(set => {
      nuevoIdiomaPorSet[set.id] = nuevoIdioma;
    });
    setIdiomaPorSet(nuevoIdiomaPorSet);
    
    // Log de confirmación
    console.log(`✅ Todos los sets (${sets.length}) cambiados a ${nuevoIdioma.toUpperCase()}`);
  };

  // Función para cambiar idioma de un set específico (solo frontend)
  const cambiarIdiomaSet = (setId, nuevoIdioma) => {
    if (!cliente?.bilingue) return; // Solo permitir si el cliente es bilingüe
    
    console.log(`🌐 Cambiando idioma del set ${setId} a ${nuevoIdioma}`);
    
    setIdiomaPorSet(prev => ({
      ...prev,
      [setId]: nuevoIdioma
    }));
    
    // Log para debug - mostrar qué opciones están disponibles
    const opcionesBilingues = opcionesBilinguesPorSet[setId];
    if (opcionesBilingues) {
      console.log(`  📋 Opciones ES: ${opcionesBilingues.es?.length || 0}`);
      console.log(`  📋 Opciones EN: ${opcionesBilingues.en?.length || 0}`);
      console.log(`  📋 Mostrando: ${opcionesBilingues[nuevoIdioma]?.length || 0} opciones`);
    }
  };

  // ==================== FUNCIONES DE FILTRADO ====================
  const obtenerSetsUnicos = () => {
    const setsEncontrados = new Set();
    registros.forEach(registro => {
      if (registro.clasificaciones) {
        Object.keys(registro.clasificaciones).forEach(setNombre => {
          setsEncontrados.add(setNombre);
        });
      }
    });
    return Array.from(setsEncontrados).sort();
  };

  const aplicarFiltros = (registros) => {
    let registrosFiltrados = [...registros];

    // Filtro por búsqueda de cuenta
    if (filtros.busquedaCuenta.trim()) {
      const busqueda = filtros.busquedaCuenta.toLowerCase();
      registrosFiltrados = registrosFiltrados.filter(registro =>
        registro.numero_cuenta.toLowerCase().includes(busqueda)
      );
    }

    // Filtro por sets seleccionados
    if (filtros.setsSeleccionados.length > 0) {
      registrosFiltrados = registrosFiltrados.filter(registro => {
        if (!registro.clasificaciones) return false;
        const setsDelRegistro = Object.keys(registro.clasificaciones);
        return filtros.setsSeleccionados.some(setFiltro => 
          setsDelRegistro.includes(setFiltro)
        );
      });
    }

    // Filtro por estado de clasificación
    if (filtros.soloSinClasificar) {
      registrosFiltrados = registrosFiltrados.filter(registro =>
        !registro.clasificaciones || Object.keys(registro.clasificaciones).length === 0
      );
    } else if (filtros.soloClasificados) {
      registrosFiltrados = registrosFiltrados.filter(registro =>
        registro.clasificaciones && Object.keys(registro.clasificaciones).length > 0
      );
    }

    return registrosFiltrados;
  };

  const limpiarFiltros = () => {
    setFiltros({
      busquedaCuenta: '',
      setsSeleccionados: [],
      soloSinClasificar: false,
      soloClasificados: false
    });
  };

  // ==================== FUNCIONES AUXILIARES PARA SETS/OPCIONES ====================
  const obtenerSetsDisponibles = () => {
    return sets || [];
  };

  const obtenerOpcionesParaSet = (setId) => {
    if (!setId) return [];
    
    console.log(`🔍 Obteniendo opciones para set ${setId}`);
   
    const idioma = cliente?.bilingue ? (idiomaPorSet[setId] || 'es') : 'es';
    console.log(`  🌐 Idioma objetivo: ${idioma}, Cliente bilingüe: ${!!cliente?.bilingue}`);
    
    const opcionesBilingues = opcionesBilinguesPorSet[setId];
    
    if (!opcionesBilingues) {
      console.log(`  ⚠️ No hay opciones cargadas para set ${setId}`);
      return [];
    }
    
    const opciones = opcionesBilingues[idioma] || [];
    console.log(`  ✅ Devolviendo ${opciones.length} opciones en ${idioma.toUpperCase()}`);
    
    return opciones;
  };

  const agregarClasificacionARegistro = () => {
    if (!setSeleccionado || !opcionSeleccionada) {
      alert("Debe seleccionar un set y una opción");
      return;
    }

    const setEncontrado = sets.find(s => s.id === parseInt(setSeleccionado));
    if (!setEncontrado) {
      console.error('Set no encontrado:', setSeleccionado);
      return;
    }

    if (creandoNuevo) {
      setNuevoRegistro(prev => ({
        ...prev,
        clasificaciones: {
          ...prev.clasificaciones,
          [setEncontrado.nombre]: opcionSeleccionada
        }
      }));
    } else if (editandoId) {
      setRegistroEditando(prev => ({
        ...prev,
        clasificaciones: {
          ...prev.clasificaciones,
          [setEncontrado.nombre]: opcionSeleccionada
        }
      }));
    }

    // Limpiar selección
    setSetSeleccionado('');
    setOpcionSeleccionada('');
  };

  const eliminarClasificacionDeRegistro = (setNombre) => {
    if (creandoNuevo) {
      setNuevoRegistro(prev => {
        const nuevasClasificaciones = { ...prev.clasificaciones };
        delete nuevasClasificaciones[setNombre];
        return { ...prev, clasificaciones: nuevasClasificaciones };
      });
    } else if (editandoId) {
      setRegistroEditando(prev => {
        const nuevasClasificaciones = { ...prev.clasificaciones };
        delete nuevasClasificaciones[setNombre];
        return { ...prev, clasificaciones: nuevasClasificaciones };
      });
    }
  };

  const manejarCambioPestana = async (nuevaPestana) => {
    // Si ya está en esa pestaña, no hacer nada
    if (pestanaActiva === nuevaPestana) return;
    
    // TODO: Implementar registro de vista de sets si es necesario
    // Comentado temporalmente porque el endpoint no existe en el backend
    // if (nuevaPestana === 'sets') {
    //   try {
    //     await registrarVistaSetsClasificacion(clienteId);
    //   } catch (error) {
    //     console.error("Error al registrar vista de sets:", error);
    //   }
    // }
    
    setPestanaActiva(nuevaPestana);
  };

  // ==================== FUNCIONES CRUD PARA SETS ====================
  const handleCrearSet = async () => {
    if (!nuevoSet.trim()) {
      alert("El nombre del set es requerido");
      return;
    }
    try {
      await crearSet(clienteId, nuevoSet.trim());
      setNuevoSet('');
      setCreandoSet(false);
      await cargarSets();
    } catch (error) {
      console.error("Error creando set:", error);
      alert("Error al crear el set");
    }
  };

  const handleEditarSet = async () => {
    if (!setEditando.trim()) {
      alert("El nombre del set es requerido");
      return;
    }
    try {
      await actualizarSet(editandoSet, setEditando.trim());
      setEditandoSet(null);
      setSetEditando('');
      await cargarSets();
    } catch (error) {
      console.error("Error editando set:", error);
      alert("Error al editar el set");
    }
  };

  const handleEliminarSet = async (setId) => {
    if (window.confirm("¿Estás seguro de eliminar este set? Se eliminarán también todas sus opciones.")) {
      try {
        await eliminarSet(setId);
        await cargarSets();
      } catch (error) {
        console.error("Error eliminando set:", error);
        alert("Error al eliminar el set");
      }
    }
  };

  // ==================== FUNCIONES CRUD PARA OPCIONES ====================
  const handleCrearOpcion = async (setId) => {
    if (modoCreacionOpcion === 'ambos') {
      // Validar que ambos idiomas tengan valor
      if (!nuevaOpcionBilingue.es.trim() || !nuevaOpcionBilingue.en.trim()) {
        alert("Para crear una opción bilingüe, debe proporcionar el valor en ambos idiomas");
        return;
      }
      
      try {
        await crearOpcion(setId, {
          valor: nuevaOpcionBilingue.es.trim(),
          valor_en: nuevaOpcionBilingue.en.trim(),
          descripcion: nuevaOpcionBilingue.descripcion_es.trim(),
          descripcion_en: nuevaOpcionBilingue.descripcion_en.trim(),
        });
        
        setNuevaOpcionBilingue({ es: '', en: '', descripcion_es: '', descripcion_en: '' });
        setCreandoOpcionPara(null);
        await cargarSets();
      } catch (error) {
        console.error("Error creando opción bilingüe:", error);
        alert("Error al crear la opción bilingüe");
      }
    } else {
      // Crear solo en un idioma
      const valor = modoCreacionOpcion === 'es' ? nuevaOpcionBilingue.es : nuevaOpcionBilingue.en;
      const descripcion = modoCreacionOpcion === 'es' ? nuevaOpcionBilingue.descripcion_es : nuevaOpcionBilingue.descripcion_en;
      
      if (!valor.trim()) {
        alert("El valor de la opción es requerido");
        return;
      }
      
      try {
        const datos = {};
        
        if (modoCreacionOpcion === 'es') {
          datos.valor = valor.trim();
          if (descripcion.trim()) datos.descripcion = descripcion.trim();
        } else {
          datos.valor_en = valor.trim();
          if (descripcion.trim()) datos.descripcion_en = descripcion.trim();
        }
        
        await crearOpcion(setId, datos);
        setNuevaOpcionBilingue({ es: '', en: '', descripcion_es: '', descripcion_en: '' });
        setCreandoOpcionPara(null);
        await cargarSets();
      } catch (error) {
        console.error("Error creando opción:", error);
        alert("Error al crear la opción");
      }
    }
  };

  const handleEditarOpcion = async (opcionId, setId = null) => {
    // Determinar qué idioma estamos editando basado en el switch del set
    const idiomaActual = cliente?.bilingue ? (idiomaPorSet[setId] || 'es') : 'es';
    
    let valorAEditar;
    if (idiomaActual === 'es') {
      valorAEditar = opcionEditandoBilingue.es.trim();
    } else {
      valorAEditar = opcionEditandoBilingue.en.trim();
    }
    
    if (!valorAEditar) {
      alert(`El valor de la opción en ${idiomaActual.toUpperCase()} es requerido`);
      return;
    }
    
    try {
      // Si no se proporciona setId, intentar obtenerlo desde la opción
      let setClasId = setId;
      if (!setClasId) {
        // Buscar el set que contiene esta opción
        for (const set of sets) {
          const opciones = obtenerOpcionesParaSet(set.id);
          const opcionEncontrada = opciones.find(opcion => opcion.id === opcionId);
          if (opcionEncontrada) {
            setClasId = set.id;
            break;
          }
        }
      }
      
      // Preparar datos según el idioma que se está editando
      const datos = {};
      if (idiomaActual === 'es') {
        datos.valor = valorAEditar;
        if (opcionEditandoBilingue.descripcion_es.trim()) {
          datos.descripcion = opcionEditandoBilingue.descripcion_es.trim();
        }
      } else {
        datos.valor_en = valorAEditar;
        if (opcionEditandoBilingue.descripcion_en.trim()) {
          datos.descripcion_en = opcionEditandoBilingue.descripcion_en.trim();
        }
      }
      
      await actualizarOpcion(opcionId, datos, setClasId);
      setEditandoOpcion(null);
      setOpcionEditandoBilingue({ es: '', en: '', descripcion_es: '', descripcion_en: '' });
      await cargarSets();
    } catch (error) {
      console.error("Error editando opción:", error);
      console.error("Error response:", error.response?.data);
      
      // Mostrar error más específico
      let errorMessage = "Error al editar la opción";
      if (error.response?.data) {
        if (error.response.data.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.response.data.valor) {
          errorMessage = `Error en valor: ${error.response.data.valor.join(', ')}`;
        } else if (error.response.data.set_clas) {
          errorMessage = `Error en set: ${error.response.data.set_clas.join(', ')}`;
        } else if (typeof error.response.data === 'string') {
          errorMessage = error.response.data;
        } else {
          errorMessage = `Error del servidor: ${JSON.stringify(error.response.data)}`;
        }
      }
      
      alert(errorMessage);
    }
  };

  const handleEliminarOpcion = async (opcionId) => {
    if (window.confirm("¿Estás seguro de eliminar esta opción?")) {
      try {
        await eliminarOpcion(opcionId);
        await cargarSets();
      } catch (error) {
        console.error("Error eliminando opción:", error);
        alert("Error al eliminar la opción");
      }
    }
  };

  // ==================== FUNCIONES CRUD PARA REGISTROS ====================
  const handleIniciarCreacion = () => {
    setNuevoRegistro({
      numero_cuenta: '',
      clasificaciones: {}
    });
    setCreandoNuevo(true);
    // Limpiar selecciones
    setSetSeleccionado('');
    setOpcionSeleccionada('');
  };

  const handleCancelarCreacion = () => {
    setCreandoNuevo(false);
    setNuevoRegistro({ numero_cuenta: '', clasificaciones: {} });
    // Limpiar selecciones
    setSetSeleccionado('');
    setOpcionSeleccionada('');
  };

  const handleGuardarNuevo = async () => {
    if (!nuevoRegistro.numero_cuenta.trim()) {
      alert("El número de cuenta es requerido");
      return;
    }

    // Validar que el número de cuenta no exista ya en este upload
    const numeroCuentaExiste = registros.some(r => r.numero_cuenta === nuevoRegistro.numero_cuenta.trim());
    if (numeroCuentaExiste) {
      alert(`El número de cuenta "${nuevoRegistro.numero_cuenta}" ya existe en este archivo. Por favor usa un número diferente o edita el registro existente.`);
      return;
    }

    try {
      // Calcular la siguiente fila disponible basándose en las filas existentes
      const filasExistentes = registros.map(r => r.fila_excel || 0);
      const maxFila = filasExistentes.length > 0 ? Math.max(...filasExistentes) : 1;
      const siguienteFila = maxFila + 1;
      
      const datosAEnviar = {
        upload_log: uploadId,
        cliente: clienteId,
        numero_cuenta: nuevoRegistro.numero_cuenta.trim(),
        clasificaciones: nuevoRegistro.clasificaciones,
        fila_excel: siguienteFila
      };
      
      console.log('=== CREANDO NUEVO REGISTRO ===');
      console.log('Upload ID:', uploadId);
      console.log('Cliente ID:', clienteId);
      console.log('Datos completos a enviar:', JSON.stringify(datosAEnviar, null, 2));
      console.log('Tipo de clasificaciones:', typeof nuevoRegistro.clasificaciones);
      console.log('¿Clasificaciones es object?:', nuevoRegistro.clasificaciones && typeof nuevoRegistro.clasificaciones === 'object');

      await crearClasificacionArchivo(datosAEnviar);
      
      console.log('✅ Registro creado exitosamente');
      await cargarRegistros();
      handleCancelarCreacion();
      if (onDataChanged) onDataChanged();
    } catch (error) {
      console.error('❌ ERROR COMPLETO:', error);
      console.error('Error response:', error.response);
      console.error('Error response data:', error.response?.data);
      console.error('Error response status:', error.response?.status);
      console.error('Error response headers:', error.response?.headers);
      
      // Mostrar error más específico
      let errorMessage = "Error al crear el registro";
      if (error.response?.data) {
        console.log('Procesando error response data:', error.response.data);
        
        if (error.response.data.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.response.data.numero_cuenta) {
          errorMessage = `Error en número de cuenta: ${error.response.data.numero_cuenta.join(', ')}`;
        } else if (error.response.data.upload) {
          errorMessage = `Error en upload: ${error.response.data.upload.join(', ')}`;
        } else if (error.response.data.fila_excel) {
          errorMessage = `Error en fila excel: ${error.response.data.fila_excel.join(', ')}`;
        } else if (error.response.data.clasificaciones) {
          errorMessage = `Error en clasificaciones: ${error.response.data.clasificaciones.join(', ')}`;
        } else if (typeof error.response.data === 'string') {
          errorMessage = error.response.data;
        } else {
          errorMessage = `Error del servidor: ${JSON.stringify(error.response.data)}`;
        }
      }
      
      alert(errorMessage);
    }
  };

  const handleIniciarEdicion = (registro) => {
    setEditandoId(registro.id);
    setRegistroEditando({
      numero_cuenta: registro.numero_cuenta,
      clasificaciones: { ...registro.clasificaciones }
    });
    // Limpiar selecciones
    setSetSeleccionado('');
    setOpcionSeleccionada('');
  };

  const handleCancelarEdicion = () => {
    setEditandoId(null);
    setRegistroEditando(null);
    // Limpiar selecciones
    setSetSeleccionado('');
    setOpcionSeleccionada('');
  };

  const handleGuardarEdicion = async () => {
    if (!registroEditando.numero_cuenta.trim()) {
      alert("El número de cuenta es requerido");
      return;
    }

    try {
      await actualizarClasificacionArchivo(editandoId, registroEditando);
      await cargarRegistros();
      setEditandoId(null);
      setRegistroEditando(null);
      // Limpiar selecciones
      setSetSeleccionado('');
      setOpcionSeleccionada('');
      if (onDataChanged) onDataChanged();
    } catch (error) {
      console.error("Error al editar registro:", error);
      alert("Error al editar el registro");
    }
  };

  const handleEliminar = async (id) => {
    if (window.confirm("¿Estás seguro de que quieres eliminar este registro?")) {
      try {
        await eliminarClasificacionArchivo(id);
        await cargarRegistros();
        if (onDataChanged) onDataChanged();
      } catch (error) {
        console.error("Error al eliminar registro:", error);
        alert("Error al eliminar el registro");
      }
    }
  };

  // ==================== FUNCIONES PARA CLASIFICACIÓN MASIVA ====================
  const alternarModoClasificacionMasiva = () => {
    setModoClasificacionMasiva(!modoClasificacionMasiva);
    setRegistrosSeleccionados(new Set());
    setSetMasivo('');
    setOpcionMasiva('');
  };

  const alternarSeleccionRegistro = (registroId) => {
    const nuevosSeleccionados = new Set(registrosSeleccionados);
    if (nuevosSeleccionados.has(registroId)) {
      nuevosSeleccionados.delete(registroId);
    } else {
      nuevosSeleccionados.add(registroId);
    }
    setRegistrosSeleccionados(nuevosSeleccionados);
  };

  const seleccionarTodosLosRegistros = () => {
    const todosLosIds = new Set(registrosFiltrados.map(r => r.id));
    setRegistrosSeleccionados(todosLosIds);
  };

  const limpiarSeleccionRegistros = () => {
    setRegistrosSeleccionados(new Set());
  };

  const aplicarClasificacionMasiva = async () => {
    if (!setMasivo || !opcionMasiva) {
      alert("Debe seleccionar un set y una opción para la clasificación masiva");
      return;
    }

    if (registrosSeleccionados.size === 0) {
      alert("Debe seleccionar al menos un registro");
      return;
    }

    const setEncontrado = sets.find(s => s.id === parseInt(setMasivo));
    if (!setEncontrado) {
      console.error('Set no encontrado:', setMasivo);
      alert("Set no encontrado");
      return;
    }

    try {
      const promesas = Array.from(registrosSeleccionados).map(async (registroId) => {
        const registro = registros.find(r => r.id === registroId);
        if (!registro) return;

        const nuevasClasificaciones = {
          ...registro.clasificaciones,
          [setEncontrado.nombre]: opcionMasiva
        };

        return actualizarClasificacionArchivo(registroId, {
          numero_cuenta: registro.numero_cuenta,
          clasificaciones: nuevasClasificaciones
        });
      });

      await Promise.all(promesas);
      
      // Recargar datos y limpiar selección
      await cargarRegistros();
      setRegistrosSeleccionados(new Set());
      setSetMasivo('');
      setOpcionMasiva('');
      setModoClasificacionMasiva(false);
      
      if (onDataChanged) onDataChanged();
      
      alert(`Clasificación aplicada exitosamente a ${registrosSeleccionados.size} registros`);
    } catch (error) {
      console.error("Error aplicando clasificación masiva:", error);
      alert("Error al aplicar la clasificación masiva");
    }
  };

  const registrosFiltrados = aplicarFiltros(registros || []);
  const setsUnicos = obtenerSetsUnicos();

  if (!isOpen) {
    console.log("🚫 Modal no se abre - isOpen:", isOpen);
    return null;
  }

  console.log("✅ Modal se está abriendo");
  console.log("📋 Props recibidas:", { isOpen, uploadId, clienteId });

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex justify-center items-center p-4">
      <div 
        className="bg-gray-900 rounded-lg shadow-xl w-full overflow-hidden flex flex-col"
        style={{ 
          maxWidth: '95vw',
          height: '90vh',
          width: '1200px'
        }}
      >
        {/* Header del modal */}
        <div className="flex justify-between items-center p-6 border-b border-gray-700 bg-gray-900">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-semibold text-white flex items-center gap-2">
              <Database size={20} />
              Gestión de Clasificaciones
            </h2>
            
            {/* Switch global de idioma - Solo para clientes con sets bilingües */}
            {(() => {
              // Verificar si hay al menos un set con opciones bilingües
              const haySetsBilingues = cliente?.bilingue && sets.some(set => {
                const opcionesEs = opcionesBilinguesPorSet[set.id]?.es || [];
                const opcionesEn = opcionesBilinguesPorSet[set.id]?.en || [];
                return opcionesEs.length > 0 && opcionesEn.length > 0;
              });
              
              if (!haySetsBilingues) return null;
              
              return (
                <div className="flex items-center gap-2 bg-gray-800 rounded-lg p-2 border border-gray-600">
                  <Globe size={14} className="text-gray-400" />
                  <span className="text-xs text-gray-400">Todos los sets:</span>
                  <button
                    onClick={() => cambiarIdiomaGlobal('es')}
                    className={`px-3 py-1 rounded text-sm font-medium transition ${
                      idiomaMostrado === 'es'
                        ? 'bg-blue-600 text-white shadow-md'
                        : 'text-gray-300 hover:text-white hover:bg-gray-700'
                    }`}
                    title="Cambiar todos los sets a Español"
                  >
                    🇪🇸 ES
                  </button>
                  <button
                    onClick={() => cambiarIdiomaGlobal('en')}
                    className={`px-3 py-1 rounded text-sm font-medium transition ${
                      idiomaMostrado === 'en'
                        ? 'bg-blue-600 text-white shadow-md'
                        : 'text-gray-300 hover:text-white hover:bg-gray-700'
                    }`}
                    title="Cambiar todos los sets a Inglés"
                  >
                    🇺🇸 EN
                  </button>
                </div>
              );
            })()}
          </div>
          
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Pestañas de navegación */}
        <div className="bg-gray-800 border-b border-gray-700">
          <div className="flex space-x-4 p-4">
            <button
              onClick={() => manejarCambioPestana('registros')}
              className={`px-4 py-2 rounded font-medium transition-colors flex items-center gap-2 ${
                pestanaActiva === 'registros'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <FileText size={16} />
              Registros ({registros.length})
            </button>
            <button
              onClick={() => manejarCambioPestana('sets')}
              className={`px-4 py-2 rounded font-medium transition-colors flex items-center gap-2 ${
                pestanaActiva === 'sets'
                  ? 'bg-green-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Settings size={16} />
              Sets y Opciones ({sets.length})
            </button>
          </div>
        </div>

        {/* Contenido principal con scroll */}
        <div className="flex-1 overflow-auto bg-gray-900" style={{ minHeight: 0 }}>
          {/* Contenido de la pestaña Registros */}
          {pestanaActiva === 'registros' && (
            <div className="p-4">
              {/* Filtros y estadísticas */}
              <div className="bg-gray-800 p-4 rounded-lg mb-4 border border-gray-700">
                {/* Header con estadísticas y botón crear */}
                <div className="flex justify-between items-center mb-4">
                  <div className="flex items-center gap-4 text-sm text-gray-300">
                    <span>Total: <strong className="text-white">{registros.length}</strong></span>
                    <span>Filtrados: <strong className="text-blue-400">{registrosFiltrados.length}</strong></span>
                    {modoClasificacionMasiva && (
                      <span>Seleccionados: <strong className="text-green-400">{registrosSeleccionados.size}</strong></span>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={alternarModoClasificacionMasiva}
                      className={`px-4 py-2 rounded font-medium transition flex items-center gap-2 ${
                        modoClasificacionMasiva 
                          ? 'bg-red-600 hover:bg-red-500 text-white' 
                          : 'bg-green-600 hover:bg-green-500 text-white'
                      }`}
                    >
                      {modoClasificacionMasiva ? (
                        <>
                          <X size={16} />
                          Cancelar Masiva
                        </>
                      ) : (
                        <>
                          <CheckSquare size={16} />
                          Clasificación Masiva
                        </>
                      )}
                    </button>
                    <button
                      onClick={handleIniciarCreacion}
                      className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded font-medium transition flex items-center gap-2"
                      disabled={modoClasificacionMasiva}
                    >
                      <Plus size={16} />
                      Nuevo Registro
                    </button>
                  </div>
                </div>

                {/* Filtros */}
                <div className="border-t border-gray-700 pt-4">
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                    {/* Búsqueda por número de cuenta */}
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Buscar por cuenta:</label>
                      <div className="relative">
                        <input
                          type="text"
                          value={filtros.busquedaCuenta}
                          onChange={(e) => setFiltros(prev => ({ ...prev, busquedaCuenta: e.target.value }))}
                          onKeyDown={(e) => {
                            if (e.key === 'Escape') {
                              setFiltros(prev => ({ ...prev, busquedaCuenta: '' }));
                            }
                          }}
                          placeholder="Ej: 1-01-001... (Esc para limpiar)"
                          className="w-full bg-gray-700 text-white px-3 py-1 rounded border border-gray-600 text-sm focus:border-blue-500 focus:outline-none"
                        />
                        {filtros.busquedaCuenta && (
                          <button
                            onClick={() => setFiltros(prev => ({ ...prev, busquedaCuenta: '' }))}
                            className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
                          >
                            <XCircle size={14} />
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Filtros por estado */}
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Estado:</label>
                      <div className="flex gap-2">
                        <label className="flex items-center text-sm text-gray-300 hover:bg-gray-700 px-2 py-1 rounded cursor-pointer">
                          <input
                            type="checkbox"
                            checked={filtros.soloClasificados}
                            onChange={(e) => setFiltros(prev => ({ 
                              ...prev, 
                              soloClasificados: e.target.checked,
                              soloSinClasificar: e.target.checked ? false : prev.soloSinClasificar
                            }))}
                            className="mr-1 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
                          />
                          Con clasificaciones
                        </label>
                        <label className="flex items-center text-sm text-gray-300 hover:bg-gray-700 px-2 py-1 rounded cursor-pointer">
                          <input
                            type="checkbox"
                            checked={filtros.soloSinClasificar}
                            onChange={(e) => setFiltros(prev => ({ 
                              ...prev, 
                              soloSinClasificar: e.target.checked,
                              soloClasificados: e.target.checked ? false : prev.soloClasificados
                            }))}
                            className="mr-1 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
                          />
                          Sin clasificar
                        </label>
                      </div>
                    </div>

                    {/* Botón limpiar filtros y contador activos */}
                    <div className="flex items-end gap-2">
                      {(filtros.busquedaCuenta || filtros.setsSeleccionados.length > 0 || filtros.soloClasificados || filtros.soloSinClasificar) && (
                        <div className="text-xs text-blue-400 bg-blue-900/30 px-2 py-1 rounded">
                          {[
                            filtros.busquedaCuenta ? 'cuenta' : null,
                            filtros.setsSeleccionados.length > 0 ? `${filtros.setsSeleccionados.length} sets` : null,
                            filtros.soloClasificados ? 'clasificados' : null,
                            filtros.soloSinClasificar ? 'sin clasificar' : null
                          ].filter(Boolean).length} filtros activos
                        </div>
                      )}
                      <button
                        onClick={limpiarFiltros}
                        disabled={!filtros.busquedaCuenta && filtros.setsSeleccionados.length === 0 && !filtros.soloClasificados && !filtros.soloSinClasificar}
                        className="bg-gray-600 hover:bg-gray-500 disabled:bg-gray-700 disabled:text-gray-500 text-white px-3 py-1 rounded text-sm transition flex items-center gap-1"
                      >
                        <XCircle size={14} />
                        Limpiar filtros
                      </button>
                    </div>
                  </div>

                  {/* Filtros por sets */}
                  {setsUnicos.length > 0 && (
                    <div className="mt-4">
                      <div className="flex items-center gap-2 mb-2">
                        <label className="text-xs text-gray-400">Filtrar por sets:</label>
                        {filtros.setsSeleccionados.length > 0 && (
                          <button
                            onClick={() => setFiltros(prev => ({ ...prev, setsSeleccionados: [] }))}
                            className="text-xs text-blue-400 hover:text-blue-300 underline"
                          >
                            Deseleccionar todos
                          </button>
                        )}
                        {filtros.setsSeleccionados.length !== setsUnicos.length && (
                          <button
                            onClick={() => setFiltros(prev => ({ ...prev, setsSeleccionados: [...setsUnicos] }))}
                            className="text-xs text-blue-400 hover:text-blue-300 underline"
                          >
                            Seleccionar todos
                          </button>
                        )}
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {setsUnicos.map(setNombre => (
                          <label key={setNombre} className="flex items-center text-sm text-gray-300 bg-gray-700 hover:bg-gray-600 px-2 py-1 rounded cursor-pointer transition">
                            <input
                              type="checkbox"
                              checked={filtros.setsSeleccionados.includes(setNombre)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setFiltros(prev => ({
                                    ...prev,
                                    setsSeleccionados: [...prev.setsSeleccionados, setNombre]
                                  }));
                                } else {
                                  setFiltros(prev => ({
                                    ...prev,
                                    setsSeleccionados: prev.setsSeleccionados.filter(s => s !== setNombre)
                                  }));
                                }
                              }}
                              className="mr-2 text-blue-600 bg-gray-600 border-gray-500 rounded focus:ring-blue-500"
                            />
                            {setNombre}
                          </label>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Panel de clasificación masiva */}
              {modoClasificacionMasiva && (
                <div className="bg-gray-800 p-4 rounded-lg mb-4 border border-green-500/50">
                  <div className="flex items-center gap-2 mb-3">
                    <CheckSquare size={20} className="text-green-400" />
                    <h3 className="text-green-400 font-medium">Clasificación Masiva</h3>
                  </div>
                  
                  <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 items-end">
                    {/* Selector de Set */}
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Set:</label>
                      <select
                        value={setMasivo}
                        onChange={(e) => {
                          setSetMasivo(e.target.value);
                          setOpcionMasiva('');
                        }}
                        className="w-full bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 text-sm focus:border-green-500 focus:outline-none"
                      >
                        <option value="">Seleccionar set...</option>
                        {obtenerSetsDisponibles().map(set => (
                          <option key={set.id} value={set.id}>{set.nombre}</option>
                        ))}
                      </select>
                    </div>
                    
                    {/* Selector de Opción */}
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Opción:</label>
                      <select
                        value={opcionMasiva}
                        onChange={(e) => setOpcionMasiva(e.target.value)}
                        disabled={!setMasivo}
                        className="w-full bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 text-sm focus:border-green-500 focus:outline-none disabled:opacity-50"
                      >
                        <option value="">Seleccionar opción...</option>
                        {setMasivo && obtenerOpcionesParaSet(setMasivo).map(opcion => (
                          <option key={opcion.id} value={opcion.valor}>{opcion.valor}</option>
                        ))}
                      </select>
                    </div>
                    
                    {/* Controles de selección */}
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Selección:</label>
                      <div className="flex gap-2">
                        <button
                          onClick={seleccionarTodosLosRegistros}
                          className="bg-blue-600 hover:bg-blue-500 text-white px-3 py-2 rounded text-sm transition"
                          disabled={registrosFiltrados.length === 0}
                        >
                          Todos
                        </button>
                        <button
                          onClick={limpiarSeleccionRegistros}
                          className="bg-gray-600 hover:bg-gray-500 text-white px-3 py-2 rounded text-sm transition"
                          disabled={registrosSeleccionados.size === 0}
                        >
                          Limpiar
                        </button>
                      </div>
                    </div>
                    
                    {/* Botón aplicar */}
                    <div>
                      <button
                        onClick={aplicarClasificacionMasiva}
                        disabled={!setMasivo || !opcionMasiva || registrosSeleccionados.size === 0}
                        className="w-full bg-green-600 hover:bg-green-500 disabled:bg-gray-600 disabled:opacity-50 text-white px-4 py-2 rounded font-medium transition"
                      >
                        Aplicar ({registrosSeleccionados.size})
                      </button>
                    </div>
                  </div>
                  
                  {registrosSeleccionados.size > 0 && setMasivo && opcionMasiva && (
                    <div className="mt-3 p-3 bg-green-900/20 border border-green-700/50 rounded text-sm">
                      <span className="text-green-400">Vista previa:</span> Se aplicará la clasificación{' '}
                      <span className="font-medium text-white">
                        {obtenerSetsDisponibles().find(s => s.id === parseInt(setMasivo))?.nombre}: {opcionMasiva}
                      </span>{' '}
                      a <span className="font-medium text-green-400">{registrosSeleccionados.size}</span> registro(s).
                    </div>
                  )}
                </div>
              )}

              {/* Tabla */}
              <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
                {loading ? (
                  <div className="flex justify-center items-center h-32">
                    <div className="animate-spin w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full"></div>
                  </div>
                ) : registrosFiltrados.length === 0 ? (
                  <div className="text-center py-8 text-gray-400">
                    <FileText size={48} className="mx-auto mb-2 opacity-50" />
                    {registros.length === 0 ? (
                      <p>No hay registros de clasificación disponibles</p>
                    ) : (
                      <div>
                        <p className="mb-2">No hay registros que coincidan con los filtros aplicados</p>
                        {(filtros.busquedaCuenta || filtros.setsSeleccionados.length > 0 || filtros.soloClasificados || filtros.soloSinClasificar) && (
                          <div className="text-sm text-gray-500 mb-3">
                            Filtros activos: {[
                              filtros.busquedaCuenta ? `cuenta "${filtros.busquedaCuenta}"` : null,
                              filtros.setsSeleccionados.length > 0 ? `sets: ${filtros.setsSeleccionados.join(', ')}` : null,
                              filtros.soloClasificados ? 'solo clasificados' : null,
                              filtros.soloSinClasificar ? 'solo sin clasificar' : null
                            ].filter(Boolean).join(' • ')}
                          </div>
                        )}
                        <button
                          onClick={limpiarFiltros}
                          className="mt-2 text-blue-400 hover:text-blue-300 underline text-sm"
                        >
                          Limpiar filtros para ver todos los registros
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  <table className="w-full">
                    <thead className="bg-gray-800 sticky top-0 z-10">
                      <tr>
                        {modoClasificacionMasiva && (
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider border-b border-gray-700">
                            <input
                              type="checkbox"
                              checked={registrosFiltrados.length > 0 && registrosFiltrados.every(r => registrosSeleccionados.has(r.id))}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  seleccionarTodosLosRegistros();
                                } else {
                                  limpiarSeleccionRegistros();
                                }
                              }}
                              className="text-green-600 bg-gray-600 border-gray-500 rounded focus:ring-green-500"
                            />
                          </th>
                        )}
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider border-b border-gray-700">
                          Fila
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider border-b border-gray-700">
                          Número Cuenta
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider border-b border-gray-700">
                          Clasificaciones
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider border-b border-gray-700">
                          Acciones
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-gray-900 divide-y divide-gray-700">
                      {/* Fila de creación de nuevo registro */}
                      {creandoNuevo && (
                        <tr className="bg-gray-800 border-l-4 border-l-blue-500">
                          {modoClasificacionMasiva && (
                            <td className="px-3 py-2">
                              {/* Sin checkbox para fila de creación */}
                            </td>
                          )}
                          <td className="px-3 py-2 text-gray-400 text-sm">Nuevo</td>
                          <td className="px-3 py-2">
                            {(() => {
                              const cuentaExiste = nuevoRegistro.numero_cuenta.trim() && 
                                                 registros.some(r => r.numero_cuenta === nuevoRegistro.numero_cuenta.trim());
                              return (
                                <div>
                                  <input
                                    type="text"
                                    value={nuevoRegistro.numero_cuenta}
                                    onChange={(e) => setNuevoRegistro(prev => ({ ...prev, numero_cuenta: e.target.value }))}
                                    placeholder="Número de cuenta"
                                    className={`w-full bg-gray-700 text-white px-2 py-1 rounded border focus:outline-none ${
                                      cuentaExiste 
                                        ? 'border-red-500 focus:border-red-400' 
                                        : 'border-gray-600 focus:border-blue-500'
                                    }`}
                                  />
                                  {cuentaExiste && (
                                    <div className="text-red-400 text-xs mt-1">
                                      ⚠️ Esta cuenta ya existe en el archivo
                                    </div>
                                  )}
                                </div>
                              );
                            })()}
                          </td>
                          <td className="px-3 py-2">
                            {/* Clasificaciones agregadas */}
                            {Object.keys(nuevoRegistro.clasificaciones).length > 0 && (
                              <div className="mb-2">
                                <div className="flex flex-wrap gap-1">
                                  {Object.entries(nuevoRegistro.clasificaciones || {}).map(([set, valor]) => (
                                    <div key={set} className="flex items-center gap-1 bg-blue-900/50 px-2 py-1 rounded text-xs border border-blue-700/50">
                                      <span className="text-blue-300 font-medium">{set}:</span>
                                      <span className="text-white">{valor}</span>
                                      <button
                                        onClick={() => eliminarClasificacionDeRegistro(set)}
                                        className="text-red-400 hover:text-red-300 ml-1 hover:bg-red-900/30 rounded p-0.5 transition"
                                        title="Eliminar clasificación"
                                      >
                                        <XCircle size={12} />
                                      </button>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                            
                            {/* Selector de nueva clasificación */}
                            <div className="border-t border-gray-600 pt-2">
                              <div className="text-xs text-gray-400 mb-2">Agregar nueva clasificación:</div>
                              {obtenerSetsDisponibles().length === 0 ? (
                                <div className="text-xs text-yellow-400 bg-yellow-900/20 p-2 rounded border border-yellow-700/50">
                                  ⚠️ No hay sets disponibles.
                                </div>
                              ) : (
                                <div className="flex gap-2 items-center flex-wrap">
                                  <select
                                    value={setSeleccionado}
                                    onChange={(e) => {
                                      setSetSeleccionado(e.target.value);
                                      setOpcionSeleccionada('');
                                    }}
                                    className="bg-gray-800 text-white px-2 py-1 rounded border border-gray-600 text-xs focus:border-blue-500 focus:outline-none"
                                  >
                                    <option value="">🏷️ Set...</option>
                                    {obtenerSetsDisponibles().map(set => (
                                      <option key={set.id} value={set.id}>{set.nombre}</option>
                                    ))}
                                  </select>
                                  
                                  {setSeleccionado && obtenerOpcionesParaSet(setSeleccionado).length > 0 && (
                                    <select
                                      value={opcionSeleccionada}
                                      onChange={(e) => setOpcionSeleccionada(e.target.value)}
                                      className="bg-gray-800 text-white px-2 py-1 rounded border border-gray-600 text-xs focus:border-blue-500 focus:outline-none"
                                    >
                                      <option value="">📋 Opción...</option>
                                      {obtenerOpcionesParaSet(setSeleccionado).map(opcion => (
                                        <option key={opcion.id} value={opcion.valor}>{opcion.valor}</option>
                                      ))}
                                    </select>
                                  )}
                                  
                                  {setSeleccionado && opcionSeleccionada && (
                                    <button
                                      onClick={agregarClasificacionARegistro}
                                      className="bg-green-600 hover:bg-green-500 px-2 py-1 rounded text-white text-xs font-medium transition flex items-center gap-1"
                                      title="Agregar"
                                    >
                                      <Plus size={12} />
                                    </button>
                                  )}
                                </div>
                              )}
                            </div>
                          </td>
                          <td className="px-3 py-2">
                            <div className="flex gap-1">
                              <button
                                onClick={handleGuardarNuevo}
                                className="p-1 text-green-400 hover:text-green-300"
                                title="Guardar"
                              >
                                <Save size={16} />
                              </button>
                              <button
                                onClick={handleCancelarCreacion}
                                className="p-1 text-gray-400 hover:text-gray-300"
                                title="Cancelar"
                              >
                                <XCircle size={16} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      )}
                      
                      {/* Filas de registros existentes */}
                      {registrosFiltrados.map((registro) => (
                        <tr key={registro.id} className={`hover:bg-gray-800/50 transition-colors ${
                          modoClasificacionMasiva && registrosSeleccionados.has(registro.id) ? 'bg-green-900/20 border-l-4 border-l-green-500' : ''
                        }`}>
                          {modoClasificacionMasiva && (
                            <td className="px-3 py-2">
                              <input
                                type="checkbox"
                                checked={registrosSeleccionados.has(registro.id)}
                                onChange={() => alternarSeleccionRegistro(registro.id)}
                                className="text-green-600 bg-gray-600 border-gray-500 rounded focus:ring-green-500"
                              />
                            </td>
                          )}
                          <td className="px-3 py-2 text-gray-400 text-sm">{registro.fila_excel}</td>
                          <td className="px-3 py-2">
                            {editandoId === registro.id ? (
                              <input
                                type="text"
                                value={registroEditando.numero_cuenta}
                                onChange={(e) => setRegistroEditando(prev => ({ ...prev, numero_cuenta: e.target.value }))}
                                className="w-full bg-gray-700 text-white px-2 py-1 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                              />
                            ) : (
                              <span className="text-white font-mono">{registro.numero_cuenta}</span>
                            )}
                          </td>
                          <td className="px-3 py-2">
                            {editandoId === registro.id ? (
                              <div>
                                {/* Clasificaciones agregadas */}
                                {Object.keys(registroEditando.clasificaciones).length > 0 && (
                                  <div className="mb-2">
                                    <div className="flex flex-wrap gap-1">
                                      {Object.entries(registroEditando.clasificaciones || {}).map(([set, valor]) => (
                                        <div key={set} className="flex items-center gap-1 bg-blue-900/50 px-2 py-1 rounded text-xs border border-blue-700/50">
                                          <span className="text-blue-300 font-medium">{set}:</span>
                                          <span className="text-white">{valor}</span>
                                          <button
                                            onClick={() => eliminarClasificacionDeRegistro(set)}
                                            className="text-red-400 hover:text-red-300 ml-1 hover:bg-red-900/30 rounded p-0.5 transition"
                                            title="Eliminar clasificación"
                                          >
                                            <XCircle size={12} />
                                          </button>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                
                                {/* Selector de nueva clasificación */}
                                <div className="border-t border-gray-600 pt-2">
                                  <div className="text-xs text-gray-400 mb-2">Agregar nueva clasificación:</div>
                                  {obtenerSetsDisponibles().length === 0 ? (
                                    <div className="text-xs text-yellow-400 bg-yellow-900/20 p-2 rounded border border-yellow-700/50">
                                      ⚠️ No hay sets disponibles.
                                    </div>
                                  ) : (
                                    <div className="flex gap-2 items-center flex-wrap">
                                      <select
                                        value={setSeleccionado}
                                        onChange={(e) => {
                                          setSetSeleccionado(e.target.value);
                                          setOpcionSeleccionada('');
                                        }}
                                        className="bg-gray-800 text-white px-2 py-1 rounded border border-gray-600 text-xs focus:border-blue-500 focus:outline-none"
                                      >
                                        <option value="">🏷️ Set...</option>
                                        {obtenerSetsDisponibles().map(set => (
                                          <option key={set.id} value={set.id}>{set.nombre}</option>
                                        ))}
                                      </select>
                                      
                                      {setSeleccionado && obtenerOpcionesParaSet(setSeleccionado).length > 0 && (
                                        <select
                                          value={opcionSeleccionada}
                                          onChange={(e) => setOpcionSeleccionada(e.target.value)}
                                          className="bg-gray-800 text-white px-2 py-1 rounded border border-gray-600 text-xs focus:border-blue-500 focus:outline-none"
                                        >
                                          <option value="">📋 Opción...</option>
                                          {obtenerOpcionesParaSet(setSeleccionado).map(opcion => (
                                            <option key={opcion.id} value={opcion.valor}>{opcion.valor}</option>
                                          ))}
                                        </select>
                                      )}
                                      
                                      {setSeleccionado && opcionSeleccionada && (
                                        <button
                                          onClick={agregarClasificacionARegistro}
                                          className="bg-green-600 hover:bg-green-500 px-2 py-1 rounded text-white text-xs font-medium transition flex items-center gap-1"
                                          title="Agregar"
                                        >
                                          <Plus size={12} />
                                        </button>
                                      )}
                                    </div>
                                  )}
                                </div>
                              </div>
                            ) : (
                              <div className="flex flex-wrap gap-1">
                                {Object.entries(registro.clasificaciones || {}).map(([set, valor]) => (
                                  <span key={set} className="inline-block bg-blue-900/50 px-2 py-1 rounded text-xs">
                                    <span className="text-gray-300">{set}:</span> <span className="text-white">{valor}</span>
                                  </span>
                                ))}
                              </div>
                            )}
                          </td>
                          <td className="px-3 py-2">
                            {editandoId === registro.id ? (
                              <div className="flex gap-1">
                                <button
                                  onClick={handleGuardarEdicion}
                                  className="p-1 text-green-400 hover:text-green-300"
                                  title="Guardar"
                                >
                                  <Save size={16} />
                                </button>
                                <button
                                  onClick={handleCancelarEdicion}
                                  className="p-1 text-gray-400 hover:text-gray-300"
                                  title="Cancelar"
                                >
                                  <XCircle size={16} />
                                </button>
                              </div>
                            ) : (
                              <div className="flex gap-1">
                                <button
                                  onClick={() => handleIniciarEdicion(registro)}
                                  className="p-1 text-blue-400 hover:text-blue-300"
                                  title="Editar"
                                >
                                  <Edit2 size={16} />
                                </button>
                                <button
                                  onClick={() => handleEliminar(registro.id)}
                                  className="p-1 text-red-400 hover:text-red-300"
                                  title="Eliminar"
                                >
                                  <Trash2 size={16} />
                                </button>
                              </div>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}

          {/* Contenido de la pestaña Sets y Opciones */}
          {pestanaActiva === 'sets' && (
            <div className="p-4">
              {/* Header para crear nuevo set */}
              <div className="bg-gray-800 p-4 rounded-lg mb-4 border border-gray-700">
                <h3 className="text-lg font-medium text-white mb-3 flex items-center gap-2">
                  <FolderPlus size={18} />
                  Gestión de Sets de Clasificación
                </h3>
                
                {/* Ayuda para entender los switches */}
                {cliente?.bilingue && (
                  <div className="mb-4 p-3 bg-blue-900/20 border border-blue-700/50 rounded-lg">
                    <div className="flex items-center gap-2 text-blue-300 text-sm">
                      <Globe size={14} />
                      <span className="font-medium">Controles de idioma:</span>
                    </div>
                    <ul className="mt-2 text-xs text-blue-200 space-y-1">
                      <li>• <strong>Header del modal</strong>: Cambia TODOS los sets al mismo idioma</li>
                      <li>• <strong>Switch por set</strong>: Cambia solo ese set específico</li>
                      <li>• Los números muestran cuántas opciones hay en cada idioma</li>
                    </ul>
                  </div>
                )}
                
                <div className="flex gap-2 items-center">
                  {creandoSet ? (
                    <>
                      <input
                        type="text"
                        value={nuevoSet}
                        onChange={(e) => setNuevoSet(e.target.value)}
                        placeholder="Nombre del nuevo set"
                        className="flex-1 bg-gray-700 text-white px-3 py-2 rounded border border-gray-600"
                        onKeyPress={(e) => e.key === 'Enter' && handleCrearSet()}
                      />
                      <button
                        onClick={handleCrearSet}
                        className="bg-green-600 hover:bg-green-500 px-3 py-2 rounded text-white font-medium transition"
                      >
                        <Save size={16} />
                      </button>
                      <button
                        onClick={() => {
                          setCreandoSet(false);
                          setNuevoSet('');
                        }}
                        className="bg-gray-600 hover:bg-gray-500 px-3 py-2 rounded text-white font-medium transition"
                      >
                        <XCircle size={16} />
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => setCreandoSet(true)}
                      className="bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded text-white font-medium transition flex items-center gap-2"
                    >
                      <Plus size={16} />
                      Nuevo Set
                    </button>
                  )}
                </div>
              </div>

              {/* Lista de sets */}
              <div className="space-y-4">
                {loadingSets ? (
                  <div className="flex justify-center items-center h-32">
                    <div className="animate-spin w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full"></div>
                  </div>
                ) : sets.length === 0 ? (
                  <div className="text-center py-8 text-gray-400">
                    <Database size={48} className="mx-auto mb-2 opacity-50" />
                    <p>No hay sets de clasificación creados</p>
                    <p className="text-sm">Crea el primer set para comenzar</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {sets.map((set) => (
                      <div key={set.id} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                        {/* Header del set */}
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div className="flex items-center gap-2">
                              {editandoSet === set.id ? (
                                <input
                                  type="text"
                                  value={setEditando}
                                  onChange={(e) => setSetEditando(e.target.value)}
                                  className="bg-gray-700 text-white px-2 py-1 rounded border border-gray-600 font-medium"
                                  onKeyPress={(e) => e.key === 'Enter' && handleEditarSet()}
                                />
                              ) : (
                                <h4 className="text-white font-medium">{set.nombre}</h4>
                              )}
                              <span className="text-gray-400 text-sm">
                                ({obtenerOpcionesParaSet(set.id).length || 0} opciones)
                              </span>
                              
                              {/* Indicador de estado bilingüe */}
                              {(() => {
                                const opcionesEs = opcionesBilinguesPorSet[set.id]?.es || [];
                                const opcionesEn = opcionesBilinguesPorSet[set.id]?.en || [];
                                const tieneEspanol = opcionesEs.length > 0;
                                const tieneIngles = opcionesEn.length > 0;
                                
                                if (tieneEspanol && tieneIngles) {
                                  return (
                                    <span 
                                      className="px-2 py-0.5 bg-green-700 text-green-200 text-xs rounded-full flex items-center gap-1"
                                      title={`Bilingüe completo: ${opcionesEs.length} ES, ${opcionesEn.length} EN`}
                                    >
                                      <Globe size={10} />
                                      Bilingüe ({opcionesEs.length}/{opcionesEn.length})
                                    </span>
                                  );
                                } else if (tieneEspanol) {
                                  return (
                                    <span 
                                      className="px-2 py-0.5 bg-blue-700 text-blue-200 text-xs rounded-full"
                                      title={`Solo español: ${opcionesEs.length} opciones`}
                                    >
                                      Solo ES ({opcionesEs.length})
                                    </span>
                                  );
                                } else if (tieneIngles) {
                                  return (
                                    <span 
                                      className="px-2 py-0.5 bg-purple-700 text-purple-200 text-xs rounded-full"
                                      title={`Solo inglés: ${opcionesEn.length} opciones`}
                                    >
                                      Solo EN ({opcionesEn.length})
                                    </span>
                                  );
                                } else {
                                  return (
                                    <span 
                                      className="px-2 py-0.5 bg-gray-700 text-gray-300 text-xs rounded-full"
                                      title="Sin opciones bilingües"
                                    >
                                      Sin opciones
                                    </span>
                                  );
                                }
                              })()}
                            </div>
                            
                            {/* Selector de idioma individual - Solo para sets con opciones bilingües */}
                            {(() => {
                              const opcionesEs = opcionesBilinguesPorSet[set.id]?.es || [];
                              const opcionesEn = opcionesBilinguesPorSet[set.id]?.en || [];
                              const tieneOpcionesBilingues = opcionesEs.length > 0 && opcionesEn.length > 0;
                              
                              // Solo mostrar si el cliente es bilingüe Y el set tiene opciones en ambos idiomas
                              if (!cliente?.bilingue || !tieneOpcionesBilingues) {
                                return null;
                              }
                              
                              const idiomaActual = idiomaPorSet[set.id] || 'es';
                              
                              return (
                                <div className="flex items-center gap-1 bg-gray-700 rounded-lg p-1 border border-gray-600">
                                  <span className="text-xs text-gray-400 px-1">Este set:</span>
                                  <button
                                    onClick={() => cambiarIdiomaSet(set.id, 'es')}
                                    className={`px-2 py-1 rounded text-xs font-medium transition relative ${
                                      idiomaActual === 'es'
                                        ? 'bg-blue-600 text-white shadow-sm'
                                        : 'text-gray-300 hover:text-white hover:bg-gray-600'
                                    }`}
                                    title={`Español: ${opcionesEs.length} opciones disponibles`}
                                  >
                                    ES
                                    <span className="absolute -top-1 -right-1 bg-blue-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center leading-none">
                                      {opcionesEs.length}
                                    </span>
                                  </button>
                                  <button
                                    onClick={() => cambiarIdiomaSet(set.id, 'en')}
                                    className={`px-2 py-1 rounded text-xs font-medium transition relative ${
                                      idiomaActual === 'en'
                                        ? 'bg-blue-600 text-white shadow-sm'
                                        : 'text-gray-300 hover:text-white hover:bg-gray-600'
                                    }`}
                                    title={`Inglés: ${opcionesEn.length} opciones disponibles`}
                                  >
                                    EN
                                    <span className="absolute -top-1 -right-1 bg-green-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center leading-none">
                                      {opcionesEn.length}
                                    </span>
                                  </button>
                                </div>
                              );
                            })()}
                          </div>
                          
                          <div className="flex gap-1">
                            {editandoSet === set.id ? (
                              <>
                                <button
                                  onClick={handleEditarSet}
                                  className="p-1 text-green-400 hover:text-green-300"
                                  title="Guardar"
                                >
                                  <Save size={16} />
                                </button>
                                <button
                                  onClick={() => {
                                    setEditandoSet(null);
                                    setSetEditando('');
                                  }}
                                  className="p-1 text-gray-400 hover:text-gray-300"
                                  title="Cancelar"
                                >
                                  <XCircle size={16} />
                                </button>
                              </>
                            ) : (
                              <>
                                <button
                                  onClick={() => {
                                    setEditandoSet(set.id);
                                    setSetEditando(set.nombre);
                                  }}
                                  className="p-1 text-blue-400 hover:text-blue-300"
                                  title="Editar nombre"
                                >
                                  <Edit2 size={16} />
                                </button>
                                <button
                                  onClick={() => handleEliminarSet(set.id)}
                                  className="p-1 text-red-400 hover:text-red-300"
                                  title="Eliminar set"
                                >
                                  <Trash2 size={16} />
                                </button>
                              </>
                            )}
                          </div>
                        </div>

                        {/* Opciones del set */}
                        <div className="space-y-2">
                          <div className="flex flex-wrap gap-2">
                            {obtenerOpcionesParaSet(set.id)?.map((opcion) => {
                              // Determinar el texto a mostrar según el idioma seleccionado
                              const idiomaActual = idiomaPorSet[set.id] || 'es';
                              const textoOpcion = idiomaActual === 'en' && opcion.valor_en 
                                ? opcion.valor_en 
                                : (opcion.valor || 'Sin texto');
                              
                              return (
                                <div key={opcion.id} className="flex items-center gap-1 bg-blue-900/30 px-2 py-1 rounded">
                                  {editandoOpcion === opcion.id ? (
                                    <div className="flex flex-col gap-1">
                                      <input
                                        type="text"
                                        value={idiomaActual === 'es' ? opcionEditandoBilingue.es : opcionEditandoBilingue.en}
                                        onChange={(e) => setOpcionEditandoBilingue(prev => ({
                                          ...prev,
                                          [idiomaActual]: e.target.value
                                        }))}
                                        placeholder={`Valor en ${idiomaActual.toUpperCase()}`}
                                        className="bg-gray-700 text-white px-1 py-0.5 rounded border border-gray-600 text-sm w-24"
                                        onKeyPress={(e) => e.key === 'Enter' && handleEditarOpcion(opcion.id, set.id)}
                                      />
                                      {cliente?.bilingue && (
                                        <input
                                          type="text"
                                          value={idiomaActual === 'es' ? opcionEditandoBilingue.descripcion_es : opcionEditandoBilingue.descripcion_en}
                                          onChange={(e) => setOpcionEditandoBilingue(prev => ({
                                            ...prev,
                                            [`descripcion_${idiomaActual}`]: e.target.value
                                          }))}
                                          placeholder={`Descripción en ${idiomaActual.toUpperCase()}`}
                                          className="bg-gray-700 text-white px-1 py-0.5 rounded border border-gray-600 text-xs w-24"
                                        />
                                      )}
                                    </div>
                                  ) : (
                                    <span className="text-white text-sm" title={opcion.descripcion || opcion.descripcion_en}>
                                      {textoOpcion}
                                    </span>
                                  )}
                                  
                                  {/* Indicador de idioma y estado bilingüe */}
                                  <div className="flex flex-col items-center gap-0.5">
                                    <span className={`text-xs px-1 rounded ${
                                      idiomaActual === 'en' ? 'bg-green-700 text-green-200' : 'bg-blue-700 text-blue-200'
                                    }`}>
                                      {idiomaActual.toUpperCase()}
                                    </span>
                                    {cliente?.bilingue && opcion.es_bilingue && (
                                      <span className="text-xs px-1 rounded bg-purple-700 text-purple-200" title="Opción bilingüe">
                                        ES/EN
                                      </span>
                                    )}
                                  </div>
                                  
                                  <div className="flex gap-0.5 ml-1">
                                    {editandoOpcion === opcion.id ? (
                                      <>
                                        <button
                                          onClick={() => handleEditarOpcion(opcion.id, set.id)}
                                          className="text-green-400 hover:text-green-300"
                                          title="Guardar"
                                        >
                                          <Save size={12} />
                                        </button>
                                        <button
                                          onClick={() => {
                                            setEditandoOpcion(null);
                                            setOpcionEditandoBilingue({ es: '', en: '', descripcion_es: '', descripcion_en: '' });
                                          }}
                                          className="text-gray-400 hover:text-gray-300"
                                          title="Cancelar"
                                        >
                                          <XCircle size={12} />
                                        </button>
                                      </>
                                    ) : (
                                      <>
                                        <button
                                          onClick={() => {
                                            setEditandoOpcion(opcion.id);
                                            setOpcionEditandoBilingue({
                                              es: opcion.valor || '',
                                              en: opcion.valor_en || '',
                                              descripcion_es: opcion.descripcion || '',
                                              descripcion_en: opcion.descripcion_en || ''
                                            });
                                          }}
                                          className="text-blue-400 hover:text-blue-300"
                                          title={`Editar en ${idiomaActual.toUpperCase()}`}
                                        >
                                          <Edit2 size={12} />
                                        </button>
                                        <button
                                          onClick={() => handleEliminarOpcion(opcion.id)}
                                          className="text-red-400 hover:text-red-300"
                                          title="Eliminar"
                                        >
                                          <Trash2 size={12} />
                                        </button>
                                      </>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>

                          {/* Agregar nueva opción */}
                          <div className="space-y-2">
                            {creandoOpcionPara === set.id ? (
                              <div className="bg-gray-700/50 p-3 rounded border border-gray-600">
                                {/* Selector de modo de creación */}
                                {cliente?.bilingue && (
                                  <div className="mb-3">
                                    <label className="block text-xs text-gray-400 mb-2">Modo de creación:</label>
                                    <div className="flex gap-2">
                                      <button
                                        onClick={() => setModoCreacionOpcion('es')}
                                        className={`px-3 py-1 rounded text-sm transition ${
                                          modoCreacionOpcion === 'es' 
                                            ? 'bg-blue-600 text-white' 
                                            : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                                        }`}
                                      >
                                        🇪🇸 Solo Español
                                      </button>
                                      <button
                                        onClick={() => setModoCreacionOpcion('en')}
                                        className={`px-3 py-1 rounded text-sm transition ${
                                          modoCreacionOpcion === 'en' 
                                            ? 'bg-green-600 text-white' 
                                            : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                                        }`}
                                      >
                                        🇺🇸 Solo Inglés
                                      </button>
                                      <button
                                        onClick={() => setModoCreacionOpcion('ambos')}
                                        className={`px-3 py-1 rounded text-sm transition ${
                                          modoCreacionOpcion === 'ambos' 
                                            ? 'bg-purple-600 text-white' 
                                            : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                                        }`}
                                      >
                                        🌐 Bilingüe
                                      </button>
                                    </div>
                                  </div>
                                )}
                                
                                {/* Campos de entrada según el modo */}
                                <div className="space-y-2">
                                  {(modoCreacionOpcion === 'es' || modoCreacionOpcion === 'ambos') && (
                                    <div>
                                      <input
                                        type="text"
                                        value={nuevaOpcionBilingue.es}
                                        onChange={(e) => setNuevaOpcionBilingue(prev => ({ ...prev, es: e.target.value }))}
                                        placeholder="Valor en Español"
                                        className="w-full bg-gray-800 text-white px-2 py-1 rounded border border-gray-600 text-sm"
                                        onKeyPress={(e) => e.key === 'Enter' && handleCrearOpcion(set.id)}
                                      />
                                      <input
                                        type="text"
                                        value={nuevaOpcionBilingue.descripcion_es}
                                        onChange={(e) => setNuevaOpcionBilingue(prev => ({ ...prev, descripcion_es: e.target.value }))}
                                        placeholder="Descripción en Español (opcional)"
                                        className="w-full bg-gray-800 text-white px-2 py-1 rounded border border-gray-600 text-xs mt-1"
                                      />
                                    </div>
                                  )}
                                  
                                  {(modoCreacionOpcion === 'en' || modoCreacionOpcion === 'ambos') && (
                                    <div>
                                      <input
                                        type="text"
                                        value={nuevaOpcionBilingue.en}
                                        onChange={(e) => setNuevaOpcionBilingue(prev => ({ ...prev, en: e.target.value }))}
                                        placeholder="Valor en Inglés"
                                        className="w-full bg-gray-800 text-white px-2 py-1 rounded border border-gray-600 text-sm"
                                        onKeyPress={(e) => e.key === 'Enter' && handleCrearOpcion(set.id)}
                                      />
                                      <input
                                        type="text"
                                        value={nuevaOpcionBilingue.descripcion_en}
                                        onChange={(e) => setNuevaOpcionBilingue(prev => ({ ...prev, descripcion_en: e.target.value }))}
                                        placeholder="Descripción en Inglés (opcional)"
                                        className="w-full bg-gray-800 text-white px-2 py-1 rounded border border-gray-600 text-xs mt-1"
                                      />
                                    </div>
                                  )}
                                </div>
                                
                                {/* Botones de acción */}
                                <div className="flex gap-2 mt-3">
                                  <button
                                    onClick={() => handleCrearOpcion(set.id)}
                                    className="bg-green-600 hover:bg-green-500 px-3 py-1 rounded text-white text-sm transition flex items-center gap-1"
                                    title="Crear opción"
                                  >
                                    <Save size={14} />
                                    Crear
                                  </button>
                                  <button
                                    onClick={() => {
                                      setCreandoOpcionPara(null);
                                      setNuevaOpcionBilingue({ es: '', en: '', descripcion_es: '', descripcion_en: '' });
                                      setModoCreacionOpcion('es');
                                    }}
                                    className="bg-gray-600 hover:bg-gray-500 px-3 py-1 rounded text-white text-sm transition flex items-center gap-1"
                                    title="Cancelar"
                                  >
                                    <XCircle size={14} />
                                    Cancelar
                                  </button>
                                </div>
                              </div>
                            ) : (
                              <button
                                onClick={() => {
                                  setCreandoOpcionPara(set.id);
                                  // Detectar idioma actual del switch del set para inicializar el modo
                                  const idiomaActual = idiomaPorSet[set.id] || 'es';
                                  setModoCreacionOpcion(cliente?.bilingue ? idiomaActual : 'es');
                                }}
                                className="text-blue-400 hover:text-blue-300 flex items-center gap-1 text-sm"
                                title="Agregar opción"
                              >
                                <Plus size={14} />
                                Agregar opción
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-800 px-6 py-4 border-t border-gray-700">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4 text-sm text-gray-400">
              <span>
                {pestanaActiva === 'registros' ? (
                  `Mostrando ${registros.length} registros de clasificación`
                ) : (
                  `Gestionando ${sets.length} sets con ${Object.values(opcionesBilinguesPorSet).flatMap(opciones => [...(opciones.es || []), ...(opciones.en || [])]).length} opciones`
                )}
              </span>
              
              {/* Indicador de estado bilingüe */}
              {cliente?.bilingue && (
                <div className="flex items-center gap-1 px-2 py-1 bg-green-900/30 border border-green-700/50 rounded text-green-300">
                  <Globe size={12} />
                  <span className="text-xs">Cliente bilingüe</span>
                </div>
              )}
            </div>
            <button
              onClick={onClose}
              className="bg-gray-600 hover:bg-gray-500 text-white px-4 py-2 rounded font-medium transition"
            >
              Cerrar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModalClasificacionRegistrosRaw;
