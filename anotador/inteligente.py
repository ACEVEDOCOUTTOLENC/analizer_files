import json
import datetime
import fitz  # PyMuPDF
import os


class AnotadorInteligente:
    def __init__(self, pdf_path, datos_entrenamiento_path="datos_entrenamiento.json"):
        self.pdf_path = pdf_path
        self.datos_entrenamiento_path = datos_entrenamiento_path
        self.doc = fitz.open(pdf_path)
        self.tipo_documento = None
        self.campos_por_anotar = []
        self.anotaciones_actuales = {}
        self.compania = None
        self.ramo = None

        # 🆕 Lista temporal de documentos anotados en este PDF
        self.documentos_en_pdf = []

        # Configuración de tipos de documento
        try:
            from config.tipos_documento import TIPOS_DOCUMENTO
            self.TIPOS_DOCUMENTO = TIPOS_DOCUMENTO
        except ImportError:
            self.TIPOS_DOCUMENTO = {
                "poliza": {"campos": ["label1", "label2", "numero_poliza", "fecha_expedicion", "nombre_asegurado"]},
                "recibo": {"campos": ["label1", "label2", "forma_pago", "numero_poliza", "serie"]},
                "endoso": {"campos": ["label1", "label2", "fecha_expedicion", "numero_poliza"]},
                "recibo_endoso": {"campos": ["label1", "label2", "numero_poliza", "forma_pago", "serie"]},
                "nota_credito": {"campos": ["label1", "label2", "numero_poliza"]},
                "factura": {"campos": ["label1", "label2", "numero_poliza"]}
            }

        self.cargar_datos_entrenamiento()

    # ----------------------------------------------------------------------
    # 🧱 CONFIGURACIÓN BÁSICA
    # ----------------------------------------------------------------------
    def set_metadata(self, compania, ramo):
        """🆕 Establece metadatos del documento"""
        self.compania = compania
        self.ramo = ramo

    def set_tipo_documento(self, tipo_documento):
        """Establece el tipo de documento y carga sus campos"""
        self.tipo_documento = tipo_documento
        if tipo_documento in self.TIPOS_DOCUMENTO:
            self.campos_por_anotar = self.TIPOS_DOCUMENTO[tipo_documento]["campos"][:]
        else:
            self.campos_por_anotar = []

    # ----------------------------------------------------------------------
    # 🧠 ANOTACIÓN Y EXTRACCIÓN
    # ----------------------------------------------------------------------
    def agregar_anotacion(self, campo, texto, coordenadas):
        """Agrega una anotación manual"""
        self.anotaciones_actuales[campo] = {
            "texto": texto,
            "coordenadas": coordenadas,
            "confianza": 1.0
        }
        if campo in self.campos_por_anotar:
            self.campos_por_anotar.remove(campo)

    def extraer_texto_en_coordenadas(self, x, y, pagina_num, ancho=100, alto=50):
        """Extrae texto de un área específica del PDF"""
        pagina = self.doc[pagina_num]
        rect = fitz.Rect(x, y, x + ancho, y + alto)
        return pagina.get_text("text", clip=rect).strip()

    # ----------------------------------------------------------------------
    # 🆕 NUEVA LÓGICA DE MÚLTIPLES DOCUMENTOS
    # ----------------------------------------------------------------------
    def guardar_anotacion_actual(self, hojas=None):
        """
        🆕 Guarda la anotación actual y pregunta si quiere anotar otro documento
        """
        if not self.tipo_documento:
            print("⚠️ No se ha definido el tipo de documento.")
            return False
        if not self.anotaciones_actuales:
            print("⚠️ No hay campos anotados para este documento.")
            return False
    
        if hojas is None:
            try:
                paginas_input = input("📄 Ingrese las páginas correspondientes a este documento (ej. 1-3 o 2): ").strip()
                if "-" in paginas_input:
                    inicio, fin = map(int, paginas_input.split("-"))
                    hojas = list(range(inicio, fin + 1))
                else:
                    hojas = [int(paginas_input)]
            except Exception as e:
                print(f"❌ Error procesando páginas: {e}")
                hojas = []
    
        # Guardar el documento actual
        success = self.agregar_documento_actual(hojas)
        
        if success:
            print("\n" + "="*50)
            print("🎉 DOCUMENTO GUARDADO EXITOSAMENTE")
            print("="*50)
            
            # 🆕 PREGUNTAR SI QUIERE ANOTAR OTRO DOCUMENTO EN EL MISMO PDF
            while True:
                otro_documento = input("\n¿Quieres anotar OTRO documento en este mismo PDF? (s/n): ").strip().lower()
                if otro_documento in ['s', 'si', 'sí', 'y', 'yes']:
                    # 🆕 REINICIAR ESTADO PARA NUEVA ANOTACIÓN
                    self.reiniciar_para_nueva_anotacion()
                    return True  # Continuar en el mismo PDF
                elif otro_documento in ['n', 'no']:
                    print("➡️ Pasando al siguiente PDF...")
                    return False  # Pasar al siguiente PDF
                else:
                    print("❌ Por favor responde 's' o 'n'")
        
        return False
        
    def agregar_documento_actual(self, paginas):
        """
        🆕 Agrega el documento actual a la lista temporal de documentos en este PDF
        """
        if not self.tipo_documento:
            print("❌ No se puede agregar documento: tipo no definido")
            return False
        
        if not self.anotaciones_actuales:
            print("❌ No se puede agregar documento: no hay anotaciones")
            return False
    
        # Crear documento con la estructura correcta
        documento = {
            "tipo": self.tipo_documento,
            "paginas": paginas,
            "campos": self.anotaciones_actuales.copy(),
            "metadata": {
                "compania": self.compania,
                "ramo": self.ramo,
                "fecha_anotacion": datetime.datetime.now().isoformat()
            }
        }
        
        self.documentos_en_pdf.append(documento)
        print(f"✅ Documento '{self.tipo_documento}' agregado (páginas {paginas})")
        
        return True
        
    def guardar_pdf_completo(self):
        """
        🆕 Guarda todos los documentos de este PDF en el archivo de entrenamiento.
        """
        if not self.documentos_en_pdf:
            print("⚠️ No hay documentos para guardar en este PDF.")
            return

        anotacion_final = {
            "archivo": {
                "ruta_archivo": self.pdf_path,
                "nombre_archivo": os.path.basename(self.pdf_path),
                "compania": self.compania,
                "ramo": self.ramo,
                "fecha_anotacion": datetime.datetime.now().isoformat(),
                "total_paginas": len(self.doc),
                "documentos": self.documentos_en_pdf
            },
            "metadata_entrenamiento": {
                "anotado_por": "usuario",
                "fecha_entrenamiento": datetime.datetime.now().isoformat(),
                "version_modelo": "v1.0"
            }
        }

        # Agregar al dataset y guardar
        self.datos_entrenamiento["anotaciones"].append(anotacion_final)
        self.datos_entrenamiento["ejemplos_anotados"] = len(self.datos_entrenamiento["anotaciones"])

        with open(self.datos_entrenamiento_path, 'w', encoding='utf-8') as f:
            json.dump(self.datos_entrenamiento, f, indent=2, ensure_ascii=False)

        print(f"💾 PDF completo guardado con {len(self.documentos_en_pdf)} documentos.")
        self.documentos_en_pdf = []  # Limpia para el siguiente PDF

    # ----------------------------------------------------------------------
    # 🧰 UTILIDADES
    # ----------------------------------------------------------------------
    def cargar_datos_entrenamiento(self):
        """Carga datos de entrenamiento existentes"""
        try:
            with open(self.datos_entrenamiento_path, 'r', encoding='utf-8') as f:
                self.datos_entrenamiento = json.load(f)
        except FileNotFoundError:
            self.datos_entrenamiento = {"ejemplos_anotados": 0, "anotaciones": []}

    def cerrar_documento(self):
        """Cierra el documento PDF"""
        if hasattr(self, 'doc'):
            self.doc.close()



    def reiniciar_para_nueva_anotacion(self):
        """
        🆕 Reinicia el estado para comenzar una nueva anotación en el mismo PDF
        """
        print("\n" + "🔄 REINICIANDO PARA NUEVO DOCUMENTO")
        print("="*40)
        
        # Conservar metadata del PDF (compañía, ramo)
        compania_temp = self.compania
        ramo_temp = self.ramo
        
        # Reiniciar estado de anotación actual
        self.tipo_documento = None
        self.campos_por_anotar = []
        self.anotaciones_actuales = {}
        
        # Restaurar metadata
        self.compania = compania_temp
        self.ramo = ramo_temp
        
        print("✅ Estado reiniciado. Listo para nuevo documento.")
        print(f"📊 Documentos anotados en este PDF hasta ahora: {len(self.documentos_en_pdf)}")