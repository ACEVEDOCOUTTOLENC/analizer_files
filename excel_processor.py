import os
import pandas as pd
from datetime import datetime
import shutil
import re

def procesar_con_excel(pdf_path, datos_extraidos, cia_detectada, ramo, tipo_doc):
    """
    Procesa el archivo PDF comparando con el Excel y renombra/mueve si coincide
    """
    try:
        print(f"      🔗 INICIANDO PROCESAMIENTO CON EXCEL")
        
        # 1. Encontrar archivo Excel más reciente
        excel_path = encontrar_excel_reciente()
        if not excel_path:
            print("❌ No se encontró archivo Excel")
            return False
        
        print(f"📊 Usando Excel: {os.path.basename(excel_path)}")
        
        # 2. Cargar y procesar Excel
        df = cargar_excel(excel_path)
        if df is None or df.empty:
            print("❌ Excel vacío o no se pudo cargar")
            return False
        
        # 3. Buscar coincidencias
        registro_coincidente = buscar_coincidencia(df, datos_extraidos, cia_detectada, ramo, tipo_doc)
        
        # 🔥 CORRECCIÓN COMPLETA: Verificar si no hay coincidencia
        if registro_coincidente is None or (hasattr(registro_coincidente, 'empty') and registro_coincidente.empty):
            print("❌ No se encontró coincidencia en Excel")
            return False
        
        print(f"✅ Coincidencia encontrada en Excel: Póliza {registro_coincidente['Póliza']}")
        
        # 🔥 CORRECCIÓN: Si es DataFrame de una fila, convertirlo a Series
        if isinstance(registro_coincidente, pd.DataFrame):
            print(f"      🔄 Convirtiendo DataFrame a Series...")
            registro_coincidente = registro_coincidente.iloc[0]
        
        # 4. Renombrar archivo según tipo de documento
        print(f"      📝 Generando nombre del archivo...")
        nuevo_nombre = generar_nombre_archivo(registro_coincidente, tipo_doc)
        
        if not nuevo_nombre:
            print("❌ No se pudo generar el nombre del archivo")
            return False
        
        print(f"      ✅ Nombre generado: {nuevo_nombre}")
        
        # 5. Mover archivo a carpeta de package
        print(f"      🚚 Moviendo archivo...")
        if mover_archivo(pdf_path, nuevo_nombre):
            # 6. Marcar como procesado en Excel
            print(f"      📊 Marcando en Excel...")
            marcar_procesado_excel(excel_path, registro_coincidente, df)
            print(f"🎉 ¡ARCHIVO RENOMBRADO Y MOVIDO EXITOSAMENTE!: {nuevo_nombre}")
            return True
        else:
            print("❌ Falló el movimiento del archivo")
            return False
        
    except Exception as e:
        print(f"❌ Error en procesamiento con Excel: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    
def encontrar_excel_reciente():
    """Encuentra el archivo Excel más reciente en produccion_final"""
    excel_dir = r"/mnt/desarrollo/storage/data/produccion_final"
    
    if not os.path.exists(excel_dir):
        print(f"❌ Directorio no existe: {excel_dir}")
        return None
    
    archivos = []
    for archivo in os.listdir(excel_dir):
        if archivo.startswith("produccion_final_") and archivo.endswith(".xlsx"):
            # Extraer fecha del nombre
            try:
                fecha_str = archivo.replace("produccion_final_", "").replace(".xlsx", "")
                fecha = datetime.strptime(fecha_str, "%Y%m%d_%H%M%S")
                archivos.append((fecha, os.path.join(excel_dir, archivo)))
            except Exception as e:
                print(f"⚠️ Error procesando archivo {archivo}: {e}")
                continue
    
    if not archivos:
        print("❌ No se encontraron archivos Excel")
        return None
    
    # Devolver el más reciente
    archivos.sort(reverse=True)
    return archivos[0][1]

def cargar_excel(excel_path):
    """Carga el archivo Excel y elimina duplicados de Póliza"""
    try:
        df = pd.read_excel(excel_path)
        
        # Verificar columnas requeridas
        columnas_requeridas = ['Póliza', 'Endoso', 'Forma de pago', 'Serie', 'CiaNombre', 'UserConvertOT', 'RamosNombre', 'FEmisionDocto']
        for col in columnas_requeridas:
            if col not in df.columns:
                print(f"❌ Columna faltante en Excel: {col}")
                return None
        
        print(f"📋 Excel cargado: {len(df)} registros")
        return df
        
    except Exception as e:
        print(f"❌ Error cargando Excel: {e}")
        return None

def buscar_coincidencia(df, datos_extraidos, cia_detectada, ramo, tipo_doc):
    """
    Busca coincidencia en el Excel basado en los datos extraídos
    """
    from companias import COMPANIAS
    from companias.gnp import RAMOS_ALIASES, RAMOS_MAP
    
    # Preparar datos para búsqueda
    poliza_buscar = datos_extraidos.get('poliza') or datos_extraidos.get('numero_de_poliza')
    forma_pago_buscar = datos_extraidos.get('forma_pago') or datos_extraidos.get('forma_de_pago')
    
    if not poliza_buscar:
        print("❌ No hay póliza para buscar")
        return None
    
    print(f"🔍 Buscando: Póliza='{poliza_buscar}', Ramo='{ramo}', Cía='{cia_detectada}'")
    print(f"   📋 Datos extraídos: {datos_extraidos}")
    
    # Filtrar por tipo de documento
    if tipo_doc == 'endoso':
        df_filtrado = df[df['Endoso'].notna() & (df['Endoso'] != '')]
        print(f"   📑 Filtrado ENDOSO: {len(df_filtrado)} registros")
    else:
        df_filtrado = df
        # Para carátula, eliminar duplicados de Póliza
        if tipo_doc == 'caratula':
            df_filtrado = df_filtrado.drop_duplicates(subset=['Póliza'], keep='first')
            print(f"   📑 Filtrado CARÁTULA: {len(df_filtrado)} registros únicos")
        else:
            print(f"   📑 Sin filtro especial: {len(df_filtrado)} registros")
    
    # Mostrar primeras filas del Excel para debug
    print(f"   📊 Primeras 5 filas del Excel:")
    for i, (idx, row) in enumerate(df_filtrado.head(5).iterrows()):
        print(f"      Fila {i+1}: Póliza='{row['Póliza']}', Cia='{row['CiaNombre']}', Ramo='{row['RamosNombre']}'")
    
    # Buscar por coincidencia parcial de póliza
    def buscar_poliza_parcial(poliza_excel, poliza_buscar):
        # Limpiar ambas pólizas (quitar espacios, guiones, etc.)
        poliza_buscar_limpia = re.sub(r'[^\d]', '', poliza_buscar)
        poliza_excel_limpia = re.sub(r'[^\d]', '', str(poliza_excel))
        
        resultado = poliza_buscar_limpia in poliza_excel_limpia
        print(f"      🔎 Comparando póliza: '{poliza_buscar_limpia}' in '{poliza_excel_limpia}' = {resultado}")
        return resultado
    
    # Aplicar filtros
    coincidencias = []
    print(f"   🔍 Aplicando filtros a {len(df_filtrado)} registros...")
    
    for idx, row in df_filtrado.iterrows():
        print(f"   --- Revisando fila {idx+1} ---")
        
        # 1. Coincidencia de póliza (parcial)
        print(f"      1. Póliza: '{poliza_buscar}' vs '{row['Póliza']}'")
        if not buscar_poliza_parcial(row['Póliza'], poliza_buscar):
            print(f"      ❌ Falla en póliza")
            continue
            
        # 2. Coincidencia de compañía
        print(f"      2. Compañía: '{cia_detectada}' vs '{row['CiaNombre']}'")
        if not coincidir_compania(row['CiaNombre'], cia_detectada, COMPANIAS):
            print(f"      ❌ Falla en compañía")
            continue
            
        # 3. Coincidencia de ramo
        print(f"      3. Ramo: '{ramo}' vs '{row['RamosNombre']}'")
        if not coincidir_ramo(row['RamosNombre'], ramo, RAMOS_ALIASES, RAMOS_MAP):
            print(f"      ❌ Falla en ramo")
            continue
            
        # 4. Coincidencia de forma de pago (si está disponible)
        if forma_pago_buscar:
            print(f"      4. Forma pago: '{forma_pago_buscar}' vs '{row['Forma de pago']}'")
            if not coincidir_forma_pago(row['Forma de pago'], forma_pago_buscar):
                print(f"      ❌ Falla en forma de pago")
                continue
        else:
            print(f"      4. Forma pago: Sin datos para comparar")
        
        # 5. Coincidencia de fecha (si está disponible)
        fecha_extraida = datos_extraidos.get('fecha_emision') or datos_extraidos.get('fecha_de_expedicion')
        if fecha_extraida:
            print(f"      5. Fecha: '{fecha_extraida}' vs '{row['FEmisionDocto']}'")
            if not coincidir_fecha(row['FEmisionDocto'], fecha_extraida):
                print(f"      ❌ Falla en fecha")
                continue
        else:
            print(f"      5. Fecha: Sin datos para comparar")
        
        print(f"      ✅ TODOS LOS FILTROS PASADOS - COINCIDENCIA ENCONTRADA")
        coincidencias.append((idx, row))
    
    if not coincidencias:
        print("❌ No hay coincidencias después de aplicar filtros")
        return None
    
    if len(coincidencias) > 1:
        print(f"⚠️ Múltiples coincidencias encontradas ({len(coincidencias)}), usando la primera")
    
    return coincidencias[0][1]  # Devolver el primer registro coincidente

def coincidir_compania(cia_excel, cia_detectada, COMPANIAS):
    """Verifica coincidencia de compañía con más logging"""
    if not cia_excel or not cia_detectada:
        print(f"      ⚠️ Datos faltantes: Excel='{cia_excel}', Detectada='{cia_detectada}'")
        return False
    
    cia_excel_upper = str(cia_excel).upper()
    cia_detectada_upper = cia_detectada.upper()
    
    print(f"      🔍 Buscando '{cia_detectada_upper}' en aliases de '{cia_excel_upper}'")
    
    # Buscar en los alias de COMPANIAS
    for cia_nombre, alias_list in COMPANIAS.items():
        if cia_nombre.upper() == cia_detectada_upper:
            # Verificar si el nombre del Excel coincide con algún alias
            for alias in alias_list:
                if alias.upper() in cia_excel_upper:
                    print(f"      ✅ Coincidencia encontrada: '{alias.upper()}' in '{cia_excel_upper}'")
                    return True
    print(f"      ❌ No se encontró coincidencia para compañía")
    return False

def coincidir_ramo(ramo_excel, ramo_detectado, RAMOS_ALIASES, RAMOS_MAP):
    """Verifica coincidencia de ramo - VERSIÓN MÁS SIMPLE"""
    if not ramo_excel or not ramo_detectado:
        print(f"      ⚠️ Datos faltantes: Excel='{ramo_excel}', Detectado='{ramo_detectado}'")
        return False
    
    ramo_excel_upper = str(ramo_excel).upper()
    ramo_detectado_upper = ramo_detectado.upper()
    
    print(f"      🔍 Comparando ramos: Excel='{ramo_excel_upper}' vs Detectado='{ramo_detectado_upper}'")
    
    # 1. Coincidencia directa
    if ramo_detectado_upper in ramo_excel_upper or ramo_excel_upper in ramo_detectado_upper:
        print(f"      ✅ Coincidencia directa encontrada")
        return True
    
    # 2. Verificar si son el mismo ramo estándar a través de aliases
    for ramo_estandar, aliases in RAMOS_ALIASES.items():
        # Crear lista de todos los posibles nombres para este ramo (estándar + aliases)
        todos_nombres = [ramo_estandar.upper()] + [alias.upper() for alias in aliases]
        
        # Verificar si AMBOS ramos están en la misma familia de nombres
        excel_en_familia = any(nombre in ramo_excel_upper for nombre in todos_nombres)
        detectado_en_familia = any(nombre in ramo_detectado_upper for nombre in todos_nombres)
        
        if excel_en_familia and detectado_en_familia:
            print(f"      ✅ Coincidencia: Ambos pertenecen a la familia '{ramo_estandar}'")
            print(f"         Excel: '{ramo_excel_upper}' -> Familia '{ramo_estandar}'")
            print(f"         Detectado: '{ramo_detectado_upper}' -> Familia '{ramo_estandar}'")
            return True
    
    print(f"      ❌ No se encontró coincidencia para ramo")
    return False

def coincidir_forma_pago(forma_pago_excel, forma_pago_extraida):
    """Verifica coincidencia de forma de pago - CASE INSENSITIVE"""
    if not forma_pago_excel or not forma_pago_extraida:
        return True  # Si no hay datos, no filtrar
    
    forma_excel_upper = str(forma_pago_excel).upper().strip()
    forma_extraida_upper = forma_pago_extraida.upper().strip()
    
    print(f"      🔍 Comparando formas de pago: Excel='{forma_excel_upper}' vs Extraída='{forma_extraida_upper}'")
    
    # 1. Coincidencia directa (case insensitive)
    if (forma_extraida_upper in forma_excel_upper or 
        forma_excel_upper in forma_extraida_upper):
        print(f"      ✅ Coincidencia directa de forma de pago")
        return True
    
    # 2. Mapeo especial: ANUAL = CONTADO (case insensitive)
    mapeo_formas_pago = {
        "ANUAL": ["CONTADO", "ANUAL", "ANUALIDAD", "ANUALES"],
        "CONTADO": ["ANUAL", "CONTADO", "PAGO UNICO", "PAGO ÚNICO", "CONTADO"],
        "SEMESTRAL": ["SEMESTRAL", "SEMESTRE", "SEMESTRALES"],
        "TRIMESTRAL": ["TRIMESTRAL", "TRIMESTRE", "TRIMESTRALES"], 
        "MENSUAL": ["MENSUAL", "MES", "MENSUALES"],
        "PARCIAL": ["PARCIAL", "PARCIALIDAD", "PARCIALES"]
    }
    
    # Buscar en ambos sentidos
    for forma_principal, equivalentes in mapeo_formas_pago.items():
        # Si la forma extraída coincide con la forma principal
        if forma_principal in forma_extraida_upper:
            for equivalente in equivalentes:
                if equivalente in forma_excel_upper:
                    print(f"      ✅ Coincidencia por mapeo: '{forma_extraida_upper}' -> '{forma_principal}' = '{equivalente}' en Excel")
                    return True
        
        # Si la forma del Excel coincide con la forma principal  
        if forma_principal in forma_excel_upper:
            for equivalente in equivalentes:
                if equivalente in forma_extraida_upper:
                    print(f"      ✅ Coincidencia por mapeo: '{forma_excel_upper}' -> '{forma_principal}' = '{equivalente}' en Extraída")
                    return True
    
    print(f"      ❌ No coinciden las formas de pago")
    return False
    
   

def coincidir_fecha(fecha_excel, fecha_extraida):
    """Verifica coincidencia de fecha"""
    if not fecha_excel or not fecha_extraida:
        return True  # Si no hay datos, no filtrar
    
    try:
        # Convertir ambas fechas a formato estándar para comparar
        if isinstance(fecha_excel, datetime):
            fecha_excel_str = fecha_excel.strftime('%Y-%m-%d')
        else:
            fecha_excel_str = str(fecha_excel)
        
        return fecha_extraida in fecha_excel_str or fecha_excel_str in fecha_extraida
    except:
        return False

def generar_nombre_archivo(registro, tipo_doc):
    """Genera el nombre del archivo según el tipo de documento"""
    # Asegurarnos de extraer valores escalares de la Series
    poliza = str(registro['Póliza']).strip()
    
    print(f"      📝 Generando nombre - Póliza: '{poliza}', Tipo: '{tipo_doc}'")
    
    if tipo_doc == 'caratula':
        nombre = f"{poliza}.pdf"
    
    elif tipo_doc == 'endoso':
        endoso = str(registro['Endoso']).strip()
        nombre = f"{poliza}_{endoso}.pdf"
        print(f"      📝 Endoso encontrado: '{endoso}'")
    
    elif tipo_doc == 'recibo':
        serie = str(registro['Serie']).strip()
        nombre = f"{poliza}_{serie}.pdf"
    
    elif tipo_doc == 'recibo_endoso':
        endoso = str(registro['Endoso']).strip()
        serie = str(registro['Serie']).strip()
        nombre = f"{poliza}_{endoso}_{serie}.pdf"
    
    elif tipo_doc == 'factura':
        nombre = f"{poliza}_factura.pdf"
    
    elif tipo_doc == 'nota_de_credito':
        nombre = None
    
    else:
        nombre = f"{poliza}.pdf"
    
    print(f"      📝 Nombre final: '{nombre}'")
    return nombre

def mover_archivo(pdf_path_original, nuevo_nombre):
    """Mueve el archivo a la carpeta package con la fecha de hoy"""
    if not nuevo_nombre:
        print("⚠️ No se renombra (nota de crédito)")
        return False
    
    # Crear carpeta de destino
    fecha_hoy = datetime.now().strftime('%Y%m%d')
    package_dir = os.path.join(r"/mnt/desarrollo/storage/data/package", fecha_hoy)
    
    try:
        os.makedirs(package_dir, exist_ok=True)
    except Exception as e:
        print(f"❌ Error creando directorio: {e}")
        return False
    
    # Ruta completa de destino
    destino_path = os.path.join(package_dir, nuevo_nombre)
    
    # Verificar si ya existe
    if os.path.exists(destino_path):
        print(f"⚠️ Archivo ya existe en destino: {nuevo_nombre}")
        return False
    
    try:
        shutil.move(pdf_path_original, destino_path)
        print(f"📦 Movido a: {destino_path}")
        return True
    except Exception as e:
        print(f"❌ Error moviendo archivo: {e}")
        return False

def marcar_procesado_excel(excel_path, registro, df_original):
    """Marca el registro como procesado en el Excel (pintar de verde) - CORREGIDA"""
    try:
        # Usar openpyxl para mantener formato
        from openpyxl import load_workbook
        from openpyxl.styles import PatternFill
        
        wb = load_workbook(excel_path)
        ws = wb.active
        
        print(f"      📊 Buscando fila para marcar en Excel...")
        
        # ENCONTRAR LA FILA CORRECTA - MÉTODO CORREGIDO
        fila_encontrada = None
        poliza_buscada = registro['Póliza']
        
        print(f"      🔍 Buscando Póliza: {poliza_buscada}")
        
        for idx, row in df_original.iterrows():
            # Comparar por Póliza (más confiable que equals())
            if str(row['Póliza']).strip() == str(poliza_buscada).strip():
                # Si es endoso, también comparar el Endoso
                if 'Endoso' in registro and pd.notna(registro['Endoso']):
                    if str(row['Endoso']).strip() == str(registro['Endoso']).strip():
                        fila_encontrada = idx
                        print(f"      ✅ Fila encontrada (con Endoso): {idx}")
                        break
                else:
                    fila_encontrada = idx
                    print(f"      ✅ Fila encontrada: {idx}")
                    break
        
        if fila_encontrada is not None:
            # Pintar toda la fila de verde
            green_fill = PatternFill(start_color="00FF00", end_color="00FF00", fill_type="solid")
            # +2 porque Excel empieza en 1 (fila 1) y tiene headers (fila 2)
            fila_excel = fila_encontrada + 2  
            for cell in ws[fila_excel]:
                cell.fill = green_fill
            
            print(f"      ✅ Fila {fila_excel} marcada como procesada en Excel")
        else:
            print(f"      ⚠️ No se encontró la fila para marcar en Excel")
        
        wb.save(excel_path)
        print("✅ Excel guardado con registro marcado")
        
    except Exception as e:
        print(f"⚠️ No se pudo marcar en Excel: {e}")
        # Intentar con pandas como fallback
        try:
            df_original.to_excel(excel_path, index=False)
            print("✅ Excel guardado (sin formato)")
        except Exception as e2:
            print(f"❌ Error guardando Excel: {e2}")