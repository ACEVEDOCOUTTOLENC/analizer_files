import os
from anotador.visor_pdf import VisorPDF
from config.tipos_documento import TIPOS_DOCUMENTO
import threading
import queue
import time

class InterfazAnotadorConsola:
    def __init__(self):
        self.anotador = None
        self.visor = None
        self.campo_actual = None
        
    def iniciar_visor_continuo(self, primer_pdf_path):
        """Inicia el visor una vez al principio y permanece abierto"""
        print("🎯 Iniciando visor continuo...")
        self.visor = VisorPDF(primer_pdf_path, on_click_callback=self.on_click_capturado)
        self.visor.abrir()
        return self.visor.visor_activo
    
    def cambiar_documento_en_visor(self, nueva_pdf_path):
        """Cambia el documento en el visor existente"""
        if self.visor and self.visor.visor_activo:
            return self.visor.cambiar_documento(nueva_pdf_path)
        return False
    
    def ejecutar_anotacion_continua(self, anotador, compania_detectada=None, ramo=None):
        """
        Ejecuta anotación continua - selección de tipo desde el visor
        """
        continuar_en_mismo_pdf = True
        documentos_anotados = 0
        
        while continuar_en_mismo_pdf:
            try:
                # RESETEAR banderas
                self.saltar_documento = False
                self.tipo_seleccionado = None
                
                print(f"\n🎯 INICIANDO DOCUMENTO #{documentos_anotados + 1} EN ESTE PDF")
                print("=" * 50)
                
                # 🎯 SOLO VISOR - Esperar selección de tipo desde el visor
                print("📋 ESPERANDO SELECCIÓN EN VISOR...")
                print("💡 Usa los botones en el visor para seleccionar el tipo de documento")
                
                # Actualizar estado del visor
                try:
                    self.visor.actualizar_estado("📋 Selecciona el tipo de documento", "blue")
                except:
                    pass
                
                # Esperar hasta que se seleccione un tipo o se salte
                start_time = time.time()
                while self.tipo_seleccionado is None and not self.saltar_documento:
                    # Timeout de seguridad (5 minutos) por si hay algún problema
                    if time.time() - start_time > 300:
                        print("⏰ Timeout - usando POLIZA por defecto")
                        self.tipo_seleccionado = "poliza"
                    time.sleep(0.1)
                
                # Verificar si se saltó
                if self.saltar_documento:
                    print("⏭️ Saltando documento por solicitud del usuario...")
                    return False
                
                # Configurar el tipo seleccionado
                anotador.set_tipo_documento(self.tipo_seleccionado)
                print(f"✅ Tipo seleccionado: {self.tipo_seleccionado.upper()}")
                
                # Actualizar estado del visor
                try:
                    self.visor.actualizar_estado(f"✅ Anotando: {self.tipo_seleccionado.upper()}", "green")
                except:
                    pass
                
                # Anotar campos
                resultado_anotacion = self.anotar_campos_con_visor(anotador)
                
                if not resultado_anotacion:
                    print("⏭️ Saltando a siguiente PDF por botón...")
                    return False
                
                # Si llegamos aquí: ANOTACIÓN COMPLETADA EXITOSAMENTE
                continuar_en_mismo_pdf = anotador.guardar_anotacion_actual()
                documentos_anotados += 1
                
                # 🆕 INTEGRAR EXCEL PROCESSOR (solo si tenemos los datos necesarios)
                if compania_detectada and ramo:
                    try:
                        # Importar dinámicamente para evitar errores si no está disponible
                        import importlib.util
                        import os
                        import sys
                        
                        # Buscar excel_processor.py en diferentes ubicaciones posibles
                        posibles_rutas = [
                            os.path.join(os.path.dirname(__file__), '..', 'excel_processor.py'),
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'excel_processor.py'),
                            'excel_processor.py'
                        ]
                        
                        excel_processor_path = None
                        for ruta in posibles_rutas:
                            if os.path.exists(ruta):
                                excel_processor_path = ruta
                                break
                        
                        if excel_processor_path and os.path.exists(excel_processor_path):
                            print(f"🔍 Encontrado Excel processor en: {excel_processor_path}")
                            spec = importlib.util.spec_from_file_location("excel_processor", excel_processor_path)
                            excel_module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(excel_module)
                            
                            # Preparar datos para el Excel processor
                            datos_para_excel = self._preparar_datos_para_excel(anotador, compania_detectada, ramo)
                            
                            # Llamar al Excel processor
                            if excel_module.procesar_con_excel(anotador.pdf_path, datos_para_excel, compania_detectada, ramo, anotador.tipo_documento):
                                print("📦 Archivo renombrado y movido exitosamente")
                            else:
                                print("⚠️ No se pudo procesar con Excel (continuando igual)")
                        else:
                            print("⚠️ Excel processor no encontrado")
                            
                    except Exception as e:
                        print(f"⚠️ Error en Excel processor: {e}")
                        import traceback
                        traceback.print_exc()
                        # No bloquear el flujo principal si falla el Excel processor
                else:
                    print("ℹ️  Datos insuficientes para Excel processor")
                
                if continuar_en_mismo_pdf:
                    print(f"🔄 Continuando con otro documento... (llevas {documentos_anotados})")
                else:
                    print(f"📦 Se anotaron {documentos_anotados} documentos en este PDF")
                    return True
                    
            except Exception as e:
                print(f"❌ Error durante anotación: {e}")
                import traceback
                traceback.print_exc()
                print("🔄 Reintentando documento debido a error...")
        
        return documentos_anotados > 0
                               
    def mostrar_pista_campo(self, campo):
        """Muestra pistas sobre dónde encontrar cada campo"""
        pistas = {
            "numero_poliza": "Busca en el encabezado, usualmente con formato como 'Póliza No.' o 'Número de Póliza'",
            "fecha_expedicion": "Busca en el encabezado o pie de página, formato 'Fecha de Expedición'",
            "nombre_asegurado": "Busca en la sección de datos del asegurado, 'Nombre del Asegurado'",
            "forma_pago": "Busca en detalles de pago, 'Forma de Pago' o condiciones",
            "serie": "Busca números de serie en encabezados o códigos de barras",
            "endoso": "Busca 'Endoso No.' o números de endoso"
        }   

    def cerrar_visor(self):
        """Cierra el visor al final de todo"""
        if self.visor:
            self.visor.cerrar()
            print("👋 Visor cerrado") 
    
    def anotar_campos_con_visor(self, anotador):
        """Anota campos usando el visor continuo con espera unificada"""
        print(f"\n🎯 ANOTANDO CAMPOS PARA: {anotador.tipo_documento.upper()}")
        print("-" * 50)
    
        # Variables para controlar el flujo
        self.campo_capturado_event = threading.Event()
        self._ultimo_click = None
        self.saltar_documento = False  # Nueva bandera para saltar
    
        for campo in anotador.campos_por_anotar[:]:
            # Verificar si se solicitó saltar el documento
            if self.saltar_documento:
                print("⏭️ Saltando documento por solicitud del usuario...")
                break
    
            print(f"\n📌 Campo actual: {campo}")
            print("💡 Haz clic en el visor donde aparece este campo")
            self.mostrar_pista_campo(campo)
    
            self.campo_actual = campo
    
            try:
                self.visor.actualizar_estado(f"🎯 Haz clic en: {campo}", "orange")
            except Exception as e:
                print(f"⚠️ No se pudo actualizar el estado del visor ({e})")
    
            print("⌛ Esperando clic en el visor (o presiona 'Saltar documento' en el visor)...")
            
            # Espera por evento (clic o saltar) con timeout
            self.campo_capturado_event.clear()
            self.campo_capturado_event.wait(timeout=300)  # 5 minutos de timeout
    
            # Verificar si se solicitó saltar durante la espera
            if self.saltar_documento:
                print("⏭️ Saltando documento por solicitud del usuario...")
                break
    
            # Si no hay datos del clic, continuar con el siguiente campo
            datos = getattr(self, "_ultimo_click", None)
            if not datos:
                print("⚠️ No se recibió información del visor, saltando campo.")
                continue
    
            # Procesar el texto capturado
            texto_detectado = datos.get("texto", "").strip()
            print(f"\n📦 Texto extraído para {campo}:")
            print(f"👉 {texto_detectado if texto_detectado else '[VACÍO]'}")
            nuevo = input("✏️ Si deseas editar el texto, escríbelo; de lo contrario presiona Enter para aceptar:\n→ ").strip()
            texto_final = nuevo if nuevo != "" else texto_detectado
    
            coordenadas = datos.get("coordenadas", {})
            anotador.agregar_anotacion(campo, texto_final, coordenadas)
            print(f"✅ {campo} guardado: '{texto_final}'")
    
            try:
                self.visor.actualizar_estado(f"✅ {campo} capturado", "green")
            except Exception:
                pass
    
        # Limpiar anotaciones si se saltó el documento
        if self.saltar_documento:
            anotador.anotaciones_actuales = {}
            print("🗑️ Anotaciones descartadas por salto de documento")
            return False  # Indicar que se saltó el documento
        else:
            print("\n🎉 Todos los campos anotados.\n")
            return True  # Indicar que se completó la anotación

    def on_click_capturado(self, datos):
        """
        Maneja TODOS los eventos del visor - tipos de documento, saltar, y clics en PDF
        """
        print(f"🔵 Evento recibido del visor: {type(datos)} - {datos}")
        
        # Si es un evento de botón (string)
        if isinstance(datos, str):
            if datos == "saltar_documento":
                print("🟡 Botón presionado: saltar documento")
                self.saltar_documento = True
                # Liberar eventos de espera
                if hasattr(self, "campo_capturado_event") and self.campo_capturado_event:
                    self.campo_capturado_event.set()
                    
            elif datos.startswith("tipo_documento:"):
                tipo_seleccionado = datos.split(":")[1]
                print(f"🟡 Tipo de documento seleccionado: {tipo_seleccionado}")
                self.tipo_seleccionado = tipo_seleccionado
                
            return
        
        # Si es un clic en el PDF (dict con texto y coordenadas)
        elif isinstance(datos, dict):
            print("🟡 Clic capturado en PDF - texto extraído")
            self._ultimo_click = datos
            if hasattr(self, "campo_capturado_event") and self.campo_capturado_event:
                self.campo_capturado_event.set()
                      
                
    def _preparar_datos_para_excel(self, anotador, compania_detectada, ramo):
        """Prepara los datos extraídos para el Excel processor"""
        datos = {}
        
        # Mapear campos de anotación a campos que espera el Excel processor
        mapeo_campos = {
            'numero_poliza': 'poliza',
            'forma_pago': 'forma_pago', 
            'serie': 'serie',
            'endoso': 'endoso',
            'fecha_expedicion': 'fecha_emision'
        }
        
        for campo_anotacion, campo_excel in mapeo_campos.items():
            if campo_anotacion in anotador.anotaciones_actuales:
                datos[campo_excel] = anotador.anotaciones_actuales[campo_anotacion].get('texto', '')
        
        # Agregar metadata
        datos['compania'] = compania_detectada
        datos['ramo'] = ramo
        
        print(f"📊 Datos preparados para Excel: {datos}")
        return datos