import { useState, useEffect } from 'react';
import { X, Check, AlertTriangle, Clock, FileText, Plus, Edit2, Trash2, Save, XCircle, Settings, Database, FolderPlus, Globe, CheckSquare } from 'lucide-react';
import { 
  obtenerSetsCliente,
  crearSet,
  actualizarSet,
  eliminarSet,
  obtenerOpcionesSet,
  crearOpcion,
  actualizarOpcion,
  eliminarOpcion,
  registrarActividadTarjeta,
  // APIs REDISEÑADAS - usar AccountClassification como fuente única
  obtenerClasificacionesPorUpload,
  obtenerClasificacionesTemporales,
  obtenerClasificacionesPersistentes,
  obtenerClasificacionesPersistentesDetalladas,
  obtenerCuentasCliente,
  // APIs para CRUD directo en AccountClassification
  crearClasificacionPersistente,
  actualizarClasificacionPersistente,
  eliminarClasificacionPersistente,
  // Migración de temporales a FK
  migrarClasificacionesTemporalesAFK
} from '../../api/contabilidad';

const ModalClasificacionRegistrosRaw = ({ 
  isOpen, 
  onClose, 
  uploadId = null, // Usar el uploadId real si está disponible
  clienteId, 
  cierreId, 
  cliente, 
  onDataChanged
}) => {
  console.log('🏗️ Modal props recibidos:', { 
    isOpen, 
    uploadId, 
    clienteId,
    cierreId,
    clienteExiste: !!cliente,
    clienteBilingue: cliente?.bilingue,
    onDataChanged: !!onDataChanged
  });

  // Función auxiliar para registrar actividades CRUD
  const registrarActividad = async (tipo, accion, descripcion, detalles = {}) => {
    try {
      if (!clienteId) {
        console.warn('No hay clienteId para registrar actividad');
        return;
      }

      console.log('🔍 Registrando actividad:', { 
        tipo, 
        accion, 
        cierreId, 
        tienecierre: !!cierreId,
        cierreIdTipo: typeof cierreId
      });

      const detallesCompletos = {
        upload_id: uploadId,
        accion_origen: "modal_clasificaciones_persistentes",
        source_type: "persistent_db",
        ...detalles
      };

      // CORREGIDO: Usar SIEMPRE el cierreId si está disponible y es válido
      // El problema era que no estábamos usando el cierreId del cierre específico que se está editando
      if (cierreId && (typeof cierreId === 'number' || typeof cierreId === 'string') && cierreId != '0' && cierreId !== 0) {
        // Usar el cierreId específico del cierre que se está editando
        console.log('✅ Registrando actividad en el cierre específico:', cierreId);
        detallesCompletos.cierre_id = cierreId;
        await registrarActividadTarjeta(
          clienteId,
          tipo, 
          accion,
          descripcion,
          detallesCompletos,
          cierreId // IMPORTANTE: Pasar el cierreId específico
        );
        console.log('✅ Actividad registrada en cierre específico:', cierreId);
      } else {
        // Solo si realmente no hay cierreId, usar el período actual
        console.log('⚠️ No hay cierreId específico - registrando en período actual');
        
        if (cierreId !== undefined && cierreId !== null) {
          console.log(`   CierreId recibido: ${cierreId} (tipo: ${typeof cierreId})`);
          detallesCompletos.cierre_id_original = cierreId; // Para debug
        }
        
        // Sin cierreId, el backend usará el período actual
        await registrarActividadTarjeta(
          clienteId,
          tipo, 
          accion,
          descripcion,
          detallesCompletos
          // No pasar cierreId - backend usará período actual
        );
        console.log('✅ Actividad registrada en período actual');
      }
    } catch (error) {
      console.warn('❌ Error registrando actividad:', error);
      console.warn('   Detalles del error:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        cierreId_usado: cierreId,
        cierreId_tipo: typeof cierreId
      });
      
      // Log específico para problemas de cierre
      if (error.message && error.message.includes('cierre inexistente')) {
        console.warn('⚠️ Error: Cierre inexistente detectado');
        console.warn(`   CierreId problemático: ${cierreId} (tipo: ${typeof cierreId})`);
        console.warn('   Esto puede indicar que el cierre no existe en la base de datos');
      }
      
      // No fallar la operación principal por un error de logging
    }
  };

  // REDISEÑADO: Función para adaptar datos de AccountClassification al formato del modal
  const adaptarDatosAccountClassification = (clasificaciones, cuentasCliente) => {
    console.log('🔄 INICIANDO ADAPTACIÓN DE DATOS AccountClassification');
    console.log(`   Input: ${clasificaciones.length} clasificaciones, ${cuentasCliente.length} cuentas`);

    // Crear un mapa de cuentas por código para lookup rápido
    const cuentasMap = {};
    cuentasCliente.forEach(cuenta => {
      cuentasMap[cuenta.codigo] = cuenta;
    });

    // Agrupar clasificaciones por cuenta (código o FK)
    const clasificacionesPorCuenta = {};
    
    clasificaciones.forEach((clasificacion, index) => {
      // Log detallado para TODAS las clasificaciones para debug intensivo
      console.log(`🔍 Procesando clasificación ${index + 1}/${clasificaciones.length}:`, {
        id: clasificacion.id,
        cuenta_codigo: clasificacion.cuenta_codigo,
        cuenta_id: clasificacion.cuenta_id,
        set_nombre: clasificacion.set_nombre,
        opcion_valor: clasificacion.opcion_valor,
        origen: clasificacion.origen,
        es_temporal: clasificacion.es_temporal
      });
      
      // ACTUALIZADO: Usar los campos planos del serializer
      // El serializer devuelve set_nombre y opcion_valor en lugar de objetos anidados
      if (!clasificacion.set_nombre || !clasificacion.opcion_valor) {
        console.warn('⚠️ Clasificación con datos incompletos:', {
          id: clasificacion.id,
          cuenta_codigo: clasificacion.cuenta_codigo,
          cuenta_id: clasificacion.cuenta_id,
          set_nombre: clasificacion.set_nombre,
          opcion_valor: clasificacion.opcion_valor
        });
      }
      
      // CORREGIDO: Obtener código de cuenta según el tipo (FK o temporal)
      let codigoCuenta;
      if (clasificacion.cuenta_id) {
        // Clasificación con FK a cuenta - usar cuenta_codigo del serializador
        codigoCuenta = clasificacion.cuenta_codigo;
        console.log(`   → Clasificación con FK: código=${codigoCuenta}`);
      } else {
        // Clasificación temporal - usar cuenta_codigo directo del modelo
        codigoCuenta = clasificacion.cuenta_codigo;
        console.log(`   → Clasificación temporal: código=${codigoCuenta}`);
      }
      
      if (!codigoCuenta) {
        console.error('❌ Clasificación sin código de cuenta válido:', clasificacion);
        return;
      }
      
      if (!clasificacionesPorCuenta[codigoCuenta]) {
        // Obtener nombre de cuenta
        let nombreCuenta;
        if (clasificacion.cuenta_id && clasificacion.cuenta_nombre) {
          nombreCuenta = clasificacion.cuenta_nombre;
        } else if (cuentasMap[codigoCuenta]) {
          nombreCuenta = cuentasMap[codigoCuenta].nombre;
        } else {
          nombreCuenta = `[TEMPORAL] Cuenta ${codigoCuenta}`;
        }
        
        console.log(`   → Creando nueva agrupación para cuenta ${codigoCuenta}: ${nombreCuenta}`);
        
        clasificacionesPorCuenta[codigoCuenta] = {
          numero_cuenta: codigoCuenta,
          nombre_cuenta: nombreCuenta,
          clasificaciones: {},
          cuenta_existe: !!clasificacion.cuenta_id,
          es_temporal: clasificacion.es_temporal || !clasificacion.cuenta_id,
          upload_log: clasificacion.upload_log,
          fecha_creacion: clasificacion.fecha_creacion,
          origen: clasificacion.origen
        };
      }
      
      // ACTUALIZADO: Agregar la clasificación usando los campos planos del serializer
      if (clasificacion.set_nombre && clasificacion.opcion_valor) {
        console.log(`   → Agregando clasificación: ${clasificacion.set_nombre} = ${clasificacion.opcion_valor}`);
        clasificacionesPorCuenta[codigoCuenta].clasificaciones[clasificacion.set_nombre] = 
          clasificacion.opcion_valor;
      } else {
        // Log para debug en caso de datos incompletos
        console.error('❌ Clasificación incompleta - NO SE AGREGARÁ:', {
          cuenta: codigoCuenta,
          set_nombre: clasificacion.set_nombre,
          opcion_valor: clasificacion.opcion_valor,
          clasificacion_id: clasificacion.id
        });
      }
    });

    console.log('📊 RESUMEN DE AGRUPACIÓN POR CUENTA:');
    Object.entries(clasificacionesPorCuenta).forEach(([codigo, datos]) => {
      console.log(`   ${codigo}: ${Object.keys(datos.clasificaciones).length} clasificaciones`);
    });

    // Convertir a array y agregar información de cuentas
  const registrosAdaptados = Object.entries(clasificacionesPorCuenta).map(([codigoCuenta, datos], index) => {
      const cuenta = cuentasMap[codigoCuenta];
      
      const registro = {
        id: `account_${codigoCuenta}_${index}`, // ID único para el frontend
        numero_cuenta: codigoCuenta,
        cuenta_nombre: cuenta?.nombre || datos.nombre_cuenta || '',
        cuenta_nombre_en: cuenta?.nombre_en || '',
        clasificaciones: datos.clasificaciones,
        // Campos adicionales del nuevo flujo
        cuenta_existe: datos.cuenta_existe,
        es_temporal: datos.es_temporal,
        upload_log: datos.upload_log,
        fecha_creacion: datos.fecha_creacion,
        origen: datos.origen,
        source_type: 'account_classification'
      };
      
      console.log(`📋 Registro adaptado ${index + 1}: ${codigoCuenta} con ${Object.keys(datos.clasificaciones).length} clasificaciones`);
      
      return registro;
    });

    // ➕ Incluir cuentas sin ninguna clasificación (para edición futura)
    const codigosConClasificaciones = new Set(Object.keys(clasificacionesPorCuenta));
    let agregadosSinClasificar = 0;
    cuentasCliente.forEach((cuenta, idx) => {
      if (!codigosConClasificaciones.has(cuenta.codigo)) {
        registrosAdaptados.push({
          id: `account_${cuenta.codigo}_no_class_${idx}`,
            numero_cuenta: cuenta.codigo,
            cuenta_nombre: cuenta.nombre || '',
            cuenta_nombre_en: cuenta.nombre_en || '',
            clasificaciones: {},
            cuenta_existe: true,
            es_temporal: false,
            upload_log: null,
            fecha_creacion: null,
            origen: 'sin_clasificacion',
            source_type: 'account'
        });
        agregadosSinClasificar++;
      }
    });

    console.log('✅ ADAPTACIÓN COMPLETADA:');
    console.log(`   Input: ${clasificaciones.length} clasificaciones individuales`);
    console.log(`   Output: ${registrosAdaptados.length} registros (incluye ${agregadosSinClasificar} cuentas sin clasificar)`);
    if (registrosAdaptados.length>0) {
      console.log('🔍 Primer registro final:', registrosAdaptados[0]);
    }
    
    return registrosAdaptados;
  };

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
  
  // Estados para creación masiva de cuentas
  const [creandoMasivo, setCreandoMasivo] = useState(false);
  const [cuentasMasivas, setCuentasMasivas] = useState([]);
  const [aplicandoCreacionMasiva, setAplicandoCreacionMasiva] = useState(false);
  
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
  const [aplicandoClasificacionMasiva, setAplicandoClasificacionMasiva] = useState(false);
  const [guardandoEdicionAuto, setGuardandoEdicionAuto] = useState(false); // para autosave al agregar clasificación en edición
  
  // Estados para pegado masivo en clasificación masiva
  const [textoBusquedaMasiva, setTextoBusquedaMasiva] = useState('');

  useEffect(() => {
    console.log('🎯 useEffect ejecutado:', { 
      isOpen, 
      uploadId, 
      clienteId, 
      cliente: !!cliente,
      clienteBilingue: cliente?.bilingue,
      clienteCompleto: cliente ? { id: cliente.id, nombre: cliente.nombre, bilingue: cliente.bilingue } : null,
      cierreId,
      cierreIdTipo: typeof cierreId,
      cierreIdValido: cierreId && (typeof cierreId === 'number' || typeof cierreId === 'string') && cierreId != '0' && cierreId !== 0
    });
    
    if (isOpen && clienteId) {
      console.log('✅ Condiciones cumplidas - iniciando carga de datos');
      console.log('📋 Contexto del cierre:', {
        cierreId,
        esEdicionDeCierre: !!cierreId,
        periodo: cierreId ? `Editando cierre ID ${cierreId}` : 'Sin cierre específico'
      });
      
      // Marcar tiempo de apertura del modal para estadísticas
      window.modalClasificacionesOpenTime = Date.now();
      
      // Cargar los datos
      cargarRegistros();
      cargarSets();
      
      // Registrar apertura del modal en el cierre específico si estamos editando uno
      registrarActividad(
        "clasificacion",
        "open_persistent_modal",
        cierreId ? 
          `Abrió modal de clasificaciones para cierre ${cierreId}` : 
          "Abrió modal de clasificaciones persistentes",
        {
          uploadId: uploadId,
          modo_inicial: "registros",
          cierre_id_recibido: cierreId,
          editando_cierre_especifico: !!cierreId,
          contexto: cierreId ? "edicion_cierre" : "general"
        }
      ).catch(err => console.warn("Error registrando apertura del modal:", err));
    } else {
      console.log('❌ Condiciones no cumplidas para carga', { 
        isOpen, 
        clienteId
      });
    }
  }, [isOpen, clienteId, uploadId, cierreId]);

  const cargarRegistros = async () => {
    setLoading(true);
    try {
      console.log('🔄 INICIANDO CARGA DE REGISTROS EN MODAL');
      console.log('🔍 Parámetros de carga:', { uploadId, clienteId });
      
      // REDISEÑADO: Siempre cargar todas las clasificaciones persistentes del cliente
      console.log('📊 Cargando TODAS las clasificaciones persistentes del cliente (incluyendo temporales)...');
      const [clasificacionesPersistentes, cuentasCliente] = await Promise.all([
        obtenerClasificacionesPersistentesDetalladas(clienteId), // CORREGIDO: Usar función que incluye temporales
        obtenerCuentasCliente(clienteId)
      ]);
      
      // DEBUG: Examinar datos crudos de la API
      console.log('🔍 DATOS CRUDOS RECIBIDOS DE LA API:');
      console.log('  - Clasificaciones count:', clasificacionesPersistentes.length);
      console.log('  - Cuentas count:', cuentasCliente.length);
      
      if (clasificacionesPersistentes.length > 0) {
        console.log('  - Primera clasificación completa:', clasificacionesPersistentes[0]);
        console.log('  - Últimas 3 clasificaciones:', clasificacionesPersistentes.slice(-3));
      } else {
        console.log('  ❌ NO HAY CLASIFICACIONES PERSISTENTES RECIBIDAS');
      }
      
      if (cuentasCliente.length > 0) {
        console.log('  - Primera cuenta:', cuentasCliente[0]);
        console.log('  - Total cuentas:', cuentasCliente.length);
      } else {
        console.log('  ❌ NO HAY CUENTAS DEL CLIENTE');
      }
      
      // Adaptar datos al formato esperado por el modal
      console.log('🔄 Iniciando adaptación de datos...');
      const data = adaptarDatosAccountClassification(clasificacionesPersistentes, cuentasCliente);
      console.log('✅ Datos adaptados:', data.length, 'registros');
      
      if (data.length > 0) {
        console.log('🔍 PRIMER REGISTRO ADAPTADO:', data[0]);
        console.log('🔍 ESTRUCTURA DE CLASIFICACIONES DEL PRIMER REGISTRO:', data[0].clasificaciones);
      } else {
        console.log('❌ NO HAY REGISTROS ADAPTADOS - INVESTIGAR PROBLEMA EN adaptarDatosAccountClassification');
      }
      
      setRegistros(data);
      calcularEstadisticas(data);
      console.log('✅ Modal - Clasificaciones cargadas y establecidas en estado:', data.length);
    } catch (error) {
      console.error("❌ ERROR CARGANDO CLASIFICACIONES EN MODAL:", error);
      if (error.response) {
        console.error("   Response status:", error.response.status);
        console.error("   Response data:", error.response.data);
      }
      setRegistros([]);
      calcularEstadisticas([]);
    } finally {
      setLoading(false);
      console.log('🏁 CARGA DE REGISTROS EN MODAL COMPLETADA');
      console.log('─'.repeat(80));
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
          console.log(`📋 Opciones RAW para set ${set.id} (${set.nombre}):`, opciones);
          
          // DEBUG: Examinar cada opción individualmente
          opciones.forEach((opcion, index) => {
            console.log(`🔍 Opción ${index + 1} completa:`, {
              id: opcion.id,
              valor: opcion.valor,
              valor_en: opcion.valor_en,
              valor_es: opcion.valor_es,
              descripcion: opcion.descripcion,
              descripcion_en: opcion.descripcion_en,
              descripcion_es: opcion.descripcion_es,
              tiene_es: opcion.tiene_es,
              tiene_en: opcion.tiene_en,
              todosLosCampos: Object.keys(opcion)
            });
          });
          
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

  // Función para manejar el cierre del modal con logging
  const handleClose = async () => {
    try {
      await registrarActividad(
        "clasificacion",
        "close_persistent_modal",
        cierreId ? 
          `Cerró modal de clasificaciones para cierre ${cierreId}` : 
          `Cerró modal de clasificaciones persistentes`,
        {
          tiempo_sesion: Date.now() - (window.modalClasificacionesOpenTime || Date.now()),
          pestana_activa: pestanaActiva,
          registros_cargados: registros.length,
          sets_disponibles: sets.length,
          editando_cierre_especifico: !!cierreId,
          contexto: cierreId ? "edicion_cierre" : "general"
        }
      );
    } catch (logErr) {
      console.warn("Error registrando cierre del modal:", logErr);
    }
    
    // Limpiar timestamp
    delete window.modalClasificacionesOpenTime;
    
    onClose();
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

  const agregarClasificacionARegistro = async () => {
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
      // Construir nuevo objeto de edición con la clasificación añadida
      const nuevoRegistroEditado = {
        ...registroEditando,
        clasificaciones: {
          ...(registroEditando?.clasificaciones || {}),
          [setEncontrado.nombre]: opcionSeleccionada
        }
      };
      setRegistroEditando(nuevoRegistroEditado);

      // Persistir automáticamente la edición para evitar que se "pierda" al recargar
      try {
        setGuardandoEdicionAuto(true);
        const registroActual = registros.find(r => r.id === editandoId);
        if (registroActual) {
          await actualizarClasificacionPersistente(registroActual.numero_cuenta, {
            cliente: clienteId,
            nuevo_numero_cuenta: nuevoRegistroEditado.numero_cuenta.trim(),
            cuenta_nombre: nuevoRegistroEditado.numero_cuenta.trim(),
            clasificaciones: nuevoRegistroEditado.clasificaciones
          });
          // Actualizar lista sin cerrar edición para que el usuario vea reflejado
          await cargarRegistros();
          // Mantener modo edición (buscamos de nuevo el registro por número de cuenta)
          const recargado = registros.find(r => r.numero_cuenta === nuevoRegistroEditado.numero_cuenta);
          if (recargado) {
            setEditandoId(recargado.id);
          }
        }
      } catch (e) {
        console.error('Error guardando automáticamente la nueva clasificación:', e);
        alert('No se pudo guardar automáticamente la nueva clasificación. Revisa la consola.');
      } finally {
        setGuardandoEdicionAuto(false);
      }
    } else {
      // Usuario intentó agregar sin estar creando ni editando
      alert('Para agregar clasificaciones a una cuenta existente primero haz clic en el ícono de edición.');
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
    
    // Registrar actividad de cambio de pestaña
    try {
      await registrarActividad(
        "clasificacion",
        "view_data",
        `Cambió a pestaña ${nuevaPestana} en modal de clasificaciones`,
        {
          pestana_anterior: pestanaActiva,
          pestana_nueva: nuevaPestana
        }
      );
    } catch (logErr) {
      console.warn("Error registrando cambio de pestaña:", logErr);
    }
    
    setPestanaActiva(nuevaPestana);
  };

  // ==================== FUNCIONES CRUD PARA SETS ====================
  const handleCrearSet = async () => {
    if (!nuevoSet.trim()) {
      alert("El nombre del set es requerido");
      return;
    }
    try {
      const setCreado = await crearSet(clienteId, nuevoSet.trim());
      
      // Registrar actividad detallada de creación de set
      try {
        await registrarActividad(
          "clasificacion",
          "set_create",
          `Creó set de clasificación desde modal: ${nuevoSet.trim()}`,
          {
            set_id: setCreado.id,
            nombre_set: nuevoSet.trim()
          }
        );
      } catch (logErr) {
        console.warn("Error registrando actividad de creación de set:", logErr);
      }
      
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
      // Obtener datos del set antes de editar para el log
      const setActual = sets.find(s => s.id === editandoSet);
      const datosAnteriores = setActual ? {
        nombre_anterior: setActual.nombre
      } : {};
      
      await actualizarSet(editandoSet, setEditando.trim());
      
      // Registrar actividad detallada de edición de set
      try {
        await registrarActividad(
          "clasificacion",
          "set_edit",
          `Editó set de clasificación desde modal: ${setEditando.trim()}`,
          {
            set_id: editandoSet,
            nombre_nuevo: setEditando.trim(),
            ...datosAnteriores
          }
        );
      } catch (logErr) {
        console.warn("Error registrando actividad de edición de set:", logErr);
      }
      
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
        // Obtener datos del set antes de eliminar para el log
        const setAEliminar = sets.find(s => s.id === setId);
        const datosEliminado = setAEliminar ? {
          nombre: setAEliminar.nombre
        } : {};
        
        await eliminarSet(setId);
        
        // Registrar actividad detallada de eliminación de set
        try {
          await registrarActividad(
            "clasificacion",
            "set_delete",
            `Eliminó set de clasificación desde modal: ${datosEliminado.nombre || 'N/A'}`,
            {
              set_id: setId,
              ...datosEliminado
            }
          );
        } catch (logErr) {
          console.warn("Error registrando actividad de eliminación de set:", logErr);
        }
        
        await cargarSets();
      } catch (error) {
        console.error("Error eliminando set:", error);
        alert("Error al eliminar el set");
      }
    }
  };

  // ==================== FUNCIONES CRUD PARA OPCIONES ====================
  const handleCrearOpcion = async (setId) => {
    console.log('🚀 Iniciando creación de opción:', {
      setId,
      modoCreacionOpcion,
      nuevaOpcionBilingue,
      clienteBilingue: cliente?.bilingue
    });

    // Validación según el modo de creación
    if (modoCreacionOpcion === 'ambos') {
      // Validar que ambos idiomas tengan valor
      if (!nuevaOpcionBilingue.es.trim() || !nuevaOpcionBilingue.en.trim()) {
        alert("Para crear una opción bilingüe, debe proporcionar el valor en ambos idiomas");
        return;
      }
      
      try {
        const datosOpcion = {
          valor: nuevaOpcionBilingue.es.trim(),
          valor_en: nuevaOpcionBilingue.en.trim(),
          descripcion: nuevaOpcionBilingue.descripcion_es.trim() || '',
          descripcion_en: nuevaOpcionBilingue.descripcion_en.trim() || '',
        };
        
        console.log('📤 DATOS COMPLETOS ENVIANDO AL BACKEND (modo bilingüe):', {
          setId,
          datosOpcion,
          modoCreacionOpcion,
          estadoCompleto: nuevaOpcionBilingue
        });
        
        const opcionCreada = await crearOpcion(setId, datosOpcion);
        
        console.log('✅ RESPUESTA COMPLETA DEL BACKEND:', {
          opcionCreada,
          respuestaCompleta: JSON.stringify(opcionCreada, null, 2)
        });
        
        // Verificar qué campos se guardaron realmente
        if (opcionCreada.valor && opcionCreada.valor_en) {
          console.log('✅ Ambos idiomas guardados correctamente:', {
            español: opcionCreada.valor,
            inglés: opcionCreada.valor_en
          });
        } else if (opcionCreada.valor && !opcionCreada.valor_en) {
          console.error('❌ PROBLEMA: Solo se guardó español:', {
            español: opcionCreada.valor,
            inglés: opcionCreada.valor_en || 'NO GUARDADO'
          });
        } else {
          console.error('❌ PROBLEMA: Datos inesperados en respuesta:', opcionCreada);
        }
        
        // Registrar actividad detallada de creación de opción bilingüe
        try {
          const setActual = sets.find(s => s.id === setId);
          await registrarActividad(
            "clasificacion",
            "option_create",
            `Creó opción bilingüe desde modal: ${datosOpcion.valor} / ${datosOpcion.valor_en}`,
            {
              opcion_id: opcionCreada.id,
              set_id: setId,
              set_nombre: setActual?.nombre,
              valor_es: datosOpcion.valor,
              valor_en: datosOpcion.valor_en,
              descripcion_es: datosOpcion.descripcion,
              descripcion_en: datosOpcion.descripcion_en,
              tipo_creacion: "bilingue",
              // Datos de verificación
              guardado_es: opcionCreada.valor,
              guardado_en: opcionCreada.valor_en,
              ambos_idiomas_guardados: !!(opcionCreada.valor && opcionCreada.valor_en)
            }
          );
        } catch (logErr) {
          console.warn("Error registrando actividad de creación de opción bilingüe:", logErr);
        }
        
        // Limpiar estados después del éxito
        setNuevaOpcionBilingue({ es: '', en: '', descripcion_es: '', descripcion_en: '' });
        setCreandoOpcionPara(null);
        setModoCreacionOpcion('es'); // Reset al modo por defecto
        
        // Mostrar mensaje específico según lo que se guardó
        if (opcionCreada.valor && opcionCreada.valor_en) {
          alert(`✅ Opción bilingüe creada exitosamente:\n🇪🇸 Español: ${opcionCreada.valor}\n🇺🇸 Inglés: ${opcionCreada.valor_en}`);
        } else if (opcionCreada.valor && !opcionCreada.valor_en) {
          alert(`⚠️ PROBLEMA: Solo se guardó en español: "${opcionCreada.valor}"\nEl inglés NO se guardó. Verificar backend.`);
        } else {
          alert(`Opción creada: ${datosOpcion.valor} / ${datosOpcion.valor_en}`);
        }
        
        await cargarSets();
        
      } catch (error) {
        console.error("❌ Error creando opción bilingüe:", error);
        let errorMessage = "Error al crear la opción bilingüe";
        if (error.response?.data?.error) {
          errorMessage += `: ${error.response.data.error}`;
        } else if (error.response?.data?.detail) {
          errorMessage += `: ${error.response.data.detail}`;
        }
        alert(errorMessage);
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
          if (descripcion && descripcion.trim()) datos.descripcion = descripcion.trim();
        } else {
          datos.valor_en = valor.trim();
          if (descripcion && descripcion.trim()) datos.descripcion_en = descripcion.trim();
        }
        
        console.log(`📤 Enviando datos de opción ${modoCreacionOpcion.toUpperCase()}:`, datos);
        const opcionCreada = await crearOpcion(setId, datos);
        console.log('✅ Opción monolingüe creada exitosamente:', opcionCreada);
        
        // Registrar actividad detallada de creación de opción monolingüe
        try {
          const setActual = sets.find(s => s.id === setId);
          await registrarActividad(
            "clasificacion",
            "option_create",
            `Creó opción en ${modoCreacionOpcion.toUpperCase()} desde modal: ${valor.trim()}`,
            {
              opcion_id: opcionCreada.id,
              set_id: setId,
              set_nombre: setActual?.nombre,
              idioma: modoCreacionOpcion,
              valor: valor.trim(),
              descripcion: descripcion?.trim() || '',
              tipo_creacion: "monolingue"
            }
          );
        } catch (logErr) {
          console.warn("Error registrando actividad de creación de opción:", logErr);
        }
        
        // Limpiar estados después del éxito
        setNuevaOpcionBilingue({ es: '', en: '', descripcion_es: '', descripcion_en: '' });
        setCreandoOpcionPara(null);
        setModoCreacionOpcion('es'); // Reset al modo por defecto
        await cargarSets();
        
        alert(`Opción creada exitosamente: ${valor.trim()}`);
        
      } catch (error) {
        console.error("❌ Error creando opción monolingüe:", error);
        let errorMessage = "Error al crear la opción";
        if (error.response?.data?.error) {
          errorMessage += `: ${error.response.data.error}`;
        } else if (error.response?.data?.detail) {
          errorMessage += `: ${error.response.data.detail}`;
        }
        alert(errorMessage);
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
      
      // Obtener datos actuales de la opción para el log
      const opcionesActuales = obtenerOpcionesParaSet(setClasId);
      const opcionActual = opcionesActuales.find(o => o.id === opcionId);
      const datosAnteriores = opcionActual ? {
        valor_anterior: opcionActual.valor,
        descripcion_anterior: opcionActual.descripcion
      } : {};
      
      await actualizarOpcion(opcionId, datos, setClasId);
      
      // Registrar actividad detallada de edición de opción
      try {
        const setActual = sets.find(s => s.id === setClasId);
        await registrarActividad(
          "clasificacion",
          "option_edit",
          `Editó opción en ${idiomaActual.toUpperCase()} desde modal: ${valorAEditar}`,
          {
            opcion_id: opcionId,
            set_id: setClasId,
            set_nombre: setActual?.nombre,
            idioma_editado: idiomaActual,
            valor_nuevo: valorAEditar,
            descripcion_nueva: idiomaActual === 'es' ? 
              opcionEditandoBilingue.descripcion_es.trim() : 
              opcionEditandoBilingue.descripcion_en.trim(),
            ...datosAnteriores
          }
        );
      } catch (logErr) {
        console.warn("Error registrando actividad de edición de opción:", logErr);
      }
      
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
        // Obtener datos de la opción antes de eliminar para el log
        let opcionAEliminar = null;
        let setContenedor = null;
        
        // Buscar la opción en todos los sets
        for (const set of sets) {
          const opciones = obtenerOpcionesParaSet(set.id);
          const opcionEncontrada = opciones.find(o => o.id === opcionId);
          if (opcionEncontrada) {
            opcionAEliminar = opcionEncontrada;
            setContenedor = set;
            break;
          }
        }
        
        const datosEliminado = opcionAEliminar ? {
          valor: opcionAEliminar.valor,
          descripcion: opcionAEliminar.descripcion
        } : {};
        
        await eliminarOpcion(opcionId);
        
        // Registrar actividad detallada de eliminación de opción
        try {
          await registrarActividad(
            "clasificacion",
            "option_delete",
            `Eliminó opción desde modal: ${datosEliminado.valor || 'N/A'}`,
            {
              opcion_id: opcionId,
              set_id: setContenedor?.id,
              set_nombre: setContenedor?.nombre,
              ...datosEliminado
            }
          );
        } catch (logErr) {
          console.warn("Error registrando actividad de eliminación de opción:", logErr);
        }
        
        await cargarSets();
      } catch (error) {
        console.error("Error eliminando opción:", error);
        alert("Error al eliminar la opción");
      }
    }
  };

  // ==================== FUNCIONES CRUD PARA REGISTROS ====================
  const handleIniciarCreacion = () => {
    // Cancelar modo masivo si está activo
    if (creandoMasivo) {
      handleCancelarCreacionMasiva();
    }
    
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
    
    // También cancelar modo masivo si está activo
    if (creandoMasivo) {
      handleCancelarCreacionMasiva();
    }
  };

  // ==================== FUNCIONES PARA CREACIÓN MASIVA ====================
  const procesarTextoPegado = (texto) => {
    console.log('🔄 Procesando texto pegado:', texto);
    
    // Dividir por líneas y limpiar
    const lineas = texto.split(/[\r\n]+/).map(linea => linea.trim()).filter(linea => linea.length > 0);
    
    console.log('📋 Líneas detectadas:', lineas);
    
    // Si hay más de una línea, es creación masiva
    if (lineas.length > 1) {
      console.log('✅ Detectada creación masiva con', lineas.length, 'cuentas');
      
      // Validar que las cuentas no existan ya
      const cuentasExistentes = [];
      const cuentasNuevas = [];
      
      lineas.forEach(cuenta => {
        const existe = registros.some(r => r.numero_cuenta === cuenta);
        if (existe) {
          cuentasExistentes.push(cuenta);
        } else {
          cuentasNuevas.push({
            numero_cuenta: cuenta,
            clasificaciones: {},
            existe: false
          });
        }
      });
      
      if (cuentasExistentes.length > 0) {
        console.warn('⚠️ Cuentas que ya existen:', cuentasExistentes);
      }
      
      console.log('📝 Cuentas nuevas a crear:', cuentasNuevas.length);
      
      return {
        esMultiple: true,
        cuentasNuevas,
        cuentasExistentes,
        totalLineas: lineas.length
      };
    }
    
    return {
      esMultiple: false,
      cuenta: lineas[0] || '',
      totalLineas: lineas.length
    };
  };

  const handleTextoPegado = (texto) => {
    const resultado = procesarTextoPegado(texto);
    
    if (resultado.esMultiple) {
      // Mostrar alerta si hay cuentas existentes
      if (resultado.cuentasExistentes.length > 0) {
        const mensaje = `⚠️ Detectadas ${resultado.totalLineas} cuentas. ${resultado.cuentasExistentes.length} ya existen y se omitirán:\n\n${resultado.cuentasExistentes.join('\n')}\n\n¿Continuar con las ${resultado.cuentasNuevas.length} cuentas nuevas?`;
        
        if (!confirm(mensaje)) {
          return;
        }
      }
      
      // Iniciar creación masiva
      setCuentasMasivas(resultado.cuentasNuevas);
      setCreandoMasivo(true);
      setCreandoNuevo(false); // Asegurar que no está en modo individual
    } else {
      // Creación individual normal
      setNuevoRegistro(prev => ({ ...prev, numero_cuenta: resultado.cuenta }));
    }
  };

  const handleCancelarCreacionMasiva = () => {
    setCreandoMasivo(false);
    setCuentasMasivas([]);
  };

  const aplicarClasificacionMasivaACuentas = () => {
    if (!setMasivo || !opcionMasiva) {
      alert('Debe seleccionar un set y una opción para aplicar a todas las cuentas');
      return;
    }

    const setNombre = obtenerSetsDisponibles().find(s => s.id === setMasivo)?.nombre;
    if (!setNombre) {
      alert('Error: No se pudo encontrar el set seleccionado');
      return;
    }

    // Aplicar la clasificación a todas las cuentas
    setCuentasMasivas(cuentas => 
      cuentas.map(cuenta => ({
        ...cuenta,
        clasificaciones: {
          ...cuenta.clasificaciones,
          [setNombre]: opcionMasiva
        }
      }))
    );

    // Limpiar selección
    setSetMasivo('');
    setOpcionMasiva('');
  };

  const removerClasificacionDeCuentaMasiva = (indiceCuenta, setNombre) => {
    setCuentasMasivas(cuentas => 
      cuentas.map((cuenta, index) => {
        if (index === indiceCuenta) {
          const nuevasClasificaciones = { ...cuenta.clasificaciones };
          delete nuevasClasificaciones[setNombre];
          return {
            ...cuenta,
            clasificaciones: nuevasClasificaciones
          };
        }
        return cuenta;
      })
    );
  };

  const handleGuardarCreacionMasiva = async () => {
    if (cuentasMasivas.length === 0) {
      alert('No hay cuentas para crear');
      return;
    }

    const cuentasSinClasificar = cuentasMasivas.filter(cuenta => Object.keys(cuenta.clasificaciones).length === 0);
    
    if (cuentasSinClasificar.length > 0) {
      const mensaje = `${cuentasSinClasificar.length} cuentas no tienen clasificaciones asignadas:\n\n${cuentasSinClasificar.map(c => c.numero_cuenta).join('\n')}\n\n¿Continuar de todas formas?`;
      
      if (!confirm(mensaje)) {
        return;
      }
    }

    setAplicandoCreacionMasiva(true);
    let errores = [];
    let exitosos = 0;

    try {
      console.log('🚀 Iniciando creación masiva de', cuentasMasivas.length, 'cuentas');

      for (const cuenta of cuentasMasivas) {
        try {
          const datosAEnviar = {
            cliente: clienteId,
            numero_cuenta: cuenta.numero_cuenta.trim(),
            cuenta_nombre: cuenta.numero_cuenta.trim(),
            clasificaciones: cuenta.clasificaciones
          };

          console.log('📝 Creando cuenta:', cuenta.numero_cuenta);
          await crearClasificacionPersistente(datosAEnviar);
          exitosos++;

          // Registrar actividad individual
          try {
            await registrarActividad(
              "clasificacion",
              "bulk_create",
              `Creó cuenta en creación masiva: ${cuenta.numero_cuenta}`,
              {
                numero_cuenta: cuenta.numero_cuenta,
                cantidad_clasificaciones: Object.keys(cuenta.clasificaciones).length,
                clasificaciones: cuenta.clasificaciones,
                source_type: "persistent_db",
                es_creacion_masiva: true
              }
            );
          } catch (logErr) {
            console.warn("Error registrando actividad individual:", logErr);
          }

        } catch (error) {
          console.error('❌ Error creando cuenta', cuenta.numero_cuenta, ':', error);
          
          let errorMessage = `${cuenta.numero_cuenta}: `;
          if (error.response?.data?.detail) {
            errorMessage += error.response.data.detail;
          } else if (error.response?.data) {
            errorMessage += JSON.stringify(error.response.data);
          } else {
            errorMessage += error.message || 'Error desconocido';
          }
          
          errores.push(errorMessage);
        }
      }

      // Registrar actividad de resumen
      try {
        await registrarActividad(
          "clasificacion",
          "bulk_create_summary",
          `Creación masiva completada: ${exitosos} exitosas, ${errores.length} errores`,
          {
            total_intentos: cuentasMasivas.length,
            exitosos,
            errores: errores.length,
            source_type: "persistent_db",
            cuentas_exitosas: cuentasMasivas.slice(0, exitosos).map(c => c.numero_cuenta)
          }
        );
      } catch (logErr) {
        console.warn("Error registrando actividad de resumen:", logErr);
      }

      // Mostrar resultado
      let mensaje = `✅ Creación masiva completada:\n\n`;
      mensaje += `• ${exitosos} cuentas creadas exitosamente\n`;
      
      if (errores.length > 0) {
        mensaje += `• ${errores.length} errores:\n\n${errores.join('\n')}`;
      }
      
      alert(mensaje);

      // Recargar datos y limpiar
      await cargarRegistros();
      handleCancelarCreacionMasiva();
      if (onDataChanged) onDataChanged();

    } catch (error) {
      console.error('❌ Error general en creación masiva:', error);
      alert('Error general durante la creación masiva: ' + (error.message || 'Error desconocido'));
    } finally {
      setAplicandoCreacionMasiva(false);
    }
  };

  const handleGuardarNuevo = async () => {
    if (!nuevoRegistro.numero_cuenta.trim()) {
      alert("El número de cuenta es requerido");
      return;
    }

    // Validar que el número de cuenta no exista ya
    const numeroCuentaExiste = registros.some(r => r.numero_cuenta === nuevoRegistro.numero_cuenta.trim());
    if (numeroCuentaExiste) {
      alert(`El número de cuenta "${nuevoRegistro.numero_cuenta}" ya existe. Por favor usa un número diferente o edita el registro existente.`);
      return;
    }

    try {
      const datosAEnviar = {
        cliente: clienteId,
        numero_cuenta: nuevoRegistro.numero_cuenta.trim(),
        cuenta_nombre: nuevoRegistro.numero_cuenta.trim(), // Por defecto usar el código como nombre
        clasificaciones: nuevoRegistro.clasificaciones
      };
      
      console.log('=== CREANDO NUEVO REGISTRO PERSISTENTE ===');
      console.log('Cliente ID:', clienteId);
      console.log('Datos completos a enviar:', JSON.stringify(datosAEnviar, null, 2));

      const registroCreado = await crearClasificacionPersistente(datosAEnviar);
      
      // Registrar actividad detallada de creación de registro
      try {
        await registrarActividad(
          "clasificacion",
          "individual_create",
          `Creó registro persistente desde modal: ${nuevoRegistro.numero_cuenta.trim()}`,
          {
            registro_id: registroCreado.id,
            numero_cuenta: nuevoRegistro.numero_cuenta.trim(),
            cantidad_clasificaciones: Object.keys(nuevoRegistro.clasificaciones).length,
            clasificaciones: nuevoRegistro.clasificaciones,
            source_type: "persistent_db"
          }
        );
      } catch (logErr) {
        console.warn("Error registrando actividad de creación de registro:", logErr);
      }
      
      console.log('✅ Registro persistente creado exitosamente');
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
      // Obtener datos del registro actual para el log
      const registroActual = registros.find(r => r.id === editandoId);
      const datosAnteriores = registroActual ? {
        numero_cuenta_anterior: registroActual.numero_cuenta,
        clasificaciones_anteriores: registroActual.clasificaciones
      } : {};
      
      if (!registroActual) {
        throw new Error('No se encontró el registro a editar');
      }
      
      await actualizarClasificacionPersistente(registroActual.numero_cuenta, {
        cliente: clienteId,
        nuevo_numero_cuenta: registroEditando.numero_cuenta.trim(),
        cuenta_nombre: registroEditando.numero_cuenta.trim(),
        clasificaciones: registroEditando.clasificaciones
      });
      
      // Registrar actividad detallada de edición de registro
      try {
        await registrarActividad(
          "clasificacion",
          "individual_edit",
          `Editó registro persistente desde modal: ${registroEditando.numero_cuenta.trim()}`,
          {
            registro_id: editandoId,
            numero_cuenta_nuevo: registroEditando.numero_cuenta.trim(),
            cantidad_clasificaciones_nueva: Object.keys(registroEditando.clasificaciones).length,
            clasificaciones_nuevas: registroEditando.clasificaciones,
            ...datosAnteriores
          }
        );
      } catch (logErr) {
        console.warn("Error registrando actividad de edición de registro:", logErr);
      }
      
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
        // Obtener datos del registro antes de eliminar para el log
        const registroAEliminar = registros.find(r => r.id === id);
        const datosEliminado = registroAEliminar ? {
          numero_cuenta: registroAEliminar.numero_cuenta,
          clasificaciones: registroAEliminar.clasificaciones,
          cantidad_clasificaciones: Object.keys(registroAEliminar.clasificaciones || {}).length
        } : {};
        
        if (!registroAEliminar) {
          throw new Error('No se encontró el registro a eliminar');
        }
        
        await eliminarClasificacionPersistente(registroAEliminar.numero_cuenta, clienteId);
        
        // Registrar actividad detallada de eliminación de registro
        try {
          await registrarActividad(
            "clasificacion",
            "individual_delete",
            `Eliminó registro de clasificación desde modal: ${datosEliminado.numero_cuenta || 'N/A'}`,
            {
              registro_id: id,
              ...datosEliminado
            }
          );
        } catch (logErr) {
          console.warn("Error registrando actividad de eliminación de registro:", logErr);
        }
        
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
    setTextoBusquedaMasiva(''); // Limpiar búsqueda al cambiar modo
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
    console.log('🚀 Iniciando aplicación de clasificación masiva:', {
      setMasivo,
      opcionMasiva,
      registrosSeleccionados: Array.from(registrosSeleccionados),
      cantidadRegistros: registrosSeleccionados.size
    });

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

    console.log('✅ Validaciones pasadas, aplicando clasificación:', {
      setNombre: setEncontrado.nombre,
      opcionValor: opcionMasiva,
      registrosAfectados: registrosSeleccionados.size
    });

    setAplicandoClasificacionMasiva(true);

    try {
      // Como no existe endpoint de bulk para archivo, actualizamos individualmente
      const registroIds = Array.from(registrosSeleccionados);
      console.log('🔄 Aplicando clasificación individual a cada registro...');
      
      let registrosActualizados = 0;
      let errores = [];
      
      for (const registroId of registroIds) {
        try {
          // Encontrar el registro actual
          const registroActual = registros.find(r => r.id === registroId);
          if (!registroActual) {
            errores.push(`Registro ${registroId} no encontrado`);
            continue;
          }
          
          // Crear nuevas clasificaciones agregando la clasificación masiva
          const nuevasClasificaciones = {
            ...registroActual.clasificaciones,
            [setEncontrado.nombre]: opcionMasiva
          };
          
          // Actualizar el registro individual usando el código de cuenta
          await actualizarClasificacionPersistente(registroActual.numero_cuenta, {
            cliente: clienteId,
            numero_cuenta: registroActual.numero_cuenta,
            cuenta_nombre: registroActual.cuenta_nombre,
            clasificaciones: nuevasClasificaciones
          });
          
          registrosActualizados++;
          console.log(`✅ Registro ${registroActual.numero_cuenta} actualizado`);
          
        } catch (errorRegistro) {
          console.error(`❌ Error actualizando registro ${registroId}:`, errorRegistro);
          errores.push(`Error en registro ${registroId}: ${errorRegistro.message}`);
        }
      }
      
      console.log('✅ Clasificación masiva completada:', {
        registros_actualizados: registrosActualizados,
        errores: errores.length,
        set_nombre: setEncontrado.nombre,
        valor_aplicado: opcionMasiva
      });
      
      // Registrar actividad detallada de clasificación masiva
      try {
        const registrosAfectados = Array.from(registrosSeleccionados).map(id => {
          const registro = registros.find(r => r.id === id);
          return registro ? registro.numero_cuenta : `ID:${id}`;
        });
        
        await registrarActividad(
          "clasificacion",
          "bulk_classify",
          `Aplicó clasificación masiva en archivo (individual) desde modal: ${setEncontrado.nombre} = ${opcionMasiva} a ${registrosActualizados} registros`,
          {
            set_nombre: setEncontrado.nombre,
            set_id: setEncontrado.id,
            opcion_aplicada: opcionMasiva,
            cantidad_registros_solicitados: registrosSeleccionados.size,
            cantidad_registros_actualizados: registrosActualizados,
            cantidad_errores: errores.length,
            registros_afectados: registrosAfectados,
            registros_ids: Array.from(registrosSeleccionados),
            errores_detalle: errores,
            source_type: "archivo",
            metodo: "individual_updates"
          }
        );
      } catch (logErr) {
        console.warn("Error registrando actividad de clasificación masiva:", logErr);
      }
      
      // Recargar datos y limpiar selección
      await cargarRegistros();
      setRegistrosSeleccionados(new Set());
      setSetMasivo('');
      setOpcionMasiva('');
      setModoClasificacionMasiva(false);
      
      if (onDataChanged) onDataChanged();
      
      // Mostrar mensaje con resultados
      if (errores.length === 0) {
        alert(`Clasificación aplicada exitosamente a ${registrosActualizados} registros`);
      } else {
        alert(`Clasificación aplicada a ${registrosActualizados} registros. ${errores.length} errores encontrados. Ver consola para detalles.`);
        console.warn('Errores en clasificación masiva:', errores);
      }
    } catch (error) {
      console.error("❌ Error aplicando clasificación masiva:", error);
      console.error("Error details:", {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        endpoint: error.config?.url
      });
      
      let errorMessage = "Error al aplicar la clasificación masiva";
      if (error.response?.data?.error) {
        errorMessage += `: ${error.response.data.error}`;
      } else if (error.response?.data?.detail) {
        errorMessage += `: ${error.response.data.detail}`;
      }
      
      alert(errorMessage);
    } finally {
      setAplicandoClasificacionMasiva(false);
    }
  };

  // ==================== FUNCIONES PARA PEGADO MASIVO EN CLASIFICACIÓN MASIVA ====================
  const procesarTextoPegadoClasificacionMasiva = (texto) => {
    console.log('🔄 Procesando texto pegado para clasificación masiva:', texto);
    
    // Dividir por líneas y limpiar
    const lineas = texto.split(/[\r\n]+/).map(linea => linea.trim()).filter(linea => linea.length > 0);
    
    console.log('📋 Líneas detectadas para búsqueda:', lineas);
    
    // Buscar registros que coincidan con las cuentas pegadas
    const registrosEncontrados = [];
    const cuentasNoEncontradas = [];
    
    lineas.forEach(cuentaPegada => {
      const registroEncontrado = registrosFiltrados.find(r => 
        r.numero_cuenta.toLowerCase().includes(cuentaPegada.toLowerCase()) ||
        cuentaPegada.toLowerCase().includes(r.numero_cuenta.toLowerCase()) ||
        r.numero_cuenta === cuentaPegada
      );
      
      if (registroEncontrado) {
        registrosEncontrados.push(registroEncontrado);
      } else {
        cuentasNoEncontradas.push(cuentaPegada);
      }
    });
    
    console.log('🎯 Resultados búsqueda:', {
      total_lineas: lineas.length,
      encontrados: registrosEncontrados.length,
      no_encontrados: cuentasNoEncontradas.length
    });
    
    return {
      lineasOriginales: lineas,
      registrosEncontrados,
      cuentasNoEncontradas,
      totalLineas: lineas.length
    };
  };

  const handleTextoPegadoClasificacionMasiva = (texto) => {
    const resultado = procesarTextoPegadoClasificacionMasiva(texto);
    
    if (resultado.totalLineas > 1) {
      // Es pegado masivo
      console.log('✅ Detectado pegado masivo en clasificación masiva');
      
      let mensaje = `📋 Detectadas ${resultado.totalLineas} cuentas:\n\n`;
      mensaje += `✅ ${resultado.registrosEncontrados.length} cuentas encontradas y se seleccionarán\n`;
      
      if (resultado.cuentasNoEncontradas.length > 0) {
        mensaje += `❌ ${resultado.cuentasNoEncontradas.length} cuentas no encontradas:\n`;
        mensaje += resultado.cuentasNoEncontradas.slice(0, 10).join('\n');
        if (resultado.cuentasNoEncontradas.length > 10) {
          mensaje += `\n... y ${resultado.cuentasNoEncontradas.length - 10} más`;
        }
        mensaje += '\n\n';
      }
      
      mensaje += '¿Continuar con la selección de las cuentas encontradas?';
      
      if (confirm(mensaje)) {
        // Seleccionar todos los registros encontrados
        const idsEncontrados = new Set(resultado.registrosEncontrados.map(r => r.id));
        setRegistrosSeleccionados(idsEncontrados);
        
        // Limpiar el campo de búsqueda
        setTextoBusquedaMasiva('');
        
        // Mostrar resumen
        console.log(`✅ Seleccionados ${idsEncontrados.size} registros automáticamente`);
        
        // Registrar actividad
        try {
          registrarActividad(
            "clasificacion",
            "bulk_selection_paste",
            `Selección masiva por pegado: ${idsEncontrados.size} cuentas`,
            {
              total_pegadas: resultado.totalLineas,
              encontradas: resultado.registrosEncontrados.length,
              no_encontradas: resultado.cuentasNoEncontradas.length,
              cuentas_seleccionadas: resultado.registrosEncontrados.map(r => r.numero_cuenta)
            }
          );
        } catch (logErr) {
          console.warn("Error registrando actividad de selección masiva:", logErr);
        }
      }
    } else {
      // Búsqueda individual - mantener comportamiento original
      const cuentaBuscada = resultado.lineasOriginales[0] || '';
      setTextoBusquedaMasiva(cuentaBuscada);
      
      // Auto-seleccionar si encuentra exactamente una coincidencia
      if (resultado.registrosEncontrados.length === 1) {
        const registroEncontrado = resultado.registrosEncontrados[0];
        const nuevosSeleccionados = new Set(registrosSeleccionados);
        
        if (nuevosSeleccionados.has(registroEncontrado.id)) {
          console.log('ℹ️ Cuenta ya estaba seleccionada');
        } else {
          nuevosSeleccionados.add(registroEncontrado.id);
          setRegistrosSeleccionados(nuevosSeleccionados);
          console.log(`✅ Auto-seleccionada cuenta: ${registroEncontrado.numero_cuenta}`);
        }
      }
    }
  };

  const buscarYSeleccionarCuentas = (textoBusqueda) => {
    if (!textoBusqueda.trim()) {
      return;
    }
    
    const busquedaLimpia = textoBusqueda.toLowerCase().trim();
    const registrosCoincidentes = registrosFiltrados.filter(r => 
      r.numero_cuenta.toLowerCase().includes(busquedaLimpia)
    );
    
    if (registrosCoincidentes.length > 0) {
      const idsCoincidentes = new Set(registrosCoincidentes.map(r => r.id));
      const nuevosSeleccionados = new Set([...registrosSeleccionados, ...idsCoincidentes]);
      setRegistrosSeleccionados(nuevosSeleccionados);
      
      console.log(`🔍 Búsqueda "${textoBusqueda}": ${registrosCoincidentes.length} cuentas agregadas a selección`);
      
      // Limpiar búsqueda después de seleccionar
      setTextoBusquedaMasiva('');
    } else {
      console.log(`🔍 Búsqueda "${textoBusqueda}": Sin coincidencias`);
    }
  };

  const registrosFiltrados = aplicarFiltros(registros || []);
  // Mostrar todos los sets definidos por el cliente, no solo los presentes en los registros
  const setsUnicos = sets.map(s => s.nombre).sort();

  // --- Paginación ---
  const PAGE_SIZE = 20;
  const [paginaActual, setPaginaActual] = useState(1);
  const totalPaginas = Math.max(1, Math.ceil(registrosFiltrados.length / PAGE_SIZE));
  const paginaSegura = Math.min(paginaActual, totalPaginas);
  const inicio = (paginaSegura - 1) * PAGE_SIZE;
  const fin = inicio + PAGE_SIZE;
  const registrosPagina = registrosFiltrados.slice(inicio, fin);

  // Reset de página cuando cambian filtros o cantidad
  useEffect(() => {
    setPaginaActual(1);
  }, [filtros, registrosFiltrados.length]);

  if (!isOpen) {
    console.log("🚫 Modal no se abre - isOpen:", isOpen);
    return null;
  }

  console.log("✅ Modal se está abriendo");
  console.log("📋 Props recibidas:", { isOpen, uploadId, clienteId });

  return (
    <div className="fixed inset-0 z-50 flex justify-center items-center p-4 backdrop-blur-sm bg-black/70">
      <div 
        className="relative w-full flex flex-col overflow-hidden rounded-xl border border-gray-700/70 shadow-2xl bg-gradient-to-br from-gray-900 via-gray-900/95 to-gray-950"
        style={{ maxWidth: '95vw', height: '90vh', width: '1200px' }}
      >
        <div className="absolute inset-0 pointer-events-none opacity-40 mix-blend-overlay" style={{backgroundImage:'radial-gradient(circle at 25% 15%, rgba(120,119,198,0.15), transparent 60%)'}} />
        {/* Header del modal */}
        <div className="flex justify-between items-center p-6 border-b border-gray-700 bg-gray-900">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-semibold text-white flex items-center gap-2">
              <Database size={20} />
              Gestión de Clasificaciones
              {creandoMasivo && (
                <span className="bg-green-600 text-green-100 px-2 py-1 rounded text-sm font-medium">
                  Creación Masiva: {cuentasMasivas.length} cuentas
                </span>
              )}
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
            onClick={handleClose}
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
                      title="Crear nuevo registro individual o pegar múltiples cuentas desde Excel"
                    >
                      <Plus size={16} />
                      Nuevo Registro
                      <span className="text-xs text-blue-200 ml-1">(o pegar Excel)</span>
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
                    <div className="mt-5 border-t border-gray-700/60 pt-4">
                      <div className="flex items-center gap-3 mb-3">
                        <label className="text-[11px] tracking-wide uppercase text-gray-400 font-semibold">Filtrar por sets</label>
                        {filtros.setsSeleccionados.length > 0 && (
                          <button
                            onClick={() => setFiltros(prev => ({ ...prev, setsSeleccionados: [] }))}
                            className="text-xs text-blue-300 hover:text-blue-200 underline decoration-dotted"
                          >
                            Deseleccionar todos
                          </button>
                        )}
                        {filtros.setsSeleccionados.length !== setsUnicos.length && (
                          <button
                            onClick={() => setFiltros(prev => ({ ...prev, setsSeleccionados: [...setsUnicos] }))}
                            className="text-xs text-blue-300 hover:text-blue-200 underline decoration-dotted"
                          >
                            Seleccionar todos
                          </button>
                        )}
                      </div>
                      <div className="flex flex-wrap gap-2 max-h-40 overflow-auto pr-1 custom-scrollbar">
                        {setsUnicos.map(setNombre => {
                          const activo = filtros.setsSeleccionados.includes(setNombre);
                          return (
                            <button
                              type="button"
                              key={setNombre}
                              onClick={() => {
                                setFiltros(prev => ({
                                  ...prev,
                                  setsSeleccionados: activo 
                                    ? prev.setsSeleccionados.filter(s => s !== setNombre)
                                    : [...prev.setsSeleccionados, setNombre]
                                }));
                              }}
                              className={`group relative flex items-center gap-1 rounded-full px-3 py-1.5 text-xs font-medium transition
                                ${activo
                                  ? 'bg-blue-600/20 text-blue-300 border border-blue-500/40 shadow-inner'
                                  : 'bg-gray-700/70 text-gray-300 border border-gray-600 hover:bg-gray-600/60'}
                              `}
                            >
                              <span className="font-semibold tracking-wide">{setNombre}</span>
                              {activo && (
                                <span className="inline-block w-1.5 h-1.5 rounded-full bg-blue-400 shadow shadow-blue-400/40" />
                              )}
                            </button>
                          );
                        })}
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
                  
                  {/* Campo de búsqueda/pegado masivo */}
                  <div className="mb-4 p-3 bg-gray-700/50 rounded border border-gray-600">
                    <label className="block text-xs text-gray-400 mb-2">
                      🔍 Buscar/Seleccionar cuentas:
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={textoBusquedaMasiva}
                        onChange={(e) => setTextoBusquedaMasiva(e.target.value)}
                        onPaste={(e) => {
                          e.preventDefault();
                          const textoPegado = e.clipboardData.getData('text');
                          handleTextoPegadoClasificacionMasiva(textoPegado);
                        }}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            buscarYSeleccionarCuentas(textoBusquedaMasiva);
                          }
                        }}
                        placeholder="Buscar cuenta individual o pegar múltiples cuentas de Excel..."
                        className="flex-1 bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 text-sm focus:border-green-500 focus:outline-none"
                      />
                      <button
                        onClick={() => buscarYSeleccionarCuentas(textoBusquedaMasiva)}
                        disabled={!textoBusquedaMasiva.trim()}
                        className="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 disabled:opacity-50 text-white px-3 py-2 rounded text-sm transition flex items-center gap-1"
                        title="Buscar y seleccionar"
                      >
                        <Plus size={14} />
                        Buscar
                      </button>
                    </div>
                    <div className="mt-2 text-xs text-gray-400">
                      💡 <strong>Tip:</strong> Pega varias cuentas de Excel (una por línea) para seleccionarlas automáticamente
                    </div>
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
                          title="Seleccionar todos los registros visibles"
                        >
                          Todos
                        </button>
                        <button
                          onClick={limpiarSeleccionRegistros}
                          className="bg-gray-600 hover:bg-gray-500 text-white px-3 py-2 rounded text-sm transition"
                          disabled={registrosSeleccionados.size === 0}
                          title="Limpiar selección"
                        >
                          Limpiar
                        </button>
                      </div>
                    </div>
                    
                    {/* Botón aplicar */}
                    <div>
                      <button
                        onClick={aplicarClasificacionMasiva}
                        disabled={!setMasivo || !opcionMasiva || registrosSeleccionados.size === 0 || aplicandoClasificacionMasiva}
                        className="w-full bg-green-600 hover:bg-green-500 disabled:bg-gray-600 disabled:opacity-50 text-white px-4 py-2 rounded font-medium transition"
                      >
                        {aplicandoClasificacionMasiva ? 'Aplicando...' : `Aplicar (${registrosSeleccionados.size})`}
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
                  
                  {/* Indicador de estado de selección */}
                  {registrosSeleccionados.size > 0 && (
                    <div className="mt-3 p-2 bg-blue-900/20 border border-blue-700/50 rounded text-xs">
                      <span className="text-blue-400">📋 Seleccionados:</span>{' '}
                      <span className="font-medium text-white">{registrosSeleccionados.size}</span> de{' '}
                      <span className="text-gray-300">{registrosFiltrados.length}</span> registros visibles
                      {textoBusquedaMasiva && (
                        <span className="text-yellow-400 ml-2">
                          (búsqueda activa: "{textoBusquedaMasiva}")
                        </span>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Tabla */}
              <div className="bg-gray-800 rounded-lg border border-gray-700 flex flex-col overflow-hidden">
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
                  <div className="relative flex-1 flex flex-col">
                    <div className="flex-1 overflow-auto custom-scrollbar" style={{maxHeight:'42vh'}}>
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
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider border-b border-gray-700">Cuenta</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider border-b border-gray-700">Nombre (ES)</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider border-b border-gray-700">Nombre (EN)</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider border-b border-gray-700">Clasificaciones</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider border-b border-gray-700">
                          Acciones
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-gray-900 divide-y divide-gray-700">
                      {/* Sección de creación masiva */}
                      {creandoMasivo && (
                        <>
                          {/* Encabezado de creación masiva */}
                          <tr className="bg-green-900/20 border-l-4 border-l-green-500">
                            <td colSpan={modoClasificacionMasiva ? 6 : 5} className="px-3 py-4">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                  <div className="flex items-center gap-2">
                                    <FolderPlus size={20} className="text-green-400" />
                                    <h3 className="text-green-400 font-medium">
                                      Creación Masiva: {cuentasMasivas.length} cuentas detectadas
                                    </h3>
                                  </div>
                                  
                                  {/* Panel de clasificación masiva para cuentas */}
                                  <div className="flex items-center gap-2 ml-6">
                                    <span className="text-xs text-gray-400">Aplicar a todas:</span>
                                    <select
                                      value={setMasivo}
                                      onChange={(e) => {
                                        setSetMasivo(e.target.value);
                                        setOpcionMasiva('');
                                      }}
                                      className="bg-gray-700 text-white px-2 py-1 rounded border border-gray-600 text-xs focus:border-green-500 focus:outline-none"
                                    >
                                      <option value="">Set...</option>
                                      {obtenerSetsDisponibles().map(set => (
                                        <option key={set.id} value={set.id}>{set.nombre}</option>
                                      ))}
                                    </select>
                                    
                                    {setMasivo && (
                                      <select
                                        value={opcionMasiva}
                                        onChange={(e) => setOpcionMasiva(e.target.value)}
                                        className="bg-gray-700 text-white px-2 py-1 rounded border border-gray-600 text-xs focus:border-green-500 focus:outline-none"
                                      >
                                        <option value="">Opción...</option>
                                        {obtenerOpcionesParaSet(setMasivo).map(opcion => (
                                          <option key={opcion.id} value={opcion.valor}>{opcion.valor}</option>
                                        ))}
                                      </select>
                                    )}
                                    
                                    {setMasivo && opcionMasiva && (
                                      <button
                                        onClick={aplicarClasificacionMasivaACuentas}
                                        className="bg-green-600 hover:bg-green-500 px-2 py-1 rounded text-white text-xs transition flex items-center gap-1"
                                        title="Aplicar a todas las cuentas"
                                      >
                                        <Plus size={12} />
                                        Aplicar
                                      </button>
                                    )}
                                  </div>
                                </div>
                                
                                <div className="flex gap-2">
                                  <button
                                    onClick={handleGuardarCreacionMasiva}
                                    disabled={aplicandoCreacionMasiva}
                                    className="bg-green-600 hover:bg-green-500 disabled:bg-gray-600 text-white px-3 py-1 rounded text-sm font-medium transition flex items-center gap-1"
                                  >
                                    {aplicandoCreacionMasiva ? (
                                      <>
                                        <Clock size={14} className="animate-spin" />
                                        Creando...
                                      </>
                                    ) : (
                                      <>
                                        <Save size={14} />
                                        Crear Todas ({cuentasMasivas.length})
                                      </>
                                    )}
                                  </button>
                                  <button
                                    onClick={handleCancelarCreacionMasiva}
                                    disabled={aplicandoCreacionMasiva}
                                    className="bg-gray-600 hover:bg-gray-500 disabled:bg-gray-700 text-white px-3 py-1 rounded text-sm transition flex items-center gap-1"
                                  >
                                    <XCircle size={14} />
                                    Cancelar
                                  </button>
                                </div>
                              </div>
                            </td>
                          </tr>
                          
                          {/* Lista de cuentas masivas */}
              {cuentasMasivas.map((cuenta, index) => (
                            <tr key={`masiva-${index}`} className="bg-green-900/10 hover:bg-green-900/20 transition">
                              {modoClasificacionMasiva && (
                                <td className="px-3 py-2">
                                  {/* Sin checkbox para cuentas masivas */}
                                </td>
                              )}
                <td className="px-3 py-2" colSpan={2}>
                                <div className="font-mono text-sm text-green-300">
                                  {cuenta.numero_cuenta}
                                </div>
                              </td>
                <td className="px-3 py-2" colSpan={2}>
                                {/* Clasificaciones de la cuenta */}
                                {Object.keys(cuenta.clasificaciones).length > 0 ? (
                                  <div className="flex flex-wrap gap-1">
                                    {Object.entries(cuenta.clasificaciones).map(([set, valor]) => (
                                      <div key={set} className="flex items-center gap-1 bg-green-900/50 px-2 py-1 rounded text-xs border border-green-700/50">
                                        <span className="text-green-300 font-medium">{set}:</span>
                                        <span className="text-white">{valor}</span>
                                        <button
                                          onClick={() => removerClasificacionDeCuentaMasiva(index, set)}
                                          className="text-red-400 hover:text-red-300 ml-1 hover:bg-red-900/30 rounded p-0.5 transition"
                                          title="Eliminar clasificación"
                                        >
                                          <XCircle size={10} />
                                        </button>
                                      </div>
                                    ))}
                                  </div>
                                ) : (
                                  <div className="text-xs text-yellow-400 italic">
                                    Sin clasificaciones
                                  </div>
                                )}
                              </td>
                              <td className="px-3 py-2">
                                <div className="text-xs text-gray-500">
                                  Cuenta #{index + 1}
                                </div>
                              </td>
                            </tr>
                          ))}
                        </>
                      )}
                      
                      {/* Fila de creación de nuevo registro */}
                      {creandoNuevo && (
                        <>
                          {/* Fila informativa */}
                          <tr className="bg-blue-900/20">
                            <td colSpan={modoClasificacionMasiva ? 6 : 5} className="px-3 py-2 text-center">
                              <div className="text-xs text-blue-400 bg-blue-900/30 px-3 py-2 rounded border border-blue-700/50 inline-block">
                                💡 <strong>Tip:</strong> Puedes pegar varias cuentas de Excel (una por línea) en el campo "Número de cuenta" para crearlas masivamente
                              </div>
                            </td>
                          </tr>
                          
                          <tr className="bg-gray-800 border-l-4 border-l-blue-500">
                          {modoClasificacionMasiva && (
                            <td className="px-3 py-2">
                              {/* Sin checkbox para fila de creación */}
                            </td>
                          )}
                          <td className="px-3 py-2" colSpan={2}>
                            {(() => {
                              const cuentaExiste = nuevoRegistro.numero_cuenta.trim() && 
                                                 registros.some(r => r.numero_cuenta === nuevoRegistro.numero_cuenta.trim());
                              return (
                                <div>
                                  <input
                                    type="text"
                                    value={nuevoRegistro.numero_cuenta}
                                    onChange={(e) => setNuevoRegistro(prev => ({ ...prev, numero_cuenta: e.target.value }))}
                                    onPaste={(e) => {
                                      e.preventDefault();
                                      const textoPegado = e.clipboardData.getData('text');
                                      handleTextoPegado(textoPegado);
                                    }}
                                    placeholder="Número de cuenta (o pega varias líneas desde Excel)"
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
                          <td className="px-3 py-2" colSpan={2}>
                            {/* Clasificaciones agregadas */}
                            {Object.keys(nuevoRegistro.clasificaciones).length > 0 && (
                              <div className="mb-2">
                                <div className="flex flex-wrap gap-1">
                                  {Object.entries(nuevoRegistro.clasificaciones || {})
                                    .filter(([set, valor]) => set !== 'undefined' && set && valor)
                                    .map(([set, valor]) => (
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
                        </>
                      )}
                      
                      {/* Filas de registros existentes */}
                      {registrosPagina.map((registro) => (
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
                          <td className="px-3 py-2 align-top">
                            {editandoId === registro.id ? (
                              <input
                                type="text"
                                value={registroEditando.numero_cuenta}
                                onChange={(e) => setRegistroEditando(prev => ({ ...prev, numero_cuenta: e.target.value }))}
                                className="w-full bg-gray-700 text-white px-2 py-1 rounded border border-gray-600 focus:border-blue-500 focus:outline-none font-mono"
                              />
                            ) : (
                              <div className="flex flex-col">
                                <span className="text-white font-mono text-sm">{registro.numero_cuenta}</span>
                                {!registro.cuenta_existe && (
                                  <span className="text-[10px] text-yellow-400 mt-0.5">(temporal)</span>
                                )}
                              </div>
                            )}
                          </td>
                          <td className="px-3 py-2 align-top text-xs text-gray-300 max-w-[200px]">
                            <div className="whitespace-pre-line leading-snug">
                              {registro.cuenta_nombre || <span className="text-gray-600 italic">—</span>}
                            </div>
                          </td>
                          <td className="px-3 py-2 align-top text-xs text-gray-300 max-w-[200px]">
                            <div className="whitespace-pre-line leading-snug">
                              {registro.cuenta_nombre_en ? (
                                registro.cuenta_nombre_en
                              ) : (
                                <span className="text-gray-600 italic">{cliente?.bilingue ? 'sin inglés' : '—'}</span>
                              )}
                            </div>
                          </td>
                          <td className="px-3 py-2">
                            {editandoId === registro.id ? (
                              <div>
                                {/* Clasificaciones agregadas */}
                                {Object.keys(registroEditando.clasificaciones).length > 0 && (
                                  <div className="mb-2">
                                    <div className="flex flex-wrap gap-1">
                                      {Object.entries(registroEditando.clasificaciones || {})
                                        .filter(([set, valor]) => set !== 'undefined' && set && valor)
                                        .map(([set, valor]) => (
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
                                {Object.entries(registro.clasificaciones || {})
                                  .filter(([set, valor]) => set !== 'undefined' && set && valor)
                                  .map(([set, valor]) => (
                                  <span key={set} className="inline-block bg-blue-900/50 px-2 py-1 rounded text-xs">
                                    <span className="text-gray-300">{set}:</span> <span className="text-white">{valor}</span>
                                  </span>
                                ))}
                                {Object.keys(registro.clasificaciones || {}).length === 0 && (
                                  <span className="text-gray-400 text-xs italic">Sin clasificaciones</span>
                                )}
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
                    </div>
                    {/* Footer paginación */}
                    <div className="flex items-center justify-between gap-4 px-4 py-2 bg-gray-900/80 border-t border-gray-700 text-xs">
                      <div className="text-gray-400">
                        Página <span className="text-white font-medium">{paginaSegura}</span> de <span className="text-white font-medium">{totalPaginas}</span>
                        <span className="ml-3 text-gray-500">Mostrando {registrosPagina.length} de {registrosFiltrados.length}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setPaginaActual(1)}
                          disabled={paginaSegura === 1}
                          className="px-2 py-1 rounded bg-gray-700 disabled:bg-gray-800 disabled:text-gray-600 hover:bg-gray-600 text-gray-200"
                        >«</button>
                        <button
                          onClick={() => setPaginaActual(p => Math.max(1, p-1))}
                          disabled={paginaSegura === 1}
                          className="px-2 py-1 rounded bg-gray-700 disabled:bg-gray-800 disabled:text-gray-600 hover:bg-gray-600 text-gray-200"
                        >‹</button>
                        <input
                          type="number"
                          min={1}
                          max={totalPaginas}
                          value={paginaSegura}
                          onChange={e => {
                            const v = parseInt(e.target.value,10);
                            if(!isNaN(v)) setPaginaActual(Math.min(Math.max(1,v), totalPaginas));
                          }}
                          className="w-14 bg-gray-800 border border-gray-600 rounded px-2 py-1 text-center text-gray-200 focus:outline-none focus:border-blue-500"
                        />
                        <button
                          onClick={() => setPaginaActual(p => Math.min(totalPaginas, p+1))}
                          disabled={paginaSegura === totalPaginas}
                          className="px-2 py-1 rounded bg-gray-700 disabled:bg-gray-800 disabled:text-gray-600 hover:bg-gray-600 text-gray-200"
                        >›</button>
                        <button
                          onClick={() => setPaginaActual(totalPaginas)}
                          disabled={paginaSegura === totalPaginas}
                          className="px-2 py-1 rounded bg-gray-700 disabled:bg-gray-800 disabled:text-gray-600 hover:bg-gray-600 text-gray-200"
                        >»</button>
                      </div>
                    </div>
                  </div>
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
                                    <label className="block text-xs text-gray-400 mb-2">
                                      Modo de creación: 
                                      <span className="ml-2 text-blue-400 font-medium">
                                        {modoCreacionOpcion === 'es' && '🇪🇸 Solo Español'}
                                        {modoCreacionOpcion === 'en' && '🇺🇸 Solo Inglés'}
                                        {modoCreacionOpcion === 'ambos' && '🌐 Bilingüe (Recomendado)'}
                                      </span>
                                    </label>
                                    <div className="flex gap-2">
                                      <button
                                        onClick={() => {
                                          console.log('📝 Cambiando modo a: Solo Español');
                                          setModoCreacionOpcion('es');
                                        }}
                                        className={`px-3 py-1 rounded text-sm transition ${
                                          modoCreacionOpcion === 'es' 
                                            ? 'bg-blue-600 text-white shadow-lg ring-2 ring-blue-400' 
                                            : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                                        }`}
                                      >
                                        🇪🇸 Solo Español
                                      </button>
                                      <button
                                        onClick={() => {
                                          console.log('📝 Cambiando modo a: Solo Inglés');
                                          setModoCreacionOpcion('en');
                                        }}
                                        className={`px-3 py-1 rounded text-sm transition ${
                                          modoCreacionOpcion === 'en' 
                                            ? 'bg-green-600 text-white shadow-lg ring-2 ring-green-400' 
                                            : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                                        }`}
                                      >
                                        🇺🇸 Solo Inglés
                                      </button>
                                      <button
                                        onClick={() => {
                                          console.log('📝 Cambiando modo a: Bilingüe');
                                          setModoCreacionOpcion('ambos');
                                        }}
                                        className={`px-3 py-1 rounded text-sm transition ${
                                          modoCreacionOpcion === 'ambos' 
                                            ? 'bg-purple-600 text-white shadow-lg ring-2 ring-purple-400' 
                                            : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                                        }`}
                                      >
                                        🌐 Bilingüe
                                      </button>
                                    </div>
                                  </div>
                                )}
                                
                                {/* Indicador para clientes no bilingües */}
                                {!cliente?.bilingue && (
                                  <div className="mb-3">
                                    <div className="text-xs text-gray-400 flex items-center gap-2">
                                      <span className="bg-blue-600 text-white px-2 py-1 rounded text-xs">🇪🇸 Español</span>
                                      <span>Cliente configurado para español únicamente</span>
                                    </div>
                                  </div>
                                )}
                                
                                {/* Campos de entrada según el modo */}
                                <div className="space-y-3">
                                  {(modoCreacionOpcion === 'es' || modoCreacionOpcion === 'ambos') && (
                                    <div className="space-y-2">
                                      <div className="flex items-center gap-2">
                                        <span className="text-xs text-gray-400">🇪🇸 Español</span>
                                        {modoCreacionOpcion === 'ambos' && (
                                          <span className="text-xs text-red-400">*Requerido</span>
                                        )}
                                      </div>
                                      <input
                                        type="text"
                                        value={nuevaOpcionBilingue.es}
                                        onChange={(e) => setNuevaOpcionBilingue(prev => ({ ...prev, es: e.target.value }))}
                                        placeholder={`Valor en Español${modoCreacionOpcion === 'ambos' ? ' *' : ''}`}
                                        className={`w-full text-white px-3 py-2 rounded border text-sm transition ${
                                          modoCreacionOpcion === 'ambos' && !nuevaOpcionBilingue.es.trim()
                                            ? 'bg-red-900/20 border-red-500 focus:border-red-400'
                                            : 'bg-gray-800 border-gray-600 focus:border-blue-500'
                                        }`}
                                        onKeyPress={(e) => e.key === 'Enter' && handleCrearOpcion(set.id)}
                                        autoFocus={modoCreacionOpcion === 'es'}
                                      />
                                      <input
                                        type="text"
                                        value={nuevaOpcionBilingue.descripcion_es}
                                        onChange={(e) => setNuevaOpcionBilingue(prev => ({ ...prev, descripcion_es: e.target.value }))}
                                        placeholder="Descripción en Español (opcional)"
                                        className="w-full bg-gray-800 text-white px-3 py-2 rounded border border-gray-600 text-xs focus:border-blue-500 transition"
                                      />
                                    </div>
                                  )}
                                  
                                  {(modoCreacionOpcion === 'en' || modoCreacionOpcion === 'ambos') && (
                                    <div className="space-y-2">
                                      <div className="flex items-center gap-2">
                                        <span className="text-xs text-gray-400">🇺🇸 English</span>
                                        {modoCreacionOpcion === 'ambos' && (
                                          <span className="text-xs text-red-400">*Required</span>
                                        )}
                                      </div>
                                      <input
                                        type="text"
                                        value={nuevaOpcionBilingue.en}
                                        onChange={(e) => setNuevaOpcionBilingue(prev => ({ ...prev, en: e.target.value }))}
                                        placeholder={`English Value${modoCreacionOpcion === 'ambos' ? ' *' : ''}`}
                                        className={`w-full text-white px-3 py-2 rounded border text-sm transition ${
                                          modoCreacionOpcion === 'ambos' && !nuevaOpcionBilingue.en.trim()
                                            ? 'bg-red-900/20 border-red-500 focus:border-red-400'
                                            : 'bg-gray-800 border-gray-600 focus:border-green-500'
                                        }`}
                                        onKeyPress={(e) => e.key === 'Enter' && handleCrearOpcion(set.id)}
                                        autoFocus={modoCreacionOpcion === 'en'}
                                      />
                                      <input
                                        type="text"
                                        value={nuevaOpcionBilingue.descripcion_en}
                                        onChange={(e) => setNuevaOpcionBilingue(prev => ({ ...prev, descripcion_en: e.target.value }))}
                                        placeholder="English Description (optional)"
                                        className="w-full bg-gray-800 text-white px-3 py-2 rounded border border-gray-600 text-xs focus:border-green-500 transition"
                                      />
                                    </div>
                                  )}
                                </div>
                                
                                {/* Botones de acción */}
                                <div className="flex gap-2 mt-4">
                                  <button
                                    onClick={() => handleCrearOpcion(set.id)}
                                    disabled={
                                      (modoCreacionOpcion === 'es' && !nuevaOpcionBilingue.es.trim()) ||
                                      (modoCreacionOpcion === 'en' && !nuevaOpcionBilingue.en.trim()) ||
                                      (modoCreacionOpcion === 'ambos' && (!nuevaOpcionBilingue.es.trim() || !nuevaOpcionBilingue.en.trim()))
                                    }
                                    className={`px-4 py-2 rounded text-sm font-medium transition flex items-center gap-2 ${
                                      (modoCreacionOpcion === 'es' && !nuevaOpcionBilingue.es.trim()) ||
                                      (modoCreacionOpcion === 'en' && !nuevaOpcionBilingue.en.trim()) ||
                                      (modoCreacionOpcion === 'ambos' && (!nuevaOpcionBilingue.es.trim() || !nuevaOpcionBilingue.en.trim()))
                                        ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                                        : 'bg-green-600 hover:bg-green-500 text-white shadow-lg hover:shadow-xl'
                                    }`}
                                    title={
                                      modoCreacionOpcion === 'es' ? 'Crear opción en español' :
                                      modoCreacionOpcion === 'en' ? 'Crear opción en inglés' :
                                      'Crear opción bilingüe'
                                    }
                                  >
                                    <Save size={14} />
                                    {modoCreacionOpcion === 'es' && '🇪🇸 Crear en Español'}
                                    {modoCreacionOpcion === 'en' && '🇺🇸 Crear en Inglés'}
                                    {modoCreacionOpcion === 'ambos' && '🌐 Crear Bilingüe'}
                                  </button>
                                  <button
                                    onClick={() => {
                                      console.log('❌ Cancelando creación de opción');
                                      setCreandoOpcionPara(null);
                                      setNuevaOpcionBilingue({ es: '', en: '', descripcion_es: '', descripcion_en: '' });
                                      setModoCreacionOpcion('es');
                                    }}
                                    className="bg-gray-600 hover:bg-gray-500 px-4 py-2 rounded text-white text-sm font-medium transition flex items-center gap-2 shadow-lg hover:shadow-xl"
                                    title="Cancelar"
                                  >
                                    <XCircle size={14} />
                                    Cancelar
                                  </button>
                                </div>
                                
                                {/* Helper text */}
                                <div className="mt-3 text-xs text-gray-500">
                                  {modoCreacionOpcion === 'ambos' && (
                                    <div className="flex items-center gap-1">
                                      <span>💡</span>
                                      <span>Modo bilingüe: ambos idiomas son requeridos</span>
                                    </div>
                                  )}
                                  {modoCreacionOpcion !== 'ambos' && (
                                    <div className="flex items-center gap-1">
                                      <span>💡</span>
                                      <span>Presiona Enter en el campo de valor para crear rápidamente</span>
                                    </div>
                                  )}
                                </div>
                              </div>
                            ) : (
                              <button
                                onClick={() => {
                                  console.log('🚀 Iniciando creación de opción para set:', set.id);
                                  console.log('👤 Cliente bilingüe:', cliente?.bilingue);
                                  console.log('🌍 Idioma actual del set:', idiomaPorSet[set.id]);
                                  
                                  setCreandoOpcionPara(set.id);
                                  
                                  // Inicializar modo según si el cliente es bilingüe
                                  if (cliente?.bilingue) {
                                    // Para clientes bilingües, usar el idioma actual del set o defaultear a 'ambos'
                                    const idiomaActual = idiomaPorSet[set.id] || 'es';
                                    setModoCreacionOpcion('ambos'); // Para clientes bilingües, defaultear a bilingüe
                                  } else {
                                    // Para clientes monolingües, siempre español
                                    setModoCreacionOpcion('es');
                                  }
                                  
                                  // Limpiar campos
                                  setNuevaOpcionBilingue({ es: '', en: '', descripcion_es: '', descripcion_en: '' });
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
              onClick={handleClose}
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
