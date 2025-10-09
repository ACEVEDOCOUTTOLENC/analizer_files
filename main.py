#!/usr/bin/env python3
"""
Script principal - MISMA PESTAÑA (MÁXIMA VELOCIDAD)
"""

import os
import re  # 👈 AÑADIR ESTA IMPORTACIÓN
from utils.file_utils import obtener_todos_los_pdfs, obtener_propietario_desde_nombre
from utils.selenium_utils import FirefoxPDFViewer
from companias.detector import get_cia
from ramos import get_ramo_from_email
from companias import gnp
from excel_processor import procesar_con_excel
from utils.pdf_utils import buscar_valores_en_pdf

def extraer_valores_fecha(resultado_pdf):
    """Extrae valores numéricos - SOLO LOS DE FECHA (VERSIÓN CORREGIDA)"""
    try:
        valores = {}
        
        def extraer_primer_numero_despues_etiqueta(texto, etiqueta):
            """Extrae solo el primer número después de la etiqueta específica"""
            if not texto:
                return ""
            
            # Patrón: etiqueta seguida de posibles no-números y luego números
            patron = rf'{etiqueta}\D*(\d+)'
            match = re.search(patron, texto, re.IGNORECASE)
            return match.group(1) if match else ""
        
        # Extraer cada campo individualmente con patrones específicos
        texto_dia = resultado_pdf.get("emision_dia", {}).get("match_encontrado", "") or ""
        valores["emision_dia"] = extraer_primer_numero_despues_etiqueta(texto_dia, "Día")
        
        texto_mes = resultado_pdf.get("emision_mes", {}).get("match_encontrado", "") or ""
        valores["emision_mes"] = extraer_primer_numero_despues_etiqueta(texto_mes, "Mes")
        
        texto_año = resultado_pdf.get("emision_año", {}).get("match_encontrado", "") or ""
        valores["emision_año"] = extraer_primer_numero_despues_etiqueta(texto_año, "Año")
        
        # Debug: mostrar qué se está procesando
        print(f"🔍 DEBUG FECHA - Texto Día: '{texto_dia}' -> Extraído: '{valores['emision_dia']}'")
        print(f"🔍 DEBUG FECHA - Texto Mes: '{texto_mes}' -> Extraído: '{valores['emision_mes']}'")
        print(f"🔍 DEBUG FECHA - Texto Año: '{texto_año}' -> Extraído: '{valores['emision_año']}'")
        
        return valores
        
    except Exception as e:
        print(f"⚠️ Error en extraer_valores_fecha: {e}")
        return {"emision_dia": "", "emision_mes": "", "emision_año": ""}

def main():
    print("🚀 INICIANDO MODO MISMA PESTAÑA - MÁXIMA VELOCIDAD")
    print("=" * 60)
    print("📂 Buscando archivos PDF...")
    print("=" * 60)
    
    pdfs = obtener_todos_los_pdfs()
    if not pdfs:
        print("❌ No se encontraron archivos PDF")
        return
    
    print(f"🎯 Se cargarán {len(pdfs)} archivos PDF")
    print("💡 Se usa UNA SOLA pestaña - Solo cambia el documento")
    print("⚡ VELOCIDAD MÁXIMA: No se cierra/reabre el navegador")
    print("=" * 60)
    
    print("\n📋 LISTA DE PDFs:")
    for i, pdf in enumerate(pdfs, 1):
        print(f"  {i:2d}. {os.path.basename(pdf)}")
    
    print(f"\n{'='*60}")
    input("⏎ Presiona ENTER para comenzar (VELOCIDAD MÁXIMA)...")
    
    viewer = FirefoxPDFViewer(headless=False)
    
    try:
        for i, pdf in enumerate(pdfs, 1):
            print(f"\n{'#'*50}")
            print(f"📄 Cargando PDF {i}/{len(pdfs)}: {os.path.basename(pdf)}")
            print(f"{'#'*50}")
            
            viewer.cambiar_pdf_en_misma_pestana(pdf, i, len(pdfs))

            # 👉 Detectar compañía
            cia_detectada = get_cia(viewer.driver)
            print("CIA DETECTADA:", cia_detectada)

            propietario = obtener_propietario_desde_nombre(pdf)
            email_propietario = f"{propietario}@acevedocouttolenc.com"
            ramo = get_ramo_from_email(email_propietario)

            print("EMAIL PROPIETARIO:", email_propietario)
            print("RAMO DETECTADO:", ramo)

            tipo_doc = None
            datos_extraidos = {}
            
            if cia_detectada and cia_detectada.lower() == "gnp":
                tipo_doc = gnp.get_tipo_documento(viewer.driver, ramo)

                if tipo_doc:
                    datos_extraidos = gnp.extraer_datos_documento(viewer.driver, ramo, tipo_doc)
                    print(f"📊 DATOS EXTRAÍDOS COMPLETOS (Selenium): {datos_extraidos}")

                    # -----------------------------------------------------------------
                    # 🧠 NUEVO BLOQUE: EXTRACCIÓN POR PyMuPDF (pdf_utils)
                    # -----------------------------------------------------------------
                    print("\n🧠 Iniciando extracción con PyMuPDF (pdf_utils)...")

                    # Buscar por etiquetas (campos vacíos)
                    campos_a_buscar = {
                        "poliza": datos_extraidos.get("poliza", ""),
                        "emision_dia": "",  # VACÍO para buscar por etiqueta "Día"
                        "emision_mes": "",  # VACÍO para buscar por etiqueta "Mes"  
                        "emision_año": "",  # VACÍO para buscar por etiqueta "Año"
                        "serie": "",
                        "forma_pago": datos_extraidos.get("forma_pago", "")
                        
                    }

                    resultado_pdf = buscar_valores_en_pdf(pdf, campos_a_buscar)
                    # 👇 PROCESAR LOS RESULTADOS PARA EXTRAER SOLO LOS NÚMEROS
                    
                    valores_fecha = extraer_valores_fecha(resultado_pdf)
                    # Póliza
                    poliza_pdf = resultado_pdf.get("poliza", {}).get("match_encontrado", "")
                    if poliza_pdf:
                        print(f"   • PÓLIZA: {poliza_pdf}")
                    
                    # Serie
                    serie_pdf = resultado_pdf.get("serie", {}).get("match_encontrado", "")
                    if serie_pdf:
                        print(f"   • SERIE: {serie_pdf}")
                    
                    # Forma de pago
                    forma_pago_pdf = resultado_pdf.get("forma_pago", {}).get("match_encontrado", "")
                    if forma_pago_pdf:
                        print(f"   • FORMA_PAGO: {forma_pago_pdf}")
                    
                    print(f"   • emision Día: {valores_fecha['emision_dia']}")
                    print(f"   • emision Mes: {valores_fecha['emision_mes']}")
                    print(f"   • emision Año: {valores_fecha['emision_año']}")
 
                    # -----------------------------------------------------------------
                    # Excel (mismo proceso de antes)
                    # -----------------------------------------------------------------
                    print("\n🔗 CONSULTANDO EXCEL...")
                    exito = procesar_con_excel(pdf, datos_extraidos, cia_detectada, ramo, tipo_doc)
                    if exito:
                        print("🎉 Procesamiento con Excel EXITOSO")
                    else:
                        print("❌ No se pudo procesar con Excel")
                else:
                    print("⚠️ No se detectó tipo de documento para procesar con Excel")
            else:
                print(f"⚠️ Compañía {cia_detectada} no es GNP - No se procesa con Excel")

            print(f"\n🎯 RESUMEN DOCUMENTO:")
            print(f"   Cía: {cia_detectada}")
            print(f"   Ramo: {ramo}")
            print(f"   Tipo: {tipo_doc}")
            
            if datos_extraidos:
                print(f"   📋 Datos extraídos:")
                for campo, valor in datos_extraidos.items():
                    if valor:
                        print(f"      • {campo.upper()}: {valor}")
            
            if i < len(pdfs):
                input("\n⏎ Presiona ENTER para continuar al siguiente PDF...")
        
        print(f"\n{'='*60}")
        input("⏎ Último PDF - Presiona ENTER para finalizar...")
    
    except Exception as e:
        print(f"❌ Error durante el proceso: {e}")
    finally:
        viewer.cerrar_driver()
    
    print(f"\n{'='*60}")
    print("🎉 TODOS LOS PDFs PROCESADOS")
    print(f"📊 Total: {len(pdfs)} archivos PDF")
    print(f"⚡ Velocidad: Modo MISMA PESTAÑA - Máximo rendimiento")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()