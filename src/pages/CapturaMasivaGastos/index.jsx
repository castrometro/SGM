import { useCapturaGastos } from "./hooks/useCapturaGastos";
import PageHeader from "./components/PageHeader";
import InstructionsSection from "./components/InstructionsSection";
import DownloadTemplateSection from "./components/DownloadTemplateSection";
import FileUploadSection from "./components/FileUploadSection";
import MapeoCC from "./components/MapeoCC";
import ResultsSection from "./components/ResultsSection";
import ErrorSection from "./components/ErrorSection";
import { STYLES_CONFIG } from "./config/capturaConfig";

/**
 * Página principal de captura masiva de gastos
 * Refactorizada usando el patrón de feature folders
 */
const CapturaMasivaGastos = () => {
  const {
    // Estado
    archivo,
    procesando,
    resultados,
    error,
    headersExcel,
    mapeoCC,
    mostrarMapeoCC,
    
    // Acciones
    handleArchivoSeleccionado,
    procesarArchivo,
    descargarArchivo,
    descargarPlantilla,
    limpiarArchivo,
    setMapeoCC
  } = useCapturaGastos();

  const { containers } = STYLES_CONFIG;

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

        {/* Mapeo de Centros de Costos */}
        <MapeoCC 
          mostrarMapeoCC={mostrarMapeoCC}
          headersExcel={headersExcel}
          mapeoCC={mapeoCC}
          setMapeoCC={setMapeoCC}
        />

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

export default CapturaMasivaGastos;
