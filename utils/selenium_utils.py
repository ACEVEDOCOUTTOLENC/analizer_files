from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
import time
import os

class FirefoxPDFViewer:
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
        self.setup_driver()
    
    def setup_driver(self):
        """Configura el driver de Firefox UNA SOLA VEZ"""
        try:
            firefox_options = Options()
            
            if self.headless:
                firefox_options.add_argument("--headless")
            
            # Configuración optimizada para PDFs
            firefox_options.set_preference("browser.download.folderList", 2)
            firefox_options.set_preference("browser.download.manager.showWhenStarting", False)
            firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
            firefox_options.set_preference("pdfjs.disabled", False)
            firefox_options.set_preference("browser.tabs.remote.autostart", False)
            
            # OPTIMIZACIONES PARA MÁXIMA VELOCIDAD
            firefox_options.set_preference("browser.startup.homepage", "about:blank")
            firefox_options.set_preference("browser.startup.page", 0)
            firefox_options.set_preference("browser.shell.checkDefaultBrowser", False)
            
            # Deshabilitar cache para forzar recarga
            firefox_options.set_preference("browser.cache.disk.enable", False)
            firefox_options.set_preference("browser.cache.memory.enable", False)
            firefox_options.set_preference("browser.cache.offline.enable", False)
            firefox_options.set_preference("network.http.use-cache", False)
            
            # Usar webdriver-manager
            service = Service(GeckoDriverManager().install())
            self.driver = webdriver.Firefox(service=service, options=firefox_options)
            
            # Maximizar ventana UNA SOLA VEZ
            self.driver.maximize_window()
            print("   ✅ Firefox configurado (MISMA PESTAÑA)")
            
        except Exception as e:
            print(f"   ❌ Error al configurar Firefox: {e}")
            raise
    
    def cambiar_pdf_en_misma_pestana(self, ruta_pdf, numero_pdf, total_pdfs):
        """
        Cambia a un NUEVO PDF en la MISMA pestaña (SUPER RÁPIDO)
        """
        if not self.driver:
            print("   ❌ Firefox no inicializado")
            return
        
        if not os.path.exists(ruta_pdf):
            print(f"   ❌ El archivo PDF no existe: {ruta_pdf}")
            return
        
        try:
            # Convertir ruta a formato URL
            ruta_absoluta = os.path.abspath(ruta_pdf)
            url_pdf = f"file:///{ruta_absoluta}".replace('\\', '/')
            
            print(f"   📂 [{numero_pdf}/{total_pdfs}] Cargando: {os.path.basename(ruta_pdf)}")
            
            # NAVEGAR DIRECTAMENTE al nuevo PDF en la MISMA pestaña
            self.driver.get(url_pdf)
            
            # Espera mínima para que cargue (puedes ajustar este tiempo)
            time.sleep(1.5)
            
            print(f"   ✅ PDF cargado - Presiona ENTER para siguiente...")
            
        except Exception as e:
            print(f"   ❌ Error al cargar el PDF: {e}")
    
    def mantener_ventana_abierta(self):
        """Mantiene la ventana abierta entre documentos"""
        # No hace nada - la ventana ya está abierta
        pass
    
    def cerrar_driver(self):
        """Cierra Firefox completamente (solo al final)"""
        if self.driver:
            self.driver.quit()
            print("   ✅ Firefox cerrado")