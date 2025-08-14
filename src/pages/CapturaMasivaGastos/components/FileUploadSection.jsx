import { FileSpreadsheet, X, Clock } from "lucide-react";
import { CAPTURA_CONFIG, STYLES_CONFIG, UI_MESSAGES } from "../config/capturaConfig";

/**
 * Componente para subir archivos Excel
 */
const FileUploadSection = ({ 
  archivo, 
  procesando, 
  onArchivoSeleccionado, 
  onLimpiarArchivo, 
  onProcesar 
}) => {
  const { steps, fileConfig } = CAPTURA_CONFIG;
  const { containers, buttons } = STYLES_CONFIG;
  const { processing } = UI_MESSAGES;

  return (
    <div className={containers.section}>
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <steps.upload.icon className="w-5 h-5" />
        {steps.upload.title}
      </h2>
      
      <div className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center">
        <input
          type="file"
          accept={fileConfig.acceptedFormats}
          onChange={onArchivoSeleccionado}
          className="hidden"
          id="archivo-excel"
        />
        <label 
          htmlFor="archivo-excel" 
          className="cursor-pointer flex flex-col items-center gap-4"
        >
          <div className="p-4 bg-emerald-600/20 rounded-full">
            <FileSpreadsheet className="w-8 h-8 text-emerald-400" />
          </div>
          <div>
            <p className="text-lg font-medium">
              {archivo ? archivo.name : fileConfig.placeholderText}
            </p>
            <p className="text-gray-400 text-sm">
              {fileConfig.supportedText}
            </p>
          </div>
        </label>
      </div>

      {archivo && (
        <div className="mt-4 flex items-center justify-between bg-gray-700 p-4 rounded-lg">
          <div className="flex items-center gap-3">
            <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
            <div>
              <p className="font-medium">{archivo.name}</p>
              <p className="text-gray-400 text-sm">
                {(archivo.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          </div>
          <button
            onClick={onLimpiarArchivo}
            className="text-red-400 hover:text-red-300 p-1"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {archivo && (
        <button
          onClick={() => {
            console.log('🖱️ Botón procesar clickeado');
            console.log('📝 onProcesar:', onProcesar);
            console.log('⏳ procesando:', procesando);
            if (onProcesar) {
              onProcesar();
            } else {
              console.error('❌ onProcesar no está definido');
            }
          }}
          disabled={procesando}
          className={`mt-4 w-full ${buttons.secondary} ${buttons.disabled}`}
        >
          {procesando ? (
            <>
              <Clock className="w-4 h-4 animate-spin" />
              {processing.active}
            </>
          ) : (
            processing.idle
          )}
        </button>
      )}
    </div>
  );
};

export default FileUploadSection;
