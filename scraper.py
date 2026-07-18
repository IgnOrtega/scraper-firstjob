import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

from utils import sanitize_filename, logger, clave_oferta
from processor_utils import analizar_oferta

SITE_URL = "https://firstjob.me"
MAX_INTENTOS = 3

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Orden de columnas del Excel maestro (las de análisis van entre Pageweb y oferta)
COLUMNAS_EXCEL = [
    "Fecha", "Nombre", "Empresa", "Ubicacion", "Tipo", "Pageweb",
    "puntaje_data", "keyword", "ingles", "remoto", "hibrido", "presencial",
    "part_time", "practica", "trainee", "automatizacion", "oferta"
]


def crear_session():
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def obtener_soup(session, url):
    """Descarga una URL (con reintentos) y devuelve el árbol BeautifulSoup, o None."""
    for intento in range(1, MAX_INTENTOS + 1):
        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            logger.warning(f"Intento {intento}/{MAX_INTENTOS} fallido para {url}: {e}")
            if intento < MAX_INTENTOS:
                time.sleep(2 * intento)
    logger.error(f"No se pudo descargar {url}.")
    return None


def _absolutizar(url):
    return SITE_URL + url if url and url.startswith("/") else url


def parsear_listado(soup):
    """
    Extrae del listado las URLs de las ofertas (.card-job) y la URL de la
    siguiente página (a[rel=next]). El "scroll infinito" del sitio consume
    estas mismas páginas por detrás, así que basta iterar page=1,2,3...
    """
    urls = []
    for card in soup.select(".card-job"):
        enlace = card.select_one("a")
        if not enlace:
            continue
        url = _absolutizar(enlace.get("href"))
        if url and url not in urls:
            urls.append(url)

    siguiente = soup.select_one('a[rel="next"]')
    next_url = _absolutizar(siguiente.get("href")) if siguiente else None
    return urls, next_url


def bajar_datos_oferta(session, url, carpeta_destino):
    """
    Descarga el HTML de una oferta y extrae título, empresa, ubicación y texto.
    Devuelve el diccionario de datos o None si falla.
    """
    soup = obtener_soup(session, url)
    if soup is None:
        return None

    # Selectores más robustos para el título
    titulo_tag = soup.select_one("h1, .job-title, .offer-title") or soup.find("h3")
    titulo = titulo_tag.get_text(strip=True).replace("/", "") if titulo_tag else "sin_titulo"

    # Extracción de empresa (con fallback al markup actual del sitio)
    empresa_tag = soup.select_one(".company-name, header a[href*='/empresa/']") \
        or soup.select_one("a.company, .sidebar-company")
    empresa = empresa_tag.get_text(strip=True) if empresa_tag else "N/A"

    # Extracción de ubicación
    ubicacion_tag = soup.select_one(".location, .job-location, span:has(i.fa-map-marker)")
    ubicacion = ubicacion_tag.get_text(strip=True) if ubicacion_tag else "N/A"

    # Extracción de tipo de trabajo/modalidad (con fallback al markup actual: .job-tags)
    tipo_tag = soup.select_one(".job-type, .modality") or soup.select_one(".job-tags")
    tipo = tipo_tag.get_text(" ", strip=True) if tipo_tag else "N/A"

    # Contenido de la oferta
    cuerpos = soup.select(".content-single.content-offer, .description, .offer-content, #job-description")
    texto = ""
    for c in cuerpos:
        texto += c.get_text(strip=True)

    archivo = carpeta_destino / f"{sanitize_filename(titulo)[:120]}_{clave_oferta(url)}.txt"
    archivo.write_text(texto, encoding="utf-8")

    return {
        "Nombre": titulo,
        "Empresa": empresa,
        "Ubicacion": ubicacion,
        "Tipo": tipo,
        "Texto": texto
    }


def procesar_oferta(session, url, fecha_hoy, lista_datos, carpeta_destino):
    """
    Descarga una oferta, la analiza por puntaje/keywords y agrega la fila al resumen.
    Devuelve True si la oferta se procesó correctamente.
    """
    datos = bajar_datos_oferta(session, url, carpeta_destino)
    if not datos:
        return False

    # El análisis incluye título y tipo además de la descripción completa
    analisis = analizar_oferta(f"{datos['Nombre']}\n{datos['Tipo']}\n{datos['Texto']}")

    lista_datos.append({
        "Fecha": fecha_hoy,
        "Nombre": datos["Nombre"],
        "Empresa": datos["Empresa"],
        "Ubicacion": datos["Ubicacion"],
        "Tipo": datos["Tipo"],
        "Pageweb": url,
        **analisis,
        "oferta": datos["Texto"]
    })
    return True


def guardar_excel(lista_datos, output_path):
    try:
        df = pd.DataFrame(lista_datos)
        # Ordenar columnas: primero las conocidas, luego cualquier extra
        orden = [c for c in COLUMNAS_EXCEL if c in df.columns]
        orden += [c for c in df.columns if c not in orden]
        df = df[orden]
        df.to_excel(output_path, index=False)
        logger.info(f"Excel guardado exitosamente en {output_path}")
    except Exception as e:
        logger.error(f"Error al guardar Excel: {e}")
