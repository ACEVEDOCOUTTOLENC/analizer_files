import re
from collections import Counter
from companias import COMPANIAS

def get_cia(driver):
    spans = driver.find_elements("tag name", "span")
    conteo = Counter()

    for span in spans:
        texto = span.text.strip().upper()
        if not texto:
            continue
        for compania, alias_list in COMPANIAS.items():
            for alias in alias_list:
                if re.search(rf"\b{re.escape(alias.upper())}\b", texto):
                    conteo[compania] += len(
                        re.findall(rf"\b{re.escape(alias.upper())}\b", texto)
                    )

    if not conteo:
        return None

    total = sum(conteo.values())
    porcentajes = {cia: (count / total) * 100 for cia, count in conteo.items()}
    cia_top = max(porcentajes, key=porcentajes.get)

    print("📊 Resultados detección compañías:")
    for cia, pct in sorted(porcentajes.items(), key=lambda x: x[1], reverse=True):
        print(f"   - {cia}: {pct:.2f}%")

    print(f"✅ Compañía detectada: {cia_top}")
    return cia_top
