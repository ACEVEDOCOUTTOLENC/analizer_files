from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
import time
import os
import subprocess

class FirefoxPDFViewer:
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
        self.setup_driver()
    
    def setup_driver(self):
        """Configuración MÍNIMA ABSOLUTA - SIN webdriver-manager"""
        try:
            print("   🧹 Limpiando procesos anteriores...")
            subprocess.run(["pkill", "-f", "firefox"], capture_output=True)
            subprocess.run(["pkill", "-f", "geckodriver"], capture_output=True)
            time.sleep(3)
            
            firefox_options = Options()
            
            # SOLO una opción esencial
            if self.headless:
                firefox_options.add_argument("--headless")
            
            # SOLO una preferencia esencial
            firefox_options.set_preference("pdfjs.disabled", False)
            
            # NADA MÁS - configuración mínima absoluta
            print("   🔧 Inicializando Firefox ESR...")
            
            # Usar SOLO GeckoDriver del sistema, SIN webdriver-manager
            service = Service("/usr/local/bin/geckodriver")
            
            self.driver = webdriver.Firefox(
                service=service, 
                options=firefox_options
            )
            
            print("   ✅ Firefox ESR inicializado (CONFIGURACIÓN MÍNIMA)")
            
        except Exception as e:
            print(f"   ❌ Error CRÍTICO: {e}")
            self._last_resort()
    
    def _last_resort(self):
        """Último recurso: diagnóstico completo"""
        print("   🚨 EJECUTANDO DIAGNÓSTICO COMPLETO:")
        
        # Verificar Firefox
        result = subprocess.run(["which", "firefox-esr"], capture_output=True, text=True)
        print(f"      Firefox ESR path: {result.stdout.strip()}")
        
        # Verificar GeckoDriver
        result = subprocess.run(["which", "geckodriver"], capture_output=True, text=True)
        print(f"      GeckoDriver path: {result.stdout.strip()}")
        
        # Verificar permisos
        result = subprocess.run(["ls", "-la", "/usr/local/bin/geckodriver"], capture_output=True, text=True)
        print(f"      GeckoDriver permisos: {result.stdout.strip()}")
        
        # Verificar espacio en disco
        result = subprocess.run(["df", "-h", "/tmp"], capture_output=True, text=True)
        print(f"      Espacio en /tmp: {result.stdout.strip().split()[-2] if result.stdout else 'N/A'}")
        
        raise Exception("No se pudo inicializar Firefox después de diagnóstico completo")
    
    def cambiar_pdf_en_misma_pestana(self, ruta_pdf, numero_pdf, total_pdfs):
        """Método para cambiar PDFs - se mantiene igual"""
        if not self.driver:
            print("   ❌ Firefox no inicializado")
            return
        
        if not os.path.exists(ruta_pdf):
            print(f"   ❌ El archivo PDF no existe: {ruta_pdf}")
            return
        
        try:
            ruta_absoluta = os.path.abspath(ruta_pdf)
            url_pdf = f"file://{ruta_absoluta}"
            
            print(f"   📂 [{numero_pdf}/{total_pdfs}] Cargando: {os.path.basename(ruta_pdf)}")
            
            self.driver.get(url_pdf)
            time.sleep(2)
            
            print(f"   ✅ PDF cargado - Presiona ENTER para siguiente...")
            
        except Exception as e:
            print(f"   ❌ Error al cargar el PDF: {e}")
    
    def mantener_ventana_abierta(self):
        pass
    
    def cerrar_driver(self):
        if self.driver:
            try:
                self.driver.quit()
                print("   ✅ Firefox cerrado")
            except:
                pass