import os
import importlib.util
from utils.extractor import procesar_directorio_con_estadisticas
spec = importlib.util.spec_from_file_location("config_module", "config.py")
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
BASE_DIR = config_module.BASE_DIR



def main():
    print("🧠 INICIANDO EXTRACTOR INTELIGENTE")
    print("=" * 60)

    # 🔧 Directorio base configurado
    carpeta_pruebas = BASE_DIR

    if not os.path.exists(carpeta_pruebas):
        print(f"⚠️ Carpeta no encontrada: {carpeta_pruebas}")
        return

    print(f"📂 Procesando archivos en: {carpeta_pruebas}")
    print("-" * 60)

    # 🚀 Ejecutar el extractor (ya incluye toda la lógica de procesamiento)
    resultados, estadisticas = procesar_directorio_con_estadisticas(carpeta_pruebas)
    print("\n✅ Procesamiento completado.\n")
    
    


if __name__ == "__main__":
    main()