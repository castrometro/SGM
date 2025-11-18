// src/modules/contabilidad/captura-gastos/pages/CapturaGastosPage.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useCapturaGastos } from "../hooks/useCapturaGastos";
import PageHeader from "../components/PageHeader";
import InstructionsSection from "../components/InstructionsSection";
import DownloadTemplateSection from "../components/DownloadTemplateSection";
import FileUploadSection from "../components/FileUploadSection";
import MapeoCC from "../components/MapeoCC";
import CuentasGlobalesSection from "../components/CuentasGlobalesSection";
import ResultsSection from "../components/ResultsSection";
import ErrorSection from "../components/ErrorSection";
import { STYLES_CONFIG } from "../constants/capturaConfig";
import { validarAccesoContabilidad } from "../utils/capturaGastosHelpers";

/**
 * Página principal de captura masiva de gastos (Rinde Gastos)
 * SOLO ACCESIBLE PARA ÁREA DE CONTABILIDAD
 */
const CapturaGastosPage = () => {
  const navigate = useNavigate();
  const [validandoAcceso, setValidandoAcceso] = useState(true);
  const [tieneAcceso, setTieneAcceso] = useState(false);

  // Validar acceso al área de Contabilidad
  useEffect(() => {
    const validarAcceso = () => {
      const usuarioStr = localStorage.getItem('usuario');
      
      console.log('🔍 Validando acceso a Rinde Gastos...');
      
      if (!usuarioStr) {
        console.log('❌ No hay usuario en localStorage');
        setTieneAcceso(false);
        setValidandoAcceso(false);
        return;
      }

      try {
        const usuario = JSON.parse(usuarioStr);
        const tieneContabilidad = validarAccesoContabilidad(usuario);

        console.log(tieneContabilidad ? '✅ Tiene acceso a Contabilidad' : '❌ NO tiene acceso a Contabilidad');
        setTieneAcceso(tieneContabilidad);
      } catch (error) {
        console.error('❌ Error al validar acceso:', error);
        setTieneAcceso(false);
      }
      
      setValidandoAcceso(false);
    };

    validarAcceso();
  }, []);

  const {
    // Estado
    archivo,
    procesando,
    resultados,
    error,
    headersExcel,
    centrosCostoDetectados,
    mapeoCC,
    mostrarMapeoCC,
    cuentasGlobales,
    setCuentasGlobales,
    
    // Acciones
    handleArchivoSeleccionado,
    procesarArchivo,
    descargarArchivo,
    descargarPlantilla,
    limpiarArchivo,
    setMapeoCC
  } = useCapturaGastos();

  const { containers } = STYLES_CONFIG;

  // Validando acceso
  if (validandoAcceso) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Validando acceso...</p>
        </div>
      </div>
    );
  }

  // Sin acceso
  if (!tieneAcceso) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="max-w-md mx-auto text-center p-8">
          <div className="text-red-400 text-5xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-100 mb-2">Acceso Denegado</h2>
          <p className="text-gray-400 mb-6">
            Esta herramienta solo está disponible para usuarios del área de <strong className="text-purple-400">Contabilidad</strong>.
          </p>
          <button
            onClick={() => navigate('/menu')}
            className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
          >
            Volver al Menú
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={containers.main}>
      {/* Header */}
      <PageHeader />

      <div className={containers.content}>
        {/* Instrucciones */}
        <InstructionsSection />

        {/* Descargar Plantilla */}
        <DownloadTemplateSection onDownload={descargarPlantilla} />

        {/* Subir Archivo */}
        <FileUploadSection 
          archivo={archivo}
          procesando={procesando}
          onArchivoSeleccionado={handleArchivoSeleccionado}
          onLimpiarArchivo={limpiarArchivo}
          onProcesar={procesarArchivo}
        />

        {/* Mapeo de Centros de Costos (hasta 7 tipos) */}
        <MapeoCC 
          mostrarMapeoCC={mostrarMapeoCC}
          headersExcel={headersExcel}
          centrosCostoDetectados={centrosCostoDetectados}
          mapeoCC={mapeoCC}
          setMapeoCC={setMapeoCC}
        />

        {/* Cuentas Globales (obligatorias) */}
        {mostrarMapeoCC && (
          <CuentasGlobalesSection 
            cuentasGlobales={cuentasGlobales}
            setCuentasGlobales={setCuentasGlobales}
          />
        )}

        {/* Error */}
        <ErrorSection error={error} />

        {/* Resultados */}
        <ResultsSection 
          resultados={resultados}
          onDescargar={descargarArchivo}
        />
      </div>
    </div>
  );
};

export default CapturaGastosPage;
