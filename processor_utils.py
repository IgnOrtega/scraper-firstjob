import re
import unicodedata

PESOS_DATA = {
    "python": 3, "lenguaje de programacion": 3, "lenguajes de programación": 3,
    "numpy": 3, "pandas": 3, "sql": 3, "machine learning": 4, "modelo": 3,
    "etl": 3, "analisis": 1, "estadistica": 2, "matematica": 2, "informatica": 2,
    "trainee": 7, "excel": 2, "power bi": 2, "looker studio": 2, "looker": 2,
    "tableu": 2, "tableau": 2, "cloud": 2, "gcp": 2, "aws": 2, "azure": 2,
    "git": 2, "html": 2, "css": 2, "javascript": 2, "llm": 3, "rag": 3,
    "gemini": 3, "maker": 3, "zapier": 3, "n8n": 3, "workflow automation": 3,
    "no-code": 3, "low-code": 3, "orquestacion": 3, "orchestration": 3
}

KEYWORDS_INGLES = ["english", "ingles", "bilingue"]
KEYWORDS_REMOTO = ["remoto", "remote", "100 remoto", "homeoffice"]
KEYWORDS_HIBRIDO = ["hibrido", "hybrid", "hibrida"]
KEYWORDS_PRESENCIAL = ["presencial", "onsite"]
KEYWORDS_PART_TIME = ["part time", "medio tiempo"]
KEYWORDS_PRACTICA = ["practica", "intership", "internship", "seguro escolar"]
KEYWORDS_TRAINEE = ["traine", "trainee", "traini", "trainy"]
KEYWORDS_AUTOMATIZACION = [
    "n8n", "zapier", "make.com", "make (integromat)", "integromat",
    "automation", "automatizacion", "automations", "automatizar",
    "workflow automation", "automated workflows", "workflows",
    "api integration", "integraciones", "integrations", "webhooks",
    "api rest", "rest api", "no-code", "low-code", "power automate",
    "microsoft flow", "process automation", "business process automation",
    "automatizacion de procesos", "flujo de trabajo", "orquestacion", "orchestration"
]


def limpiar_texto(texto: str) -> str:
    if not texto: return ""
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def calcular_score(texto: str):
    texto_normalizado = " ".join(dict.fromkeys(texto.split()))
    score = 0
    coincidencias = {}
    palabras = texto_normalizado.split()
    for keyword, peso in PESOS_DATA.items():
        if " " in keyword:
            cantidad = texto_normalizado.count(keyword)
        else:
            cantidad = palabras.count(keyword)
        if cantidad > 0:
            coincidencias[keyword] = cantidad
            score += peso * cantidad
    return score, list(coincidencias.keys())


def detectar_modalidad(texto: str, keywords: list) -> int:
    return int(any(k in texto for k in keywords))


def analizar_oferta(cuerpo_texto):
    texto_limpio = limpiar_texto(cuerpo_texto)
    score, coincidencias = calcular_score(texto_limpio)
    return {
        "puntaje_data": score,
        "keyword": ", ".join(coincidencias),
        "ingles": detectar_modalidad(texto_limpio, KEYWORDS_INGLES),
        "remoto": detectar_modalidad(texto_limpio, KEYWORDS_REMOTO),
        "hibrido": detectar_modalidad(texto_limpio, KEYWORDS_HIBRIDO),
        "presencial": detectar_modalidad(texto_limpio, KEYWORDS_PRESENCIAL),
        "part_time": detectar_modalidad(texto_limpio, KEYWORDS_PART_TIME),
        "practica": detectar_modalidad(texto_limpio, KEYWORDS_PRACTICA),
        "trainee": detectar_modalidad(texto_limpio, KEYWORDS_TRAINEE),
        "automatizacion": detectar_modalidad(texto_limpio, KEYWORDS_AUTOMATIZACION)
    }
