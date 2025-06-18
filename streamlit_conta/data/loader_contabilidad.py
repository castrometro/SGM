import json
import pathlib


def cargar_datos():
    """Load example accounting data for the Streamlit dashboard."""

    base = pathlib.Path(__file__).parent
    with open(base / "contabilidad_ejemplo.json", encoding="utf-8") as f:
        raw = json.load(f)

    cierre_actual = raw.get("cierres", [{}])[0]
    return {
        "cliente": raw.get("cliente"),
        "clasificaciones": raw.get("clasificaciones", []),
        "centros_costo": raw.get("centros_costo", []),
        "tipos_documento": raw.get("tipos_documento", []),
        "cierre": {
            k: cierre_actual.get(k)
            for k in [
                "id",
                "cliente",
                "periodo",
                "estado",
                "fecha_inicio_libro",
                "fecha_fin_libro",
                "cuentas_nuevas",
                "parsing_completado",
            ]
        },
        "plan_cuentas": cierre_actual.get("plan_cuentas", []),
        "movimientos": cierre_actual.get("movimientos", []),
        "resumen_financiero": cierre_actual.get("resumen_financiero", {})
    }
