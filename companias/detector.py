import re
from collections import Counter
from companias import COMPANIAS
import unicodedata
from difflib import SequenceMatcher

#esta funcion solo funciona para gnp

def get_cia(driver):
    spans = driver.find_elements("tag name", "span")
    conteo = Counter()

    for span in spans:
        texto = span.text.strip().upper()
        if not texto:
            continue
        for compania, alias_list in COMPANIAS.items():
            for alias in alias_list:
                if re.search(rf"\b{re.escape(alias.upper())}\b", texto):
                    conteo[compania] += len(
                        re.findall(rf"\b{re.escape(alias.upper())}\b", texto)
                    )

    if not conteo:
        return None

    total = sum(conteo.values())
    porcentajes = {cia: (count / total) * 100 for cia, count in conteo.items()}
    cia_top = max(porcentajes, key=porcentajes.get)

    print("📊 Resultados detección compañías:")
    for cia, pct in sorted(porcentajes.items(), key=lambda x: x[1], reverse=True):
        print(f"   - {cia}: {pct:.2f}%")

    print(f"✅ Compañía detectada: {cia_top}")
    return cia_top

#red neuronal
import re
import unicodedata
from difflib import SequenceMatcher

def normalizar_texto(texto):
    """Limpia acentos, convierte a mayúsculas y remueve caracteres especiales."""
    texto = texto.upper()
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    texto = re.sub(r'[^A-Z0-9\s]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()

def buscar_coincidencias_palabras_clave(texto, variantes):
    """
    Busca coincidencias de palabras clave en el texto
    Retorna el porcentaje basado en coincidencias encontradas
    """
    texto_norm = normalizar_texto(texto)
    coincidencias_encontradas = 0
    total_variantes = len(variantes)
    
    for variante in variantes:
        variante_norm = normalizar_texto(variante)
        # Buscar la variante como palabra completa
        patron = r'\b' + re.escape(variante_norm) + r'\b'
        if re.search(patron, texto_norm):
            coincidencias_encontradas += 1
    
    # Calcular porcentaje basado en coincidencias
    if total_variantes > 0:
        return (coincidencias_encontradas / total_variantes) * 100
    return 0

def detectar_compania_con_porcentaje(texto, umbral=30):  # 🔽 Umbral más bajo (30%)
    """
    Versión corregida - Busca palabras clave en lugar de similitud de texto completo
    """
    if not texto or len(texto) < 5:
        return {}

    resultados = {}
    
    for cia, variantes in COMPANIAS.items():
        porcentaje = buscar_coincidencias_palabras_clave(texto, variantes)
        if porcentaje >= umbral:
            resultados[cia] = porcentaje

    return resultados