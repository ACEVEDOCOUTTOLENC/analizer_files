# test_final_firefox.py
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import time

def test_firefox_fixed():
    print("🧪 PRUEBA FINAL CON ENLACE SIMBÓLICO")
    
    try:
        options = Options()
        options.add_argument("--headless")  # Probar en headless primero
        options.set_preference("pdfjs.disabled", False)
        
        service = Service("/usr/local/bin/geckodriver")
        
        print("🚀 Inicializando Firefox...")
        driver = webdriver.Firefox(service=service, options=options)
        
        print("✅ Driver creado! Navegando a Google...")
        driver.get("https://www.google.com")
        
        print(f"✅ ÉXITO! Título: {driver.title}")
        
        # Probar con archivo local
        test_file = "/home/r1/proyectos/analizer_files/main.py"  # Usar cualquier archivo existente
        file_url = f"file://{test_file}"
        driver.get(file_url)
        print("✅ Archivo local cargado!")
        
        driver.quit()
        print("🎉 FIREFOX FUNCIONA CORRECTAMENTE!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_firefox_fixed()
    if success:
        print("\n🎯 Ahora puedes ejecutar tu programa principal!")
    else:
        print("\n💡 El problema persiste, usaremos la alternativa del sistema")