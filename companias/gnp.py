from selenium.webdriver.common.by import By

# RAMOS_ALIASES: mapeo de nuestro nombre estándar -> lista de alias/variantes comunes
RAMOS_ALIASES = {
    "DAÑOS": [
        "DAÑOS", "DAÑOS MATERIALES", "DAÑOS PATRIMONIALES",
        "HOGAR", "VIVIENDA", "INCENDIO", "TERREMOTO", "ROBO",
        "TODO RIESGO", "RIESGOS", "RIESGOS INDUSTRIALES",
        "TRANSPORTES", "RESPONSABILIDAD CIVIL", "RC", "CAUCIÓN",
        "MERCANCÍAS", "OBRAS", "CONSTRUCCIÓN", "RIESGO INDUSTRIAL"
    ],

    "ACCIDENTES Y ENFERMEDADES": [
        "ACCIDENTES", "ACCIDENTES PERSONALES", "SEGURO DE ACCIDENTES",
        "GASTOS MÉDICOS", "GASTOS MÉDICOS MAYORES", "GASTOS MEDICOS",
        "ASISTENCIA MÉDICA", "PÓLIZA MÉDICA", "SALUD", "SEGURO DE SALUD",
        "HOSPITALIZACIÓN", "INCAPACIDAD", "REEMBOLSO MÉDICO",
        "CONVALESCENCIA", "MEDICOS", "PROTECCIÓN MÉDICA"
    ],

    "VIDA": [
        "VIDA", "SEGURO DE VIDA", "VIDA INDIVIDUAL", "VIDA COLECTIVA",
        "SEGURO DE RETIRO", "ANUALIDAD", "TEMPORAL", "DOTAL",
        "BENEFICIO POR FALLECIMIENTO", "AHORRO", "SEGURO DE AHORRO",
        "SEGURO DE VIDA NATURAL"
    ],

    "VEHÍCULOS": [
        "AUTO", "AUTOS", "AUTOMOVIL", "AUTOMÓVILES", "AUTOS PARTICULAR",
        "SEGURO DE AUTO", "SEGURO DE VEHICULO", "SEGURO VEHICULAR",
        "RESPONSABILIDAD CIVIL VEHICULAR", "DAÑOS A VEHÍCULO", "DAÑOS PROPIOS",
        "DAÑOS A TERCEROS", "COLISIÓN", "COMPREHENSIVE", "TODO RIESGO",
        "ROBO TOTAL", "ROBO PARCIAL", "ASISTENCIA VIAL", "GASTOS MÉDICOS POR ACCIDENTE",
        "COBERTURA COLLISION", "RESPONSABILIDAD CIVIL"
    ]
}

# Mapeo de nuestro estándar -> clave usada en TIPOS_DOCUMENTOS
RAMOS_MAP = {
    "VIDA": "vida",
    "ACCIDENTES Y ENFERMEDADES": "gastos_medicos",
    "VEHÍCULOS": "autos",
    "DAÑOS": "danos"
}

# XPaths y textos esperados de GNP
TIPOS_DOCUMENTOS = {
    "vida": {
        "recibo": {
            "xpaths": [
                "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[4]"
            ],
            "textos": [
                "Aviso de Pago",
                "Aviso de recibo de pago"
            ]
        },
        "caratula": {
            "xpaths": [
                "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[5]"
            ],
            "textos": [
                "Póliza de Seguro de Vida"
            ]
        },
        "factura": {
            "xpaths": [
                "/html/body/div[1]/div/div[2]/span[11]"
            ],
            "textos": [
                "Folio Int. CFD"
            ]
        }
    },

    "gastos_medicos": {
        "caratula": {
            "xpaths": [
                "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[6]",
                "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[184]",
                "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[340]",
                "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[204]"                
            ],
            "textos": [
                "Póliza de Seguro Gastos Médicos",
                "Seguro de Gastos Médicos Mayores Colectivo",
                "Seguro de Gastos Médicos Mayores Colectivo"
            ]
        },
        "recibo": {
            "xpaths": [
                "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[4]"
            ],
            "textos": [
                "Aviso de Pago",
                "Aviso de recibo de pago",
                "Aviso de Cobro"
            ]
        },
        "factura": {
            "xpaths": [
                "/html/body/div[1]/div/div[2]/span[11]",
                "/html/body/div[1]/div[2]/div[2]/div[2]/div/div[2]/span[4]"
            ],
            "textos": [
                "Folio Int. CFD",
                "CFDI Ingreso - Factura"
            ]
        },
        "recibo_endoso": {
            "xpaths": [
                "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[16]",
                "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[18]",
                "/html/body/div[1]/div[2]/div[2]/div[2]/div/div[2]/span[4]",
                "/html/body/div[1]/div[2]/div[2]/div[2]/div/div[2]/span[5]",
                "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[1]"
                
            ],
            "textos": [
                "Endoso",
                "Recibo",
                "SOLICITUD DE"
            ]
        },
        "nota_de_credito": {
            "xpaths": [
                "/html/body/div[1]/div[2]/div[2]/div[2]/div/div[2]/span[4]",
                "/html/body/div[1]/div[2]/div[2]/div[2]/div/div[2]/span[5]"
            ],
             "textos": [
                "CFDI Egreso - Nota de",
                "Crédito"
            ]
        },
        "endoso": {
            "xpaths": [
                "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[45]",
                "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[68]", 
                "/html/body/div[1]/div[2]/div[2]/div[2]/div/div[2]/span[4]",
                "/html/body/div[1]/div[2]/div[2]/div[2]/div/div[2]/span[5]",
                "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[124]",
                "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[9]",
                "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[96]",
                "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[94]"
                
            ],
            "textos": [
                "Endoso",
                "ENDOSO B",
                "ENDOSO \"D\"",
                "ENDOSO \"A\"",
                "ENDOSO \"B\"",
                "ENDOSO",
                "Desde Vigencia del endoso Hasta"
            ]
        }
    },

    "autos": {
        "caratula": {
            "xpaths": [
                "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[54]",
                "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[2]"
            ],
            "textos": [
                "VEHÍCULO ASEGURADO",
                "Fuerza Productora Regular Autos"
            ]
        },
        "recibo": {
            "xpaths": [
                "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[1]"
            ],
            "textos": [
                "Aviso de Cobro"
            ]
        },
        "factura": {
            "xpaths": [
                "/html/body/div[1]/div/div[2]/span[5]"
            ],
            "textos": [
                "CFDI Ingreso - Factura"
            ]
        }
    },

    "danos": {
        "caratula": {
            "xpaths": [
                "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[1]"
            ],
            "textos": [
                "Póliza"
            ]
        },
        "recibo": {
            "xpaths": [
                "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[175]"
            ],
            "textos": [
                "AVISO DE COBRO DE DAÑOS"
            ]
        },
        "factura": {
            "xpaths": [
                "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[142]"
            ],
            "textos": [
                "AVISO DE PAGO DISPONIBLE DAÑOS"
            ]
        }
    }
}

def normalizar_ramo(ramo_texto: str):
    """
    Recibe un texto (ej: 'GASTOS MÉDICOS MAYORES') y devuelve la clave estándar
    usada en TIPOS_DOCUMENTOS (ej: 'gastos_medicos').
    """
    texto = ramo_texto.strip().upper()
    for ramo_estandar, aliases in RAMOS_ALIASES.items():
        if any(alias.upper() in texto for alias in aliases):
            return RAMOS_MAP[ramo_estandar]
    return None

def get_tipo_documento(driver, ramo: str):
    """
    Determina el tipo de documento (carátula, recibo, factura)
    en base al ramo y los XPaths configurados de GNP.
    """
    ramo_key = ramo.strip().lower().replace(" ", "_").replace("ñ", "n")
    if ramo_key not in TIPOS_DOCUMENTOS:
        print(f"⚠️ Ramo no soportado en GNP: {ramo}")
        return None

    for tipo, config in TIPOS_DOCUMENTOS[ramo_key].items():
        xpaths = config.get("xpaths", [])
        textos = config.get("textos", [])

        for xpath in xpaths:
            try:
                elemento = driver.find_element(By.XPATH, xpath)
                texto_extraido = elemento.text.strip()
                print(f"🔎 Revisando XPath para '{tipo}': {xpath}")
                print(f"   ➡ Texto extraído: '{texto_extraido}'")

                if any(t.lower() in texto_extraido.lower() for t in textos):
                    print(f"✅ Documento GNP detectado: {tipo}")
                    return tipo

            except Exception as e:
                print(f"❌ No se encontró elemento para '{tipo}' en {xpath} ({e})")
                continue

    print("❌ No se pudo determinar el tipo de documento en GNP")
    return None

def extraer_datos_documento(driver, ramo: str, tipo_doc: str):
    """
    Extrae información específica del documento basado en ramo y tipo de documento.
    
    Returns:
        dict: Diccionario con los datos extraídos
    """
    # Mapeo de XPaths para extracción de datos (tu estructura)
    DATOS_EXTRACCION = {
        "vida": {
            "recibo": {
                "poliza": "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[32]",
                "serie": "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[10]",
                "forma_pago": [
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[65]",
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[66]"
                ]
            },
            "caratula": {
                "poliza": [
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[176]",
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[11]"
                    ],
                
                "fecha_emision": [
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[58]",
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[54]"
                ],
                "dia": "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[60]",
                "mes": "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[62]",
                "año": "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[64]"
            },
            "factura": {
                "folio": "/html/body/div[1]/div[2]/div[2]/div[2]/div/div[2]/span[13]",
                "poliza": "/html/body/div[1]/div[2]/div[2]/div[2]/div/div[2]/span[21]"
            }
        },
        "gastos_medicos": {
            "caratula": {
                "poliza": [
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[334]",
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[12]",
                    ],
                "emision_dia": "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[78]",
                "emision_mes": "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[80]",
                "emision_año": "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[82]"
            },
            "recibo": {
                "serie": "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[10]",
                "poliza": [
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[32]",
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[33]"
                ],
                "forma_pago": [
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[65]",
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[66]"
                ]
            },
            "factura": {
                "poliza": [
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div/div[2]/span[80]",
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div/div[2]/span[81]",
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div/div[2]/span[76]"
                ]
            },
            "recibo_endoso": {
                "poliza": [
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[31]",
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div/div[2]/span[81]",
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[33]"
                ],
                "serie": [
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[106]",
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[104]"
                    ],
                "forma_pago": [
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[94]",
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[96]"
                ]
            },
            "nota_de_credito":{
                "poliza": [
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div/div[2]/span[81]"
                ]
            },
            "endoso": { 
                "poliza": [
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[173]",
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[128]"
                ],
                "fecha_de_expedicion":[
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[31]",
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[65]"
                ],
                
                
                "forma_pago": [
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[63]",
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[65]",
                    "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[29]"
                ]
                
            }
        },
        "autos": {
            "caratula": {
                "fecha_emision": "/html/body/div[1]/div[2]/div[2]/div[2]/div[3]/div[2]/span[19]"
            },
            "recibo": {
                "poliza": "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[79]",
                "forma_pago": "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[110]",
                "serie": "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[80]"
            },
            "factura": {
                "folio": "/html/body/div[1]/div[2]/div[2]/div[2]/div/div[2]/span[55]",
                "poliza": "/html/body/div[1]/div[2]/div[2]/div[2]/div/div[2]/span[81]"
            }
        },
        "danos": {
            "caratula": {
                "poliza": "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[1]",
                "fecha_emision": "/html/body/div[1]/div[2]/div[2]/div[2]/div[2]/div[2]/span[141]"
            },
            "recibo": {
                "forma_pago": "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[20]",
                "poliza": "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[135]",
                "serie": "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[129]"
            },
            "factura": {
                "folio": "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[143]",
                "poliza": "/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/span[70]"
            }
        }
    }
    
    # Patrones de validación
    PATRONES_VALIDACION = {
        "poliza": r'^\d{5,16}$',
        "numero_de_poliza": r'^\d{5,16}$',
        "forma_pago": r'^[A-ZÁÉÍÓÚÑ\s]+$',
        "fecha_de_expedicion": "date",
        "fecha_emision": "date",
        "dia": r'^\d{1,2}$',
        "mes": r'^\d{1,2}$', 
        "año": r'^\d{4}$',
        "serie": r'^\d{1,4}/\d{1,4}$'
    }
    
    # Normalizar ramo
    ramo_key = ramo.strip().lower().replace(" ", "_").replace("ñ", "n")
    
    # Verificar si tenemos configuración para este ramo y tipo
    if ramo_key not in DATOS_EXTRACCION:
        print(f"⚠️ No hay configuración de extracción para ramo: {ramo}")
        return {}
    
    if tipo_doc not in DATOS_EXTRACCION[ramo_key]:
        print(f"⚠️ No hay configuración de extracción para tipo: {tipo_doc} en ramo {ramo}")
        return {}
    
    # Extraer datos
    datos_extraidos = {}
    config_extraccion = DATOS_EXTRACCION[ramo_key][tipo_doc]
    
    print(f"\n🔍 EXTRACIENDO DATOS - Ramo: {ramo}, Tipo: {tipo_doc}")
    print("=" * 50)
    
    for campo, xpath_config in config_extraccion.items():
        # Manejar tanto XPaths individuales como listas
        xpaths = xpath_config if isinstance(xpath_config, list) else [xpath_config]
        valores_encontrados = []
        
        # Recopilar todos los valores encontrados
        for i, xpath in enumerate(xpaths):
            try:
                elemento = driver.find_element(By.XPATH, xpath)
                valor = elemento.text.strip()
                if valor:
                    # Validar el valor según el tipo de campo
                    es_valido = validar_valor_campo(campo, valor, PATRONES_VALIDACION)
                    
                    valores_encontrados.append({
                        'valor': valor,
                        'valido': es_valido,
                        'indice': i + 1
                    })
                    
                    estado = "✅" if es_valido else "⚠️"
                    print(f"   {estado} {campo.upper()} opción {i+1}: '{valor}'")
                    
            except Exception:
                print(f"   ❌ {campo.upper()} opción {i+1}: No encontrado")
                continue
        
        # Elegir el mejor valor
        if valores_encontrados:
            # Priorizar valores válidos
            valores_validos = [v for v in valores_encontrados if v['valido']]
            
            if valores_validos:
                mejor_valor = valores_validos[0]
                datos_extraidos[campo] = mejor_valor['valor']
                print(f"✅ {campo.upper()} SELECCIONADO: '{mejor_valor['valor']}'")
            else:
                # Si ninguno es válido, usar el primero con advertencia
                mejor_valor = valores_encontrados[0]
                datos_extraidos[campo] = mejor_valor['valor']
                print(f"⚠️  {campo.upper()} USADO: '{mejor_valor['valor']}'")
        else:
            datos_extraidos[campo] = None
            print(f"❌ {campo.upper()}: No encontrado")
    
    print("=" * 50)
    return datos_extraidos

def validar_valor_campo(campo, valor, patrones):
    """
    Valida si un valor cumple con el patrón esperado para el campo.
    """
    import re
    
    if campo not in patrones:
        return True  # Si no hay patrón definido, siempre es válido
    
    patron = patrones[campo]
    return bool(re.match(patron, valor, re.IGNORECASE))

