import os
import pandas as pd
from datetime import datetime
import shutil
import re
import dateutil.parser

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
    con deducción automática de forma de pago
    """
    from companias import COMPANIAS
    from companias.gnp import RAMOS_ALIASES, RAMOS_MAP
    import re
    
    # Preparar datos para búsqueda
    poliza_buscar = datos_extraidos.get('poliza') or datos_extraidos.get('numero_de_poliza')
    
    if not poliza_buscar:
        print("❌ No hay póliza para buscar")
        return None
    
    # DEDUCIR FORMA DE PAGO AUTOMÁTICAMENTE
    forma_pago_buscar = deducir_forma_pago_por_fechas_y_serie(datos_extraidos)
    if forma_pago_buscar:
        print(f"🎯 Forma de pago deducida: {forma_pago_buscar}")
    else:
        forma_pago_buscar = datos_extraidos.get('forma_pago') or datos_extraidos.get('forma_de_pago')
        if forma_pago_buscar:
            print(f"📋 Forma de pago extraída: {forma_pago_buscar}")
    
    print(f"🔍 Buscando: Póliza='{poliza_buscar}', Ramo='{ramo}', Cía='{cia_detectada}'")
    print(f"   📋 Datos extraídos: {datos_extraidos}")
    
    # Filtrar dataset por tipo de documento
    df_filtrado = _filtrar_dataframe_por_tipo(df, tipo_doc)
    
    # Mostrar muestra del Excel para debug
    _mostrar_muestra_excel(df_filtrado)
    
    # Aplicar filtros secuenciales
    coincidencias = []
    print(f"   🔍 Aplicando filtros a {len(df_filtrado)} registros...")
    
    for idx, row in df_filtrado.iterrows():
        print(f"   --- Revisando fila {idx+1} ---")
        
        # Aplicar filtros en cascada
        if not _aplicar_filtro_poliza(row, poliza_buscar):
            continue
            
        if not _aplicar_filtro_compania(row, cia_detectada, COMPANIAS):
            continue
            
        if not _aplicar_filtro_ramo(row, ramo, RAMOS_ALIASES, RAMOS_MAP):
            continue
            
        if not _aplicar_filtro_forma_pago(row, forma_pago_buscar):
            continue
            
        if not _aplicar_filtro_fecha(row, datos_extraidos):
            continue
        
        print(f"      ✅ TODOS LOS FILTROS PASADOS - COINCIDENCIA ENCONTRADA")
        coincidencias.append((idx, row))
    
    return _procesar_resultados(coincidencias)

# ==========================
# FUNCIONES AUXILIARES
# ==========================

def _filtrar_dataframe_por_tipo(df, tipo_doc):
    """Filtra el DataFrame según el tipo de documento"""
    if tipo_doc == 'endoso':
        df_filtrado = df[df['Endoso'].notna() & (df['Endoso'] != '')]
        print(f"   📑 Filtrado ENDOSO: {len(df_filtrado)} registros")
    else:
        df_filtrado = df
        if tipo_doc == 'caratula':
            df_filtrado = df_filtrado.drop_duplicates(subset=['Póliza'], keep='first')
            print(f"   📑 Filtrado CARÁTULA: {len(df_filtrado)} registros únicos")
        else:
            print(f"   📑 Sin filtro especial: {len(df_filtrado)} registros")
    return df_filtrado

def _mostrar_muestra_excel(df_filtrado, num_muestra=5):
    """Muestra una muestra del DataFrame para debug"""
    print(f"   📊 Primeras {num_muestra} filas del Excel:")
    for i, (idx, row) in enumerate(df_filtrado.head(num_muestra).iterrows()):
        print(f"      Fila {i+1}: Póliza='{row['Póliza']}', Cia='{row['CiaNombre']}', Ramo='{row['RamosNombre']}'")

def _aplicar_filtro_poliza(row, poliza_buscar):
    """Aplica filtro de póliza con búsqueda flexible"""
    print(f"      1. Póliza: '{poliza_buscar}' vs '{row['Póliza']}'")
    
    # Búsqueda flexible de póliza
    def buscar_poliza_flexible(poliza_excel, poliza_buscar):
        # Limpiar ambas pólizas
        poliza_buscar_limpia = re.sub(r'[^\d]', '', poliza_buscar)
        poliza_excel_limpia = re.sub(r'[^\d]', '', str(poliza_excel))
        
        # Estrategias de búsqueda flexibles
        estrategias = [
            poliza_buscar_limpia in poliza_excel_limpia,  # Contiene
            poliza_excel_limpia.startswith(poliza_buscar_limpia),  # Empieza con
            poliza_excel_limpia.endswith(poliza_buscar_limpia)  # Termina con
        ]
        
        resultado = any(estrategias)
        
        print(f"      🔎 Búsqueda flexible póliza:")
        print(f"         '{poliza_buscar_limpia}' in '{poliza_excel_limpia}' = {estrategias[0]}")
        if len(poliza_buscar_limpia) < 6:  # Solo mostrar para pólizas cortas
            print(f"         '{poliza_excel_limpia}'.startswith('{poliza_buscar_limpia}') = {estrategias[1]}")
            print(f"         '{poliza_excel_limpia}'.endswith('{poliza_buscar_limpia}') = {estrategias[2]}")
        print(f"         RESULTADO = {resultado}")
        
        return resultado
    
    if not buscar_poliza_flexible(row['Póliza'], poliza_buscar):
        print(f"      ❌ Falla en póliza")
        return False
    return True

def _aplicar_filtro_compania(row, cia_detectada, COMPANIAS):
    """Aplica filtro de compañía"""
    print(f"      2. Compañía: '{cia_detectada}' vs '{row['CiaNombre']}'")
    if not coincidir_compania(row['CiaNombre'], cia_detectada, COMPANIAS):
        print(f"      ❌ Falla en compañía")
        return False
    return True

def _aplicar_filtro_ramo(row, ramo, RAMOS_ALIASES, RAMOS_MAP):
    """Aplica filtro de ramo"""
    print(f"      3. Ramo: '{ramo}' vs '{row['RamosNombre']}'")
    if not coincidir_ramo(row['RamosNombre'], ramo, RAMOS_ALIASES, RAMOS_MAP):
        print(f"      ❌ Falla en ramo")
        return False
    return True

def _aplicar_filtro_forma_pago(row, forma_pago_buscar):
    """Aplica filtro de forma de pago (opcional)"""
    if forma_pago_buscar:
        print(f"      4. Forma pago: '{forma_pago_buscar}' vs '{row['Forma de pago']}'")
        if not coincidir_forma_pago(row['Forma de pago'], forma_pago_buscar):
            print(f"      ❌ Falla en forma de pago")
            return False
    else:
        print(f"      4. Forma pago: Sin datos para comparar")
    return True

def _aplicar_filtro_fecha(row, datos_extraidos):
    """Aplica filtro de fecha (opcional)"""
    fecha_extraida = datos_extraidos.get('fecha_emision') or datos_extraidos.get('fecha_de_expedicion')
    if fecha_extraida:
        print(f"      5. Fecha: '{fecha_extraida}' vs '{row['FEmisionDocto']}'")
        if not coincidir_fecha(row['FEmisionDocto'], fecha_extraida):
            print(f"      ❌ Falla en fecha")
            return False
    else:
        print(f"      5. Fecha: Sin datos para comparar")
    return True

def _procesar_resultados(coincidencias):
    """Procesa los resultados de las coincidencias encontradas"""
    if not coincidencias:
        print("❌ No hay coincidencias después de aplicar filtros")
        return None
    
    if len(coincidencias) > 1:
        print(f"⚠️ Múltiples coincidencias encontradas ({len(coincidencias)}), usando la primera")
        # Podríamos agregar lógica para elegir la mejor coincidencia aquí
    
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
    
    # 2. Mapeo especial - ACTUALIZADO CON PRIMAUNICA
    mapeo_formas_pago = {
        "CONTADO": [
            "CONTADO", "ANUAL", "PAGO UNICO", "PAGO ÚNICO", 
            "PRIMA UNICA", "PRIMAUNICA", "PRIMA ÚNICA", "UNICA",
            "PAGO TOTAL", "AL CONTADO", "UNICO PAGO", "ÚNICO PAGO",
            "EFECTIVO", "PAGO INMEDIATO"
        ],
        "ANUAL": [
            "ANUAL", "ANUALIDAD", "ANUALES", "CONTADO", "POR AÑO",
            "CADA AÑO", "ANUALMENTE"
        ],
        "SEMESTRAL": [
            "SEMESTRAL", "SEMESTRE", "SEMESTRALES", "6 MESES",
            "BIANUAL", "DOS VECES AL AÑO"
        ],
        "TRIMESTRAL": [
            "TRIMESTRAL", "TRIMESTRE", "TRIMESTRALES", "3 MESES",
            "CUATRIMESTRAL", "CUATRO VECES AL AÑO"
        ],
        "MENSUAL": [
            "MENSUAL", "MES", "MENSUALES", "MENSUALIDAD",
            "POR MES", "CADA MES", "MENSUALMENTE"
        ],
        "BIMESTRAL": [
            "BIMESTRAL", "BIMESTRE", "BIMESTRALES", "2 MESES"
        ],
        "PARCIAL": [
            "PARCIAL", "PARCIALIDAD", "PARCIALES", "ABONO",
            "PAGOS PARCIALES"
        ]
    }
    
    # 3. Buscar en el mapeo
    for forma_estandar, variantes in mapeo_formas_pago.items():
        excel_en_variantes = forma_excel_upper in variantes
        extraida_en_variantes = forma_extraida_upper in variantes
        
        if excel_en_variantes and extraida_en_variantes:
            print(f"      ✅ Coincidencia por mapeo: {forma_estandar}")
            return True
    
    print(f"      ❌ No coinciden las formas de pago")
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
    """Verifica coincidencia de fecha con normalización de formatos"""
    if not fecha_excel or not fecha_extraida:
        print(f"      ⚠️ Fechas faltantes: Excel='{fecha_excel}', Extraída='{fecha_extraida}'")
        return True  # Si no hay datos, no filtrar
    
    try:
        # Normalizar ambas fechas a un formato común
        fecha_excel_normalizada = _normalizar_fecha(fecha_excel)
        fecha_extraida_normalizada = _normalizar_fecha(fecha_extraida)
        
        print(f"      🔍 Comparando fechas:")
        print(f"         Excel: '{fecha_excel}' -> '{fecha_excel_normalizada}'")
        print(f"         Extraída: '{fecha_extraida}' -> '{fecha_extraida_normalizada}'")
        
        # Comparar las fechas normalizadas
        resultado = fecha_excel_normalizada == fecha_extraida_normalizada
        
        print(f"      📅 Resultado comparación: {resultado}")
        
        return resultado
        
    except Exception as e:
        print(f"      ⚠️ Error comparando fechas: {e}")
        return True  # En caso de error, no filtrar por fecha

def generar_nombre_archivo(registro, tipo_doc):
    """
    Genera el nombre del archivo según el estándar SICAS Online
    """
    # Asegurarnos de extraer valores escalares de la Series
    poliza = str(registro['Póliza']).strip()
    
    print(f"      📝 Generando nombre SICAS - Póliza: '{poliza}', Tipo: '{tipo_doc}'")
    
    # Obtener datos adicionales
    endoso = str(registro.get('Endoso', '')).strip()
    serie = str(registro.get('Serie', '')).strip()
    
    print(f"      📝 Datos: Endoso='{endoso}', Serie='{serie}'")
    
    nombre_base = None
    
    # REGLAS SEGÚN ESTÁNDAR SICAS ONLINE
    if tipo_doc == 'caratula':
        # Documento.pdf
        nombre_base = poliza
    
    elif tipo_doc == 'endoso':
        # Documento_Endoso.pdf
        if endoso and endoso != '':
            nombre_base = f"{poliza}_{endoso}"
        else:
            nombre_base = poliza
    
    elif tipo_doc == 'recibo':
        # Documento_Periodo.pdf
        if serie and serie != '':
            # Extraer solo el número de período (primera parte antes de /)
            periodo = _extraer_periodo_serie(serie)
            nombre_base = f"{poliza}_{periodo}"
        else:
            nombre_base = poliza
    
    elif tipo_doc == 'recibo_endoso':
        # Documento_Endoso_Periodo.pdf
        if endoso and endoso != '' and serie and serie != '':
            periodo = _extraer_periodo_serie(serie)
            nombre_base = f"{poliza}_{endoso}_{periodo}"
        elif endoso and endoso != '':
            nombre_base = f"{poliza}_{endoso}"
        elif serie and serie != '':
            periodo = _extraer_periodo_serie(serie)
            nombre_base = f"{poliza}_{periodo}"
        else:
            nombre_base = poliza
    
    elif tipo_doc == 'factura':
        nombre_base = f"{poliza}_factura"
    
    elif tipo_doc == 'nota_de_credito':
        print(f"      📝 Nota de crédito - no se renombra")
        return None
    
    else:
        nombre_base = poliza
    
    # SANITIZAR nombre (remover caracteres inválidos)
    nombre_limpio = _sanitizar_nombre_sicas(nombre_base)
    
    print(f"      📝 Nombre SICAS generado: '{nombre_limpio}'")
    
    return nombre_limpio

def _extraer_periodo_serie(serie):
    """
    Extrae el período de la serie según formato SICAS
    Ejemplos: 
      "001/001" → "1"
      "01/12" → "1" 
      "1" → "1"
    """
    if not serie:
        return "1"
    
    serie_clean = str(serie).strip()
    
    # Si tiene formato de fracción "001/001"
    if '/' in serie_clean:
        partes = serie_clean.split('/')
        if partes[0].isdigit():
            # Convertir "001" → "1", "012" → "12"
            return str(int(partes[0]))
    
    # Si es solo un número
    if serie_clean.isdigit():
        return str(int(serie_clean))
    
    # Por defecto
    return "1"

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
            
def _sanitizar_nombre_sicas(nombre_base):
    """
    Sanitiza el nombre para SICAS Online manteniendo los formatos especiales
    pero removiendo caracteres inválidos del sistema de archivos
    """
    # Caracteres inválidos en nombres de archivo (excepto ! que se usa en SICAS)
    caracteres_invalidos = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    
    # Reemplazar caracteres inválidos (excepto !)
    nombre_limpio = nombre_base
    for char in caracteres_invalidos:
        nombre_limpio = nombre_limpio.replace(char, '-')
    
    # Preservar el ! para incisos individuales (formato SICAS)
    # nombre_limpio puede contener ! según el estándar
    
    # Asegurar que no empiece o termine con puntos/espacios
    nombre_limpio = nombre_limpio.strip('. ')
    
    # Limitar longitud
    if len(nombre_limpio) > 200:
        nombre_limpio = nombre_limpio[:200]
        print(f"      ⚠️ Nombre muy largo, truncado a: '{nombre_limpio}'")
    
    # Agregar extensión .pdf si no la tiene
    if not nombre_limpio.lower().endswith('.pdf'):
        nombre_limpio += '.pdf'
    
    return nombre_limpio

def deducir_forma_pago_por_fechas_y_serie(datos_extraidos, serie_extraida=None):
    """
    Deduce la forma de pago analizando fechas de vigencia y serie
    """
    # Obtener fechas de vigencia
    fecha_inicio = datos_extraidos.get('fecha_inicio_vigencia') or datos_extraidos.get('vigencia_desde')
    fecha_fin = datos_extraidos.get('fecha_fin_vigencia') or datos_extraidos.get('vigencia_hasta')
    
    # Si no tenemos serie en parámetros, buscar en datos extraídos
    if not serie_extraida:
        serie_extraida = datos_extraidos.get('serie') or datos_extraidos.get('numero_serie') or ''
    
    print(f"🔍 Deducir forma pago - Fechas: {fecha_inicio} a {fecha_fin}, Serie: {serie_extraida}")
    
    # 1. ANÁLISIS POR SERIE (ej: "01/12", "1 de 4", etc.)
    forma_por_serie = _analizar_forma_pago_por_serie(serie_extraida)
    if forma_por_serie:
        print(f"   ✅ Forma deducida por serie: {forma_por_serie}")
        return forma_por_serie
    
    # 2. ANÁLISIS POR FECHAS (si tenemos ambas fechas)
    forma_por_fechas = _analizar_forma_pago_por_fechas(fecha_inicio, fecha_fin)
    if forma_por_fechas:
        print(f"   ✅ Forma deducida por fechas: {forma_por_fechas}")
        return forma_por_fechas
    
    # 3. USAR TEXTO EXTRAÍDO COMO RESpaldo
    forma_extraida = datos_extraidos.get('forma_pago') or datos_extraidos.get('forma_de_pago')
    if forma_extraida:
        print(f"   🔄 Usando forma extraída: {forma_extraida}")
        return forma_extraida
    
    print("   ⚠️ No se pudo deducir forma de pago")
    return None

def _analizar_forma_pago_por_serie(serie):
    """
    Analiza la serie para deducir forma de pago
    Ejemplos: "01/12" -> MENSUAL, "1/4" -> TRIMESTRAL, etc.
    """
    if not serie:
        return None
    
    serie_clean = str(serie).upper().strip()
    
    # Patrones comunes de serie
    import re
    
    # Patrón: "01/12", "1/12", "01 de 12"
    patron_fraccion = re.search(r'(\d+)\s*[/DE\s]+\s*(\d+)', serie_clean)
    if patron_fraccion:
        actual = int(patron_fraccion.group(1))
        total = int(patron_fraccion.group(2))
        
        print(f"      📊 Serie analizada: {actual}/{total}")
        
        # Determinar por el total de pagos
        if total == 1:
            return "CONTADO"
        elif total == 2:
            return "SEMESTRAL"
        elif total == 4:
            return "TRIMESTRAL"
        elif total == 6:
            return "BIMESTRAL"
        elif total == 12:
            return "MENSUAL"
        elif total == 24:
            return "QUINCENAL"
    
    # Patrones de texto
    if any(palabra in serie_clean for palabra in ["MENSUAL", "MES"]):
        return "MENSUAL"
    elif any(palabra in serie_clean for palabra in ["TRIMESTRAL", "TRIMESTRE"]):
        return "TRIMESTRAL"
    elif any(palabra in serie_clean for palabra in ["SEMESTRAL", "SEMESTRE"]):
        return "SEMESTRAL"
    elif any(palabra in serie_clean for palabra in ["ANUAL", "AÑO"]):
        return "ANUAL"
    
    return None

def _analizar_forma_pago_por_fechas(fecha_inicio, fecha_fin):
    """
    Analiza el período entre fechas para deducir forma de pago
    """
    if not fecha_inicio or not fecha_fin:
        return None
    
    try:
        from datetime import datetime
        import dateutil.parser
        
        # Convertir fechas
        inicio = dateutil.parser.parse(str(fecha_inicio))
        fin = dateutil.parser.parse(str(fecha_fin))
        
        # Calcular diferencia en días
        diferencia_dias = (fin - inicio).days
        
        print(f"      📅 Período analizado: {diferencia_dias} días")
        
        # Determinar forma de pago por duración
        if diferencia_dias <= 1:
            return "CONTADO"
        elif 30 <= diferencia_dias <= 35:  # ~1 mes
            return "MENSUAL"
        elif 85 <= diferencia_dias <= 95:  # ~3 meses
            return "TRIMESTRAL"
        elif 175 <= diferencia_dias <= 185:  # ~6 meses
            return "SEMESTRAL"
        elif 360 <= diferencia_dias <= 370:  # ~1 año
            return "ANUAL"
            
    except Exception as e:
        print(f"      ⚠️ Error analizando fechas: {e}")
    
    return None
            
def _normalizar_fecha(fecha):
    """
    Normaliza cualquier formato de fecha a 'YYYY-MM-DD'
    Maneja: 
    - '17/10/2025' (Excel)
    - '17 OCTUBRE 2025' (extraída)
    - Objetos datetime
    - Otros formatos
    """
    if not fecha:
        return None
    
    # Si ya es datetime, convertir a string
    if isinstance(fecha, datetime):
        return fecha.strftime('%Y-%m-%d')
    
    fecha_str = str(fecha).strip().upper()
    
    # Diccionario de meses en español
    meses_espanol = {
        'ENERO': '01', 'ENE': '01',
        'FEBRERO': '02', 'FEB': '02', 
        'MARZO': '03', 'MAR': '03',
        'ABRIL': '04', 'ABR': '04',
        'MAYO': '05', 'MAY': '05',
        'JUNIO': '06', 'JUN': '06',
        'JULIO': '07', 'JUL': '07',
        'AGOSTO': '08', 'AGO': '08',
        'SEPTIEMBRE': '09', 'SEP': '09',
        'OCTUBRE': '10', 'OCT': '10',
        'NOVIEMBRE': '11', 'NOV': '11',
        'DICIEMBRE': '12', 'DIC': '12'
    }
    
    # Intentar diferentes patrones de fecha
    
    # Patrón 1: "17 OCTUBRE 2025"
    for mes_nombre, mes_numero in meses_espanol.items():
        if mes_nombre in fecha_str:
            # Extraer día, mes y año
            partes = fecha_str.split()
            for parte in partes:
                if parte.isdigit() and len(parte) <= 2:  # Día
                    dia = parte.zfill(2)
                elif parte.isdigit() and len(parte) == 4:  # Año
                    año = parte
                elif parte in meses_espanol:  # Mes
                    mes = meses_espanol[parte]
            
            if 'dia' in locals() and 'mes' in locals() and 'año' in locals():
                return f"{año}-{mes}-{dia}"
    
    # Patrón 2: "17/10/2025" o "17-10-2025"
    import re
    patron_numerico = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', fecha_str)
    if patron_numerico:
        dia = patron_numerico.group(1).zfill(2)
        mes = patron_numerico.group(2).zfill(2)
        año = patron_numerico.group(3)
        return f"{año}-{mes}-{dia}"
    
    # Patrón 3: "2025-10-17" (ya normalizado)
    patron_iso = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', fecha_str)
    if patron_iso:
        año = patron_iso.group(1)
        mes = patron_iso.group(2).zfill(2)
        dia = patron_iso.group(3).zfill(2)
        return f"{año}-{mes}-{dia}"
    
    # Si no se pudo normalizar, devolver la original
    print(f"      ⚠️ No se pudo normalizar fecha: '{fecha_str}'")
    return fecha_str
