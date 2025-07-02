# 🌐 Guía Rápida: Sistema Bilingüe en Modal de Clasificaciones

## 🎯 Nueva Funcionalidad

Ahora puedes cambiar el idioma de visualización de las opciones de clasificación directamente en el modal de clasificaciones existente.

## 🚀 Cómo Usar

### 1. Acceder al Modal
1. Sube tu archivo de clasificaciones en la tarjeta Clasificación Bulk
2. Haz clic en **"Ver clasificaciones"** para abrir el modal
3. Ve a la pestaña **"Sets"**

### 2. Cambiar Idioma por Set
- En cada set verás botones **ES** y **EN** junto al nombre
- Haz clic en **ES** para ver opciones en español
- Haz clic en **EN** para ver opciones en inglés
- El idioma se detecta automáticamente según la configuración del cliente

### 3. Indicadores Visuales
- **Badge verde "Bilingüe"**: El set tiene traducciones en inglés
- **Badge amarillo "Solo ES"**: El set solo tiene opciones en español
- **Etiqueta EN/ES**: Cada opción muestra en qué idioma se está visualizando
- **Tooltip**: Pasa el mouse sobre las opciones para ver descripciones

## 🔧 Características

### Detección Automática
- El sistema detecta automáticamente el idioma preferido del cliente
- Los sets se muestran inicialmente en el idioma del cliente

### Carga Inteligente
- Las opciones en ambos idiomas se cargan automáticamente
- Solo se hacen peticiones adicionales cuando cambias de idioma

### Fallback Seguro
- Si no hay traducciones, se muestran las opciones en español
- Compatible con clientes que no usan traducciones

## 💡 Tips de Uso

### Para Analistas
1. **Revisar traducciones**: Cambia entre ES/EN para verificar que las opciones existen en ambos idiomas
2. **Identificar gaps**: Los sets con badge "Solo ES" necesitan traducciones
3. **Editar eficientemente**: Usa el modal bilingüe dedicado para completar traducciones masivas

### Para Administradores
1. **Configurar cliente bilingüe**: Establece `idioma_preferido = 'en'` en el cliente
2. **Monitorear traducciones**: Revisa qué sets necesitan más trabajo de traducción
3. **Capacitar usuarios**: Enseña a los analistas a usar los controles de idioma

## 🔗 Funciones Relacionadas

- **Modal Bilingüe Dedicado**: Para edición masiva de traducciones (botón "Gestión Bilingüe")
- **Reportes**: Los informes se generan automáticamente en el idioma del cliente
- **APIs Bilingües**: Los endpoints detectan y sirven contenido en el idioma correcto

## 🐛 Solución de Problemas

### "No aparecen opciones en inglés"
- Verifica que el cliente tenga `idioma_preferido` configurado
- Revisa que existan traducciones en la base de datos
- Usa el modal bilingüe dedicado para crear traducciones

### "El idioma no cambia"
- Refresca el modal cerrando y abriendo
- Verifica la consola del navegador para errores
- Confirma que el backend esté sirviendo los endpoints bilingües

### "Badge dice 'Solo ES' pero hay traducciones"
- Puede ser un problema de caché - recarga los datos
- Verifica que las traducciones estén guardadas correctamente
- Usa las herramientas de desarrollador para inspeccionar las peticiones

## 📝 Notas Técnicas

- Las opciones se cargan usando los helpers bilingües del backend
- El estado del idioma se mantiene por set individualmente
- Compatible con la funcionalidad existente de CRUD de sets y opciones
- Los cambios se sincronizan automáticamente entre los diferentes componentes

---

*Para más información técnica, consulta `DOCUMENTACION_HELPERS_BILINGUES.md`*
