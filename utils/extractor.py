# utils/extractor.py
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io
import os
import shutil
import tempfile
from textwrap import shorten
from difflib import SequenceMatcher
from companias.detector import detectar_compania_con_porcentaje
from utils.file_utils import obtener_propietario_desde_nombre
from ramos import get_ramo_from_email
from anotador.inteligente import AnotadorInteligente
from anotador.interfaz_consola import InterfazAnotadorConsola
import subprocess
import sys


def es_texto_legible(texto, min_alpha_ratio=0.5, min_words=3):
    """
    Detecta si el texto embebido parece ser legible.
    Evita falsos positivos de texto corrupto o sin mapa Unicode.
    """
    if not texto or not texto.strip():
        return False

    palabras = texto.strip().split()
    if len(palabras) < min_words:
        return False

    total_chars = len(texto)
    letras = sum(1 for c in texto if c.isalpha())
    alpha_ratio = letras / (total_chars + 1e-9)

    # Si tiene muchos caracteres raros o símbolos no imprimibles
    no_print = sum(1 for c in texto if ord(c) < 32 and c not in "\n\r\t")
    if no_print > total_chars * 0.1:
        return False

    return alpha_ratio >= min_alpha_ratio


def ocr_pagina_fuerte(pagina, dpi=500, lang="eng+spa", threshold=180, psm=6):
    """
    Hace OCR robusto sobre una página renderizada.
    Se usa cuando el texto embebido no es legible.
    """
    try:
        pix = pagina.get_pixmap(dpi=dpi)
        if pix.width <= 0 or pix.height <= 0:
            return "", []

        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes)).convert("L")

        # Mejorar contraste y nitidez
        img = ImageEnhance.Contrast(img).enhance(2.0)
        img = img.filter(ImageFilter.MedianFilter(size=3))
        img_bw = img.point(lambda x: 0 if x < threshold else 255, "1")

        data = pytesseract.image_to_data(
            img_bw, lang=lang, output_type=pytesseract.Output.DICT, config=f"--psm {psm}"
        )

        lineas = []
        for i in range(len(data["text"])):
            t = data["text"][i].strip()
            if t:
                x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                lineas.append({"texto": t, "bbox": [x, y, x + w, y + h]})

        texto = " ".join(l["texto"] for l in lineas)
        if not texto.strip():
            texto = pytesseract.image_to_string(img, lang=lang, config=f"--psm {psm}")

        return texto.strip(), lineas
    except Exception:
        return "", []

import os, shutil, tempfile, io
from PIL import Image
import pytesseract
from pytesseract import Output
import fitz  # PyMuPDF

def procesar_archivo(ruta_archivo):
    """
    Procesa un archivo PDF o imagen SIN modificar el original.
    Trabaja sobre una copia temporal segura.
    Devuelve:
    {
        archivo: str,
        tipo: 'pdf' | 'imagen',
        texto_completo: str,
        paginas: [
            {
                pagina: int,
                texto: str,
                words: [{word, bbox}],
                page_rect: [width_pts, height_pts]
            }
        ],
        documentos_detectados: [
            {
                tipo: str,
                paginas: [int],
                campos: dict
            }
        ],
        error: str | None
    }
    """

    resultado = {
        "archivo": ruta_archivo,
        "tipo": None,
        "texto_completo": "",
        "paginas": [],
        "documentos_detectados": [],  # 👈 ya incluido aquí
        "error": None
    }

    extension = os.path.splitext(ruta_archivo)[1].lower()

    # =====================================================
    # Crear copia temporal
    # =====================================================
    try:
        tmp_dir = tempfile.mkdtemp(prefix="analizer_tmp_")
        tmp_path = os.path.join(tmp_dir, os.path.basename(ruta_archivo))
        shutil.copy2(ruta_archivo, tmp_path)
    except Exception as e:
        resultado["error"] = f"Error creando copia temporal: {str(e)}"
        return resultado

    try:
        # =====================================================
        # PROCESAR PDF
        # =====================================================
        if extension == ".pdf":
            resultado["tipo"] = "pdf"
            texto_total = []

            with fitz.open(tmp_path) as doc:
                if doc.is_encrypted:
                    if not doc.authenticate(""):
                        raise RuntimeError("PDF protegido con contraseña")

                for num, pagina in enumerate(doc, start=1):
                    page_entry = {
                        "pagina": num,
                        "texto": "",
                        "words": [],
                        "page_rect": [float(pagina.rect.width), float(pagina.rect.height)]
                    }

                    try:
                        # Intentar texto embebido
                        texto_embebido = pagina.get_text("text") or ""
                        if texto_embebido and es_texto_legible(texto_embebido, min_alpha_ratio=0.45, min_words=5):
                            texto_pag = texto_embebido.strip()
                            page_entry["texto"] = texto_pag
                            texto_total.append(texto_pag)

                            words = pagina.get_text("words")
                            for w in words:
                                x0, y0, x1, y1, word = float(w[0]), float(w[1]), float(w[2]), float(w[3]), w[4]
                                page_entry["words"].append({
                                    "word": word,
                                    "bbox": [x0, y0, x1, y1]
                                })
                        else:
                            # OCR si no hay texto embebido legible
                            pix = pagina.get_pixmap(dpi=300)
                            img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("L")

                            ocr_data = pytesseract.image_to_data(
                                img, lang="eng+spa", output_type=Output.DICT, config="--psm 6 --oem 3"
                            )

                            scale_x = pagina.rect.width / pix.width
                            scale_y = pagina.rect.height / pix.height

                            ocr_text_fragments = []
                            for i in range(len(ocr_data['level'])):
                                text = ocr_data['text'][i].strip()
                                if not text:
                                    continue
                                left = float(ocr_data['left'][i])
                                top = float(ocr_data['top'][i])
                                w_px = float(ocr_data['width'][i])
                                h_px = float(ocr_data['height'][i])

                                x0 = left * scale_x
                                y0 = top * scale_y
                                x1 = (left + w_px) * scale_x
                                y1 = (top + h_px) * scale_y

                                page_entry["words"].append({
                                    "word": text,
                                    "bbox": [x0, y0, x1, y1]
                                })
                                ocr_text_fragments.append(text)

                            if ocr_text_fragments:
                                page_entry["texto"] = " ".join(ocr_text_fragments)
                                texto_total.append(page_entry["texto"])

                        resultado["paginas"].append(page_entry)

                    except Exception as e:
                        resultado["paginas"].append({
                            "pagina": num,
                            "error": f"Error procesando página: {str(e)}"
                        })

                resultado["texto_completo"] = "\n".join(texto_total).strip()

        # =====================================================
        # PROCESAR IMAGEN
        # =====================================================
        elif extension in [".png", ".jpg", ".jpeg", ".tif", ".tiff"]:
            resultado["tipo"] = "imagen"
            try:
                img = Image.open(tmp_path).convert("L")
                texto = pytesseract.image_to_string(img, lang="eng+spa", config="--psm 6 --oem 3")
                resultado["texto_completo"] = texto.strip()

                ocr_data = pytesseract.image_to_data(
                    img, lang="eng+spa", output_type=Output.DICT, config="--psm 6 --oem 3"
                )

                words = []
                for i in range(len(ocr_data['level'])):
                    txt = ocr_data['text'][i].strip()
                    if not txt:
                        continue
                    left = float(ocr_data['left'][i])
                    top = float(ocr_data['top'][i])
                    w_px = float(ocr_data['width'][i])
                    h_px = float(ocr_data['height'][i])
                    words.append({
                        "word": txt,
                        "bbox": [left, top, left + w_px, top + h_px]
                    })
                resultado["paginas"].append({
                    "pagina": 1,
                    "texto": texto.strip(),
                    "words": words,
                    "page_rect": [img.width, img.height]
                })
            except Exception as e:
                resultado["error"] = f"Error procesando imagen: {str(e)}"

        else:
            resultado["error"] = f"Tipo de archivo no soportado: {extension}"

    except Exception as e:
        resultado["error"] = f"Error procesando archivo: {str(e)}"

    finally:
        try:
            shutil.rmtree(tmp_dir)
        except Exception:
            pass

    return resultado




# =====================================================
# 📊 NUEVA FUNCIÓN: PROCESAR DIRECTORIO COMPLETO
# =====================================================


def procesar_directorio_con_estadisticas(ruta_directorio, mostrar_todo=True, limite_caracteres=None):
    
    resultados = []
    total_archivos = 0
    fallos = 0
    sin_texto = []
    sin_compania = []
    archivos_anotados = 0

    print("\n" + "=" * 70)
    print(f"📂 Iniciando procesamiento de: {ruta_directorio}")
    print("=" * 70)

    # 🖥️ Inicializar visor una sola vez
    interfaz_global = InterfazAnotadorConsola()
    visor_iniciado = False

    # 🔁 Recorrer archivos
    for nombre_archivo in sorted(os.listdir(ruta_directorio), reverse=True):
        ruta = os.path.join(ruta_directorio, nombre_archivo)
        if not os.path.isfile(ruta):
            continue

        total_archivos += 1
        try:
            resultado = procesar_archivo(ruta)
        except Exception as e:
            print(f"❌ Error al procesar {nombre_archivo}: {e}")
            fallos += 1
            continue

        resultado["archivo"] = ruta
        resultados.append(resultado)

        print("\n" + "-" * 70)
        print(f"📁 Archivo: {nombre_archivo}")
        print(f"🔗 Ruta: {ruta}")
        print(f"✅ Tipo detectado: {resultado.get('tipo', 'desconocido')}")

        if resultado.get("error"):
            print(f"❌ Error: {resultado['error']}")
            fallos += 1
            continue

        texto = resultado.get("texto_completo", "")
        num_palabras = len(texto.split())
        num_paginas = len(resultado.get("paginas", []))

        print(f"📄 Páginas procesadas: {num_paginas}")
        print(f"📝 Palabras extraídas: {num_palabras}")

        if num_palabras == 0:
            sin_texto.append(nombre_archivo)
            continue

        # 🧠 Detectar compañía
        resultados_compania = detectar_compania_con_porcentaje(texto)
        compania_detectada = "DESCONOCIDA"

        if resultados_compania:
            top_cia, top_pct = sorted(resultados_compania.items(), key=lambda x: x[1], reverse=True)[0]
            compania_detectada = top_cia
            print(f"🏢 Compañía más probable: {top_cia} ({top_pct:.2f}%)")
        else:
            print("⚠️ No se pudo detectar la compañía.")
            sin_compania.append(nombre_archivo)

        # 👤 Obtener propietario, email y ramo
        print(f"➡️ Obteniendo propietario y ramo...")
        propietario = obtener_propietario_desde_nombre(nombre_archivo)
        email_propietario = f"{propietario}@acevedocouttolenc.com"
        ramo = get_ramo_from_email(email_propietario)
        print(f"👤 Propietario: {propietario}")
        print(f"📧 Email: {email_propietario}")
        print(f"🌿 Ramo: {ramo}")

        # 🖥️ Mostrar documento en visor
        print("\n" + "=" * 50)
        print("🎯 VISOR DE DOCUMENTOS")
        print("=" * 50)

        if not visor_iniciado:
            print("🖥️ Iniciando visor continuo...")
            if interfaz_global.iniciar_visor_continuo(ruta):
                visor_iniciado = True
                print("✅ Visor iniciado - permanecerá abierto durante todo el proceso.")
                #interfaz_global.visor.mantener_abierto()
            else:
                print("❌ No se pudo iniciar el visor, continuando sin anotación.")
                continue
        else:
            print(f"📄 Cargando documento en visor: {nombre_archivo}")
            if interfaz_global.cambiar_documento_en_visor(ruta):
                print("✅ Documento cargado en visor - revisa la ventana.")
            else:
                print("❌ No se pudo cargar el documento en el visor.")

        try:
            anotador = AnotadorInteligente(ruta)
            anotador.set_metadata(compania=compania_detectada, ramo=ramo)
            
            # 🎯 EJECUTAR ANOTACIÓN Y CAPTURAR RESULTADO
            anotacion_completada = interfaz_global.ejecutar_anotacion_continua(anotador, compania_detectada, ramo)
            
            if anotacion_completada:
                archivos_anotados += 1
                print("✅ Anotación completada y guardada.")
            else:
                print("⏭️ Anotación cancelada - pasando al siguiente documento.")
                # NO incrementar archivos_anotados y pasar al siguiente archivo
                continue
                
        except Exception as e:
            print(f"❌ Error en anotador: {e}")
            import traceback
            traceback.print_exc()
            # En caso de error, pasar al siguiente archivo
            continue
        

    # 🧹 Finalizar visor
    if visor_iniciado:
        print("\n" + "=" * 50)
        print("👋 PROCESO COMPLETADO")
        print("=" * 50)
        input("Presiona Enter para cerrar el visor y finalizar...")
        interfaz_global.cerrar_visor()

    # 📊 Estadísticas finales
    porcentaje_fallos = (fallos / total_archivos * 100) if total_archivos > 0 else 0
    porcentaje_sin_texto = (len(sin_texto) / total_archivos * 100) if total_archivos > 0 else 0
    porcentaje_sin_compania = (len(sin_compania) / total_archivos * 100) if total_archivos > 0 else 0

    print("\n" + "=" * 60)
    print("📊 ESTADÍSTICAS FINALES")
    print(f"   Archivos procesados     : {total_archivos}")
    print(f"   Archivos fallidos       : {fallos}")
    print(f"   Archivos sin texto      : {len(sin_texto)} ({porcentaje_sin_texto:.2f}%)")
    print(f"   Archivos sin compañía   : {len(sin_compania)} ({porcentaje_sin_compania:.2f}%)")
    print(f"   Archivos anotados       : {archivos_anotados}")
    print(f"   Porcentaje fallos       : {porcentaje_fallos:.2f}%")
    print("=" * 60)

    if sin_texto:
        print("\n⚠️ Archivos sin texto extraído:")
        for archivo in sin_texto:
            print(f"   - {archivo}")
    else:
        print("\n✅ Todos los archivos contienen texto extraído.")

    if sin_compania:
        print("\n🔗 Archivos sin compañía detectada:")
        for archivo in sin_compania:
            print(f"   - {archivo}")
    else:
        print("\n✅ Todas las compañías detectadas correctamente.")

    estadisticas = {
        "total_archivos": total_archivos,
        "archivos_fallidos": fallos,
        "archivos_sin_texto": len(sin_texto),
        "archivos_sin_compania": len(sin_compania),
        "archivos_anotados": archivos_anotados,
        "porcentaje_fallos": round(porcentaje_fallos, 2),
        "porcentaje_sin_texto": round(porcentaje_sin_texto, 2),
        "porcentaje_sin_compania": round(porcentaje_sin_compania, 2),
    }

    return resultados, estadisticas


def extraer_texto_y_posiciones_ocr_puro(ruta_archivo):
    """
    Extrae texto con OCR de cada página del PDF, incluso si no tiene texto embebido.
    """
    print(f"🧩 OCR puro aplicado: {os.path.basename(ruta_archivo)}")
    doc = fitz.open(ruta_archivo)
    resultado = {
        "archivo": ruta_archivo,
        "texto_completo": "",
        "paginas": []
    }

    for num, pagina in enumerate(doc, start=1):
        # 1️⃣ Renderizar la página como imagen de alta resolución
        pix = pagina.get_pixmap(dpi=500)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))

        # 2️⃣ Preprocesamiento para mejor contraste
        img = img.convert("L")  # escala de grises
        img = ImageEnhance.Contrast(img).enhance(2.0)
        img = img.filter(ImageFilter.MedianFilter())

        # 3️⃣ Aplicar OCR (solo inglés y español)
        texto = pytesseract.image_to_string(img, lang="eng+spa")

        # 4️⃣ Guardar resultado
        resultado["paginas"].append({
            "pagina": num,
            "texto": texto.strip()
        })
        resultado["texto_completo"] += texto + "\n"

        print(f"✅ Página {num} procesada ({len(texto.split())} palabras extraídas)")

    doc.close()
    return resultado

# =====================================================
# 🧪 FUNCIÓN PARA EVALUAR CALIDAD DE EXTRACCIÓN
# =====================================================
def evaluar_calidad_extraccion(resultados, umbral_palabras=50):
    """
    Evalúa la cantidad de texto extraído por archivo.
    Muestra los que tienen menos de 'umbral_palabras' y devuelve su lista.
    """
    archivos_pocos_datos = []

    for r in resultados:
        texto = r.get("texto_completo", "")
        num_palabras = len(texto.split())
        if num_palabras < umbral_palabras:
            archivos_pocos_datos.append({
                "archivo": r["archivo"],
                "palabras": num_palabras,
                "error": r.get("error")
            })

    total = len(resultados)
    pocos = len(archivos_pocos_datos)
    porcentaje = (pocos / total * 100) if total else 0

    print("\n" + "=" * 60)
    print("📉 ANÁLISIS DE CALIDAD DE EXTRACCIÓN")
    print(f"   Total archivos evaluados : {total}")
    print(f"   Con < {umbral_palabras} palabras : {pocos} ({porcentaje:.2f}%)")
    print("=" * 60)

    if pocos > 0:
        print("📂 Archivos con poco texto extraído:")
        for a in archivos_pocos_datos:
            print(f" - {a['archivo']} ({a['palabras']} palabras)")

    return archivos_pocos_datos

