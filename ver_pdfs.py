#!/usr/bin/env python3
"""
Script rápido para ver qué PDFs se encuentran
"""

import os
from utils.file_utils import obtener_todos_los_pdfs

def main():
    print("🔍 DIAGNÓSTICO RÁPIDO DE PDFs")
    print("=" * 50)
    
    pdfs = obtener_todos_los_pdfs()
    
    if not pdfs:
        print("❌ No se encontraron PDFs")
        print(f"📁 Directorio actual: {os.path.abspath('.')}")
        return
    
    print(f"✅ Se encontraron {len(pdfs)} archivos PDF:")
    print("-" * 50)
    
    for i, pdf in enumerate(pdfs, 1):
        print(f"{i:2d}. {os.path.basename(pdf)}")
        print(f"    📍 {pdf}")
    
    print("-" * 50)
    print(f"📊 Total: {len(pdfs)} archivos PDF listos para abrir")

if __name__ == "__main__":
    main()