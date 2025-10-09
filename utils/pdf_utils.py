# utils/pdf_utils.py
import fitz
import re
from difflib import SequenceMatcher
from typing import Dict, Any, Optional, Tuple, List

# --------------------------
# Config: variantes de label por campo (añade los que necesites)
# --------------------------
DEFAULT_LABELS = {
    "fecha_de_expedicion": ["Fecha de Expedición", "Fecha Emisión", "Fecha de Emisión", "Fecha"],
    "fecha_emision": ["Fecha de Emisión", "Fecha Emisión", "Fecha"],
    "forma_pago": ["Forma de Pago", "Forma Pago", "Forma de pago"],
    "poliza": ["Póliza", "Póliza No.", "Póliza No", "Póliza /"],
    "serie": ["Serie", "Recibo", "Recibo No", "Recibo "],
    "emision_dia": ["Día", "Dia", "DD", "Día:", "Dia:"],
    "emision_mes": ["Mes", "MM", "Mes:", "MES"], 
    "emision_año": ["Año", "Año", "AAAA", "Año:", "AÑO", "AÑO:"],
    # añade más según tus campos...
}

# --------------------------
# Helpers
# --------------------------
def normalize(s: str) -> str:
    if not s:
        return ""
    return re.sub(r'\s+', ' ', s).strip().lower()

def _first_numeric_coords(item: Tuple) -> Optional[Tuple[float, float, float, float]]:
    nums = [x for x in item if isinstance(x, (int, float))]
    if len(nums) >= 4:
        return float(nums[0]), float(nums[1]), float(nums[2]), float(nums[3])
    return None

def _first_string(item: Tuple) -> str:
    for x in item:
        if isinstance(x, str):
            return x
    return ""

def _unique_rects(rects: List[fitz.Rect]) -> List[fitz.Rect]:
    seen = set()
    out = []
    for r in rects:
        key = (round(r.x0,2), round(r.y0,2), round(r.x1,2), round(r.y1,2))
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out

def _expand_rect(rect: fitz.Rect, page: fitz.Page, right=200, down=20, left=0, up=0) -> fitz.Rect:
    # Expande con límites de la página
    x0 = max(0, rect.x0 - left)
    y0 = max(0, rect.y0 - up)
    x1 = min(page.rect.width, rect.x1 + right)
    y1 = min(page.rect.height, rect.y1 + down)
    return fitz.Rect(x0, y0, x1, y1)

def _group_words_in_region(page: fitz.Page, region: fitz.Rect) -> str:
    # Devuelve el texto completo dentro del region, limpio
    try:
        text = page.get_text("text", clip=region)
        return re.sub(r'\s+', ' ', text).strip()
    except Exception:
        return ""

# --------------------------
# Búsquedas inteligentes
# --------------------------
def _best_search_rects_for_target(page: fitz.Page, target: str) -> List[fitz.Rect]:
    """Intenta varias variantes para encontrar rects que contengan target."""
    rects: List[fitz.Rect] = []
    if not target:
        return rects

    variants = [target, normalize(target), re.sub(r'\s+','', target)]
    digits_only = re.sub(r'\D','', target)
    if digits_only:
        variants.append(digits_only)

    for v in variants:
        try:
            found = page.search_for(v, quads=False)  # search_for puede fallar con algunos inputs
            if found:
                rects.extend(found)
        except Exception:
            continue
    return _unique_rects(rects)

def _search_words_by_similarity(page: fitz.Page, target_norm: str, umbral: float) -> Optional[Tuple[str, Tuple[float,float,float,float]]]:
    """Revisa words y devuelve el mejor match (texto, coords) si supera umbral, o None."""
    words = page.get_text("words") or []
    mejor = (None, 0.0, None)  # (texto, similitud, coords)
    for w in words:
        coords = _first_numeric_coords(w)
        txt = _first_string(w).strip()
        if not txt or coords is None:
            continue
        sim = SequenceMatcher(None, target_norm, normalize(txt)).ratio()
        if sim > mejor[1]:
            mejor = (txt, sim, coords)
    if mejor[1] >= umbral:
        texto, sim, coords = mejor
        return texto, (coords[0], coords[1], coords[2], coords[3])
    return None

# --------------------------
# Función principal mejorada
# --------------------------
def buscar_valores_en_pdf(pdf_path: str, datos: Dict[str, str], umbral_similitud: float = 0.7,
                          labels_map: Dict[str, List[str]] = None) -> Dict[str, Dict[str, Any]]:
    """
    Busca valores en un PDF con tolerancia a formato. Devuelve dict por campo:
    {
      campo: {
         'valor': original,
         'match_encontrado': texto_en_pdf_o_None,
         'similitud': float,
         'coords': (página, x0, y0, x1, y1) o None
      }
    }
    - Primero intenta match directo (valor exacto/approx).
    - Si no encuentra y existe label en labels_map o DEFAULT_LABELS, busca label y extrae valor vecino.
    """
    resultados: Dict[str, Dict[str, Any]] = {}
    labels_map = labels_map or DEFAULT_LABELS

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"❌ No se pudo abrir el PDF {pdf_path}: {e}")
        return resultados

    try:
        for campo, valor in datos.items():
            valor_original = valor or ""
            valor_norm = normalize(valor_original)
            mejor_match = None
            mejor_sim = 0.0
            mejor_coords = None

            # Si valor vacío, intentamos buscar por label directamente
            buscar_por_label = False
            if not valor_norm:
                buscar_por_label = True

            # 1) Búsqueda directa por valor (por páginas)
            if not buscar_por_label:
                for p_no, page in enumerate(doc, start=1):
                    # 1.A search_for (mejor para frases/compuestos)
                    try:
                        rects = _best_search_rects_for_target(page, valor_original)
                    except Exception:
                        rects = []
                    for r in rects:
                        txt_inside = _group_words_in_region(page, r)
                        sim = SequenceMatcher(None, valor_norm, normalize(txt_inside)).ratio() if txt_inside else 0.0
                        if sim > mejor_sim:
                            mejor_sim = sim
                            mejor_match = txt_inside or None
                            mejor_coords = (p_no, r.x0, r.y0, r.x1, r.y1)
                    # 1.B fallback words similarity
                    wmatch = _search_words_by_similarity(page, valor_norm, umbral_similitud)
                    if wmatch:
                        txt_w, coords_w = wmatch
                        simw = SequenceMatcher(None, valor_norm, normalize(txt_w)).ratio()
                        if simw > mejor_sim:
                            mejor_sim = simw
                            mejor_match = txt_w
                            mejor_coords = (p_no, coords_w[0], coords_w[1], coords_w[2], coords_w[3])
                    if mejor_sim >= 0.99:
                        break

            # 2) Si no encontró nada con valor, o valor está vacío, intentar label -> extraer vecino
            if (not mejor_coords) and campo in labels_map:
                labels = labels_map[campo]
                for p_no, page in enumerate(doc, start=1):
                    found_rects = []
                    for lbl in labels:
                        try:
                            rlist = _best_search_rects_for_target(page, lbl)
                        except Exception:
                            rlist = []
                        if rlist:
                            found_rects.extend(rlist)
                    found_rects = _unique_rects(found_rects)
                    if not found_rects:
                        # no label en esta página, continuar
                        continue

                    # Por cada label encontrada, buscar valor a la derecha, luego abajo, luego agrupar palabras
                    for r in found_rects:
                        # intentamos derecha amplia
                        r_right = _expand_rect(r, page, right=260, down=(r.height/2 + 10))
                        txt_right = _group_words_in_region(page, r_right)
                        if txt_right:
                            sim = SequenceMatcher(None, valor_norm, normalize(txt_right)).ratio() if valor_norm else 0.0
                            # Si valor original está vacío, aceptamos el texto aunque similitud baja (lo guardamos)
                            if valor_norm and sim >= umbral_similitud and sim > mejor_sim:
                                mejor_sim = sim
                                mejor_match = txt_right
                                mejor_coords = (p_no, r_right.x0, r_right.y0, r_right.x1, r_right.y1)
                            elif not valor_norm and txt_right.strip():
                                mejor_sim = sim
                                mejor_match = txt_right
                                mejor_coords = (p_no, r_right.x0, r_right.y0, r_right.x1, r_right.y1)
                                # si encontramos algo razonable, lo usamos
                                break
                        # intentar abajo (fila siguiente)
                        r_down = _expand_rect(r, page, right=120, down=60)
                        txt_down = _group_words_in_region(page, r_down)
                        if txt_down:
                            sim = SequenceMatcher(None, valor_norm, normalize(txt_down)).ratio() if valor_norm else 0.0
                            if valor_norm and sim >= umbral_similitud and sim > mejor_sim:
                                mejor_sim = sim
                                mejor_match = txt_down
                                mejor_coords = (p_no, r_down.x0, r_down.y0, r_down.x1, r_down.y1)
                            elif not valor_norm and txt_down.strip():
                                mejor_sim = sim
                                mejor_match = txt_down
                                mejor_coords = (p_no, r_down.x0, r_down.y0, r_down.x1, r_down.y1)
                                break
                        # intentar izquierda/agrupación si necesario
                        # (puedes añadir más heurísticas si los PDFs tienen otras estructuras)
                    if mejor_coords:
                        break

            # 3) Si aún no hay mejor_coords, intentar fallback words global sin umbral
            if not mejor_coords:
                for p_no, page in enumerate(doc, start=1):
                    words = page.get_text("words") or []
                    # agrupamos secuencialmente varias palabras contiguas para compuestos
                    # (por ejemplo: día/mes/año separados), construimos n-grams de longitud 1..4
                    texts_coords = []
                    for w in words:
                        coords = _first_numeric_coords(w)
                        txt = _first_string(w).strip()
                        if coords and txt:
                            texts_coords.append((txt, coords, p_no))
                    # construir n-grams
                    for i in range(len(texts_coords)):
                        concat = texts_coords[i][0]
                        coords_i = texts_coords[i][1]
                        for n in range(1,4):  # 1..3 palabras juntas
                            j = i + n
                            if j < len(texts_coords):
                                concat = concat + " " + texts_coords[j][0]
                                coords_j = texts_coords[j][1]
                                # bbox que cubre ambas
                                x0 = min(coords_i[0], coords_j[0])
                                y0 = min(coords_i[1], coords_j[1])
                                x1 = max(coords_i[2], coords_j[2])
                                y1 = max(coords_i[3], coords_j[3])
                                sim = SequenceMatcher(None, valor_norm, normalize(concat)).ratio()
                                if sim > mejor_sim and sim >= 0.45:  # umbral muy laxo para fallback
                                    mejor_sim = sim
                                    mejor_match = concat
                                    mejor_coords = (p_no, x0, y0, x1, y1)
                                    if sim >= umbral_similitud:
                                        break
                        if mejor_sim >= umbral_similitud:
                            break
                    if mejor_sim >= umbral_similitud:
                        break

            resultados[campo] = {
                "valor": valor_original,
                "match_encontrado": mejor_match,
                "similitud": round(mejor_sim, 3),
                "coords": mejor_coords
            }

    finally:
        doc.close()

    return resultados
