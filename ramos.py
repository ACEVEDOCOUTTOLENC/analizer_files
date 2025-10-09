# ramos.py

EMAIL_TO_RAMO = {
    # VIDA
    "vida@acevedocouttolenc.com": "VIDA",
    "vida1@acevedocouttolenc.com": "VIDA",
    "vida2@acevedocouttolenc.com": "VIDA",
    "vida3@acevedocouttolenc.com": "VIDA",

    # GASTOS MÉDICOS
    "gmm@acevedocouttolenc.com": "GASTOS MEDICOS",
    "gmm1@acevedocouttolenc.com": "GASTOS MEDICOS",
    "gmm2@acevedocouttolenc.com": "GASTOS MEDICOS",
    "gmm3@acevedocouttolenc.com": "GASTOS MEDICOS",
    "gmm4@acevedocouttolenc.com": "GASTOS MEDICOS",
    "gmm5@acevedocouttolenc.com": "GASTOS MEDICOS",

    # DAÑOS
    "danos@acevedocouttolenc.com": "DAÑOS",
    "danos1@acevedocouttolenc.com": "DAÑOS",
    "danos2@acevedocouttolenc.com": "DAÑOS",
    "danos3@acevedocouttolenc.com": "DAÑOS",

    # AUTOS
    "autos@acevedocouttolenc.com": "AUTOS",
    "autos1@acevedocouttolenc.com": "AUTOS",
    "autos2@acevedocouttolenc.com": "AUTOS",
    "autos3@acevedocouttolenc.com": "AUTOS",
    "autos4@acevedocouttolenc.com": "AUTOS",
}

def get_ramo_from_email(email: str) -> str:
    """Retorna el ramo (área) al que pertenece el correo."""
    return EMAIL_TO_RAMO.get(email.lower(), "DESCONOCIDO")
