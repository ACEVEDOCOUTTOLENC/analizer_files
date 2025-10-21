import os
import tkinter as tk
from tkinter import filedialog
from anotador.inteligente import AnotadorInteligente
from anotador.interfaz_consola import InterfazAnotador

def seleccionar_pdf():
    """Abre un diálogo para seleccionar un archivo PDF"""
    root = tk.Tk()
    root.withdraw()  # Ocultar la ventana principal
    
    archivo = filedialog.askopenfilename(
        title="Selecciona un archivo PDF",
        filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
    )
    
    return archivo

def main():
    print("🧠 ANOTADOR INTELIGENTE DE PDF")
    print("=" * 50)
    
    # Seleccionar archivo PDF
    pdf_path = seleccionar_pdf()
    
    if not pdf_path:
        print("❌ No se seleccionó ningún archivo")
        return
    
    print(f"📄 Procesando: {os.path.basename(pdf_path)}")
    
    try:
        # Crear el anotador
        anotador = AnotadorInteligente(pdf_path)
        
        # Ejecutar la interfaz
        interfaz = InterfazAnotador(anotador)
        interfaz.ejecutar()
        
        print("✅ Anotación completada")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()