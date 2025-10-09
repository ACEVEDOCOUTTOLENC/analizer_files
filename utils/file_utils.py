import os
import glob
import re
from datetime import datetime

def obtener_todos_los_pdfs():
    """Obtiene todos los PDFs del directorio base"""
    try:
        from config import BASE_DIR, PDF_SEARCH_PATTERNS
        todos_pdfs = []
        for patron in PDF_SEARCH_PATTERNS:
            archivos = glob.glob(os.path.join(BASE_DIR, patron), recursive=True)
            for archivo in archivos:
                if archivo.lower().endswith('.pdf'):
                    todos_pdfs.append(archivo)
        
        todos_pdfs = list(set(todos_pdfs))
        print(f"📚 Se encontraron {len(todos_pdfs)} archivos PDF")
        return todos_pdfs
    except Exception as e:
        print(f"❌ Error obteniendo PDFs: {e}")
        return []

def encontrar_archivo_mas_reciente():
    """Encuentra el archivo Excel más reciente (para compatibilidad)"""
    try:
        from config import BASE_DIR, EXCEL_PATTERN
        archivos = glob.glob(os.path.join(BASE_DIR, EXCEL_PATTERN))
        if not archivos:
            return None
        
        def extraer_fecha_hora(archivo):
            nombre = os.path.basename(archivo)
            match = re.search(r'(\d{8}_\d{6})', nombre)
            if match:
                return datetime.strptime(match.group(1), '%Y%m%d_%H%M%S')
            return datetime.min
        
        return max(archivos, key=extraer_fecha_hora)
    except:
        return None
    
import os

def obtener_propietario_desde_nombre(pdf_path: str) -> str:
    """
    Extrae el propietario (ej: 'danos2', 'vida1', 'autos4') desde el nombre del PDF.
    Formato esperado: YYYYMMDD_HHMMSS_propietario_....pdf
    """
    nombre = os.path.basename(pdf_path)
    partes = nombre.split("_")
    if len(partes) >= 3:
        return partes[2].lower()  # ej: "danos2"
    return "desconocido"
