import tkinter as tk
from tkinter import ttk
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import io
import os
import threading
from tkinter import Button
import queue
import time
from tkinter import simpledialog  # ✅ para poder editar texto después
import sys


config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
if config_path not in sys.path:
    sys.path.append(config_path)

try:
    from tipos_documento import TIPOS_DOCUMENTO
    print("✅ Tipos de documento importados correctamente")
except ImportError as e:
    print(f"❌ Error importando tipos de documento: {e}")
    TIPOS_DOCUMENTO = {
        "poliza": {"campos": []},
        "recibo": {"campos": []},
        "endoso": {"campos": []},
        "recibo_endoso": {"campos": []},
        "nota_credito": {"campos": []},
        "factura": {"campos": []}
    }

class VisorPDF:
    def __init__(self, pdf_path=None, on_click_callback=None):
        self.pdf_path = pdf_path
        self.on_click_callback = on_click_callback
        self.visor_activo = False
        self.doc = None
        self.root = None
        self.cmd_queue = queue.Queue()  # Comunicación con el hilo del visor
        self.selection_queue = queue.Queue()
        self.thread = None
        self.zoom = 1.5
        self._image_ref = None  # Evita que Tkinter borre la imagen
        self.pagina_actual = 0  # Agregado para evitar errores

    def abrir(self):
        """Inicia el visor en un hilo separado (no bloqueante)."""
        if self.thread and self.thread.is_alive():
            print("⚠️ El visor ya está abierto.")
            return True
    
        print("🖥️ Iniciando visor gráfico en hilo separado...")
        self.thread = threading.Thread(target=self._run_visor, daemon=True)
        self.thread.start()
    
        # Esperar hasta que el visor esté activo (máx. 2.5 segundos)
        for _ in range(50):
            if getattr(self, "visor_activo", False):
                print("✅ Visor gráfico iniciado correctamente.")
                return True
            time.sleep(0.05)
    
        print("❌ Error: el visor gráfico no pudo iniciarse correctamente.")
        return False
    
    def _run_visor(self):
        """Hilo principal del visor gráfico PDF."""
        try:
            print("🖥️ Lanzando interfaz gráfica del visor PDF...")
            self.visor_activo = False  # por si se setea antes del ready
            self.root = tk.Tk()
            self.root.title("🎯 Visor PDF")
            self.root.geometry("1000x800")
            self.root.protocol("WM_DELETE_WINDOW", self._on_close_click)
    
            # Crear interfaz
            self._setup_ui()
    
            # Marcar visor como activo (ya inicializado)
            self.visor_activo = True
            print("✅ Interfaz del visor iniciada correctamente.")
    
            # Si ya hay un PDF, abrirlo
            if self.pdf_path and os.path.exists(self.pdf_path):
                self._abrir_documento(self.pdf_path)
    
            # Bucle principal del visor
            while self.visor_activo:
                try:
                    cmd, arg = self.cmd_queue.get_nowait()
                    if cmd == "cambiar":
                        self._abrir_documento(arg)
                    elif cmd == "cerrar":
                        print("🧹 Cerrando visor por comando remoto...")
                        break
                except queue.Empty:
                    pass
    
                # Refrescar GUI
                self.root.update_idletasks()
                self.root.update()
                time.sleep(0.02)
    
        except Exception as e:
            import traceback
            print(f"❌ Error crítico en hilo del visor: {type(e).__name__}: {e}")
            traceback.print_exc()
    
        finally:
            # Limpieza segura
            try:
                if hasattr(self, "doc") and self.doc:
                    self.doc.close()
                if hasattr(self, "root") and self.root:
                    self.root.destroy()
                print("👋 Visor cerrado correctamente.")
            except Exception as cleanup_error:
                print(f"⚠️ Error al cerrar visor: {cleanup_error}")
            finally:
                self.visor_activo = False

    def cambiar_documento(self, nueva_pdf_path):
       """Cambia el documento mostrado (seguro)."""
       if not self.visor_activo:
           print("⚠️ El visor no está activo. Intentando reiniciarlo...")
           if not self.abrir():
               print("❌ No se pudo reiniciar el visor.")
               return False
       self.cmd_queue.put(("cambiar", nueva_pdf_path))
       return True

    def cerrar(self):
        """Cierra el visor de forma controlada (no bloqueante)."""
        if not self.visor_activo:
            return
        print("🧹 Enviando comando de cierre al visor...")
        self.cmd_queue.put(("cerrar", None))

    def _setup_ui(self):
        # ====== Marco principal ======
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ====== SECCIÓN DE TIPOS DE DOCUMENTO ======
        doc_types_frame = ttk.Frame(main_frame)
        doc_types_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(doc_types_frame, text="Tipo de documento:", 
                 font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)

        # ✅ USAR TIPOS DESDE CONFIGURACIÓN
        tipos = list(TIPOS_DOCUMENTO.keys())
        for tipo in tipos:
            # Mostrar en mayúsculas para mejor legibilidad pero enviar el original
            texto_boton = tipo.upper()
            ttk.Button(doc_types_frame, text=texto_boton, 
                      command=lambda t=tipo: self._enviar_evento(f'tipo_documento:{t}')).pack(side=tk.LEFT, padx=2)
    
        # ====== Controles superiores ======
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
    
        ttk.Button(controls_frame, text="← Anterior", command=self._pagina_anterior).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Siguiente →", command=self._siguiente_pagina).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="⏭️ Saltar documento", command=lambda: self._enviar_evento('saltar_documento')).pack(side=tk.RIGHT, padx=5)
    
        self.pagina_label = ttk.Label(controls_frame, text="")
        self.pagina_label.pack(side=tk.LEFT, padx=20)
    
        self.estado_label = ttk.Label(controls_frame, text="🟢 VISOR ACTIVO", foreground="green")
        self.estado_label.pack(side=tk.RIGHT)
    
        # ====== Canvas principal (visor PDF) ======
        self.canvas = tk.Canvas(main_frame, bg="white", cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)
    
        # ====== Scrollbars ======
        v_scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar = ttk.Scrollbar(main_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
    
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
    
        # ✅ Activamos el nuevo sistema de selección rectangular (drag para capturar texto)
        self._configurar_eventos_mouse()
    
        print("🟦 Sistema de selección rectangular activado correctamente.")
        print(f"🟦 Botones de tipos de documento cargados: {len(tipos)} tipos")

    def _enviar_evento(self, evento):
        """Envía un evento al callback principal (por ejemplo, 'saltar_documento')."""
        if callable(self.on_click_callback):
            print(f"📩 Enviando evento al controlador: {evento}")
            self.on_click_callback(evento)

    # ==========================
    # LÓGICA DE PÁGINAS
    # ==========================
    def _abrir_documento(self, path):
        """
        Abre y carga un PDF en el visor.
        Devuelve True si la operación tuvo éxito, False en caso de error.
        """
        try:
            # Validar existencia del archivo
            if not os.path.exists(path):
                print(f"❌ Archivo no encontrado: {path}")
                return False
    
            # Cerrar documento anterior si existe
            if hasattr(self, "doc") and self.doc:
                try:
                    self.doc.close()
                except Exception:
                    pass
    
            # Abrir nuevo documento
            self.doc = fitz.open(path)
            self.pdf_path = path
            self.pagina_actual = 0
    
            # Asegurar valor por defecto de zoom
            if not hasattr(self, "zoom") or self.zoom is None:
                self.zoom = 1.5
    
            # Actualizar título de la ventana (si la UI ya está creada)
            try:
                if self.root:
                    self.root.title(f"🎯 Visor PDF - {os.path.basename(path)}")
            except Exception:
                pass
    
            # Mostrar página inicial en canvas (si UI creada)
            try:
                self._mostrar_pagina()
            except Exception as e:
                # Si por alguna razón no puede renderizar ahora, cerramos el doc y reportamos
                try:
                    self.doc.close()
                except Exception:
                    pass
                self.doc = None
                print(f"❌ Error al mostrar la primera página: {e}")
                return False
    
            print(f"✅ Documento cargado: {os.path.basename(path)}")
            return True
    
        except Exception as e:
            # Error general al abrir el PDF
            print(f"❌ Error al abrir documento: {e}")
            # Asegurar estado limpio
            try:
                if hasattr(self, "doc") and self.doc:
                    self.doc.close()
            except Exception:
                pass
            self.doc = None
            return False

    
    def _mostrar_pagina(self):
        if not self.doc:
            return
        pagina = self.doc[self.pagina_actual]
        mat = fitz.Matrix(self.zoom, self.zoom)
        pix = pagina.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("ppm")))
        self._image_ref = ImageTk.PhotoImage(img)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self._image_ref)
        self.canvas.configure(scrollregion=self.canvas.bbox(tk.ALL))
        self.pagina_label.config(text=f"Página {self.pagina_actual + 1} / {len(self.doc)}")

    def _siguiente_pagina(self):
        if self.doc and self.pagina_actual < len(self.doc) - 1:
            self.pagina_actual += 1
            self._mostrar_pagina()

    def _pagina_anterior(self):
        if self.doc and self.pagina_actual > 0:
            self.pagina_actual -= 1
            self._mostrar_pagina()

    # ==========================
    # EVENTOS
    # ==========================
    def _on_canvas_click(self, event):
        if not (self.doc and self.on_click_callback):
            return
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        x_pdf, y_pdf = x / self.zoom, y / self.zoom
        texto = self._extraer_texto(x_pdf, y_pdf)
        self.on_click_callback({
            'texto': texto,
            'coordenadas': {'x': x_pdf, 'y': y_pdf, 'pagina': self.pagina_actual}
        })

    def extraer_texto_en_area(self, rect):
        """
        Extrae el texto del área seleccionada en el visor (coordenadas del canvas)
        transformándolas a coordenadas del PDF.
        """
        if not self.doc:
            return ""
    
        pagina = self.doc[self.pagina_actual]
    
        # Tamaño real del PDF
        pdf_width, pdf_height = pagina.rect.width, pagina.rect.height
    
        # Tamaño actual del canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
    
        # Factores de escala (canvas → PDF)
        scale_x = pdf_width / canvas_width
        scale_y = pdf_height / canvas_height
    
        x0, y0, x1, y1 = rect
        pdf_rect = fitz.Rect(
            x0 * scale_x,
            y0 * scale_y,
            x1 * scale_x,
            y1 * scale_y
        )
    
        texto = pagina.get_text("text", clip=pdf_rect)
        return texto.strip()

    def _on_close_click(self):
        """Cierre seguro desde la ventana."""
        print("\n🧩 Cerrando visor desde la ventana.")
        self.visor_activo = False
        self.root.destroy()

    def actualizar_estado(self, mensaje, color="black"):
        """Actualiza el texto de estado del visor de forma segura"""
        try:
            if self.estado_label:
                self.estado_label.after(0, lambda: self.estado_label.config(text=mensaje, foreground=color))
        except Exception as e:
            print(f"⚠️ No se pudo actualizar el estado del visor ({e})")

    def mantener_abierto(self):
        """
        Mantiene el visor abierto mientras siga activo.
        Puede usarse como una pausa controlada desde otros procesos.
        """
        try:
            while self.visor_activo:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.cerrar()
            
    # ==============================================
    # 🚀 SISTEMA DE CAPTURA CON RECTÁNGULO VISUAL
    # ==============================================
    def _configurar_eventos_mouse(self):
        """Configura los eventos para selección rectangular visual"""
        self.canvas.bind("<ButtonPress-1>", self._iniciar_seleccion)
        self.canvas.bind("<B1-Motion>", self._dibujar_rectangulo)
        self.canvas.bind("<ButtonRelease-1>", self._finalizar_seleccion)
        self.rect_id = None
        self.overlay_id = None
        self.start_x = None
        self.start_y = None
        # 🔹 Vinculamos al callback original
        self.callback_click = self.on_click_callback
    
    def _iniciar_seleccion(self, event):
        """Inicio del arrastre del rectángulo de selección (usar coordenadas de canvas)."""
        # convertir a coords del canvas (toma en cuenta scroll)
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
    
        # eliminar rectángulo anterior si existe
        if getattr(self, "rect_id", None):
            try: self.canvas.delete(self.rect_id)
            except: pass
        if getattr(self, "overlay_id", None):
            try: self.canvas.delete(self.overlay_id)
            except: pass
    
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="#007BFF", width=2, dash=(3, 2)
        )
        self.overlay_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            fill="#007BFF", stipple="gray25", outline=""
        )

    def _dibujar_rectangulo(self, event):
        """Dibuja dinámicamente el rectángulo mientras arrastras (usar canvas coords)."""
        if not getattr(self, "rect_id", None):
            return
        curX = self.canvas.canvasx(event.x)
        curY = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, curX, curY)
        if getattr(self, "overlay_id", None):
            self.canvas.coords(self.overlay_id, self.start_x, self.start_y, curX, curY)
    
    def _finalizar_seleccion(self, event):
        """Cuando se suelta el botón: capturar texto dentro del área."""
        if not hasattr(self, "start_x") or not hasattr(self, "start_y"):
            return
    
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        rect_canvas = (
            min(self.start_x, end_x),
            min(self.start_y, end_y),
            max(self.start_x, end_x),
            max(self.start_y, end_y)
        )
    
        # Convertir canvas(px) -> PDF pts usando zoom
        x0_pdf = rect_canvas[0] / self.zoom
        y0_pdf = rect_canvas[1] / self.zoom
        x1_pdf = rect_canvas[2] / self.zoom
        y1_pdf = rect_canvas[3] / self.zoom
        rect_pdf = fitz.Rect(x0_pdf, y0_pdf, x1_pdf, y1_pdf)
    
        # Extraer texto (llamamos a la función que usa rect en pts)
        texto = ""
        try:
            texto = self.doc.load_page(self.pagina_actual).get_text("text", clip=rect_pdf).strip()
            texto = texto.replace("\n", " ").strip()
        except Exception as e:
            print(f"⚠️ Error extrayendo texto del área: {e}")
    
        coordenadas = {
            "pagina": self.pagina_actual,
            "area_pdf": {"x0": x0_pdf, "y0": y0_pdf, "x1": x1_pdf, "y1": y1_pdf},
            "area_canvas": {"x0": rect_canvas[0], "y0": rect_canvas[1], "x1": rect_canvas[2], "y1": rect_canvas[3]},
        }
    
        datos_click = {"texto": texto, "coordenadas": coordenadas}
    
        # En lugar de bloquear o pedir input, dejamos el dato para que la hebra principal lo procese.
        # callback debe ser no bloqueante y solo encolar/almacenar datos.
        if self.callback_click:
            try:
                # Envolvemos en after(0) para evitar llamadas extrañas desde eventos complejos
                self.root.after(0, lambda: self.callback_click(datos_click))
            except Exception:
                # fallback directo si after no funciona
                try:
                    self.callback_click(datos_click)
                except Exception as e:
                    print(f"⚠️ callback fallo: {e}")
    
        # Confirmación visual
        if hasattr(self, "rect_id") and self.rect_id:
            self.canvas.itemconfig(self.rect_id, outline="green", dash=())
        if hasattr(self, "overlay_id") and self.overlay_id:
            self.canvas.itemconfig(self.overlay_id, fill="green", stipple="gray25")
        confirm_text = self.canvas.create_text(
            (rect_canvas[0] + rect_canvas[2]) / 2,
            (rect_canvas[1] + rect_canvas[3]) / 2 - 10,
            text="✅ Capturado",
            fill="green",
            font=("Arial", 12, "bold")
        )
        self.canvas.after(1000, lambda: self.canvas.delete(confirm_text))

    def extraer_text_en_area(self, rect_canvas):
        """
        rect_canvas: (x0, y0, x1, y1) en pixeles del canvas (coinciden con pixmap)
        Devuelve texto usando rect en coordenadas PDF (pts).
        """
        if not self.doc:
            return ""
        try:
            page = self.doc.load_page(self.pagina_actual)
            x0, y0, x1, y1 = rect_canvas
            # convertir a pts:
            x0_pdf = x0 / self.zoom
            y0_pdf = y0 / self.zoom
            x1_pdf = x1 / self.zoom
            y1_pdf = y1 / self.zoom
            texto = page.get_text("text", clip=fitz.Rect(x0_pdf, y0_pdf, x1_pdf, y1_pdf))
            return texto.strip()
        except Exception as e:
            print(f"⚠️ Error al extraer texto del área: {e}")
            return ""