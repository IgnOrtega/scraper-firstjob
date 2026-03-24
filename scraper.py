import pandas as pd
from pathlib import Path
from utils import sanitize_filename, centrar_pantalla, logger, async_retry
import httpx
from bs4 import BeautifulSoup
import asyncio
from fake_useragent import UserAgent
from config import MAX_RETRIES, MAX_CONCURRENT_REQUESTS, RETRY_DELAY

ua = UserAgent()

@async_retry(max_retries=MAX_RETRIES, delay=RETRY_DELAY)
async def bajar_datos_oferta(client, url, carpeta_destino):
    """
    Descarga el HTML de una oferta laboral y extrae título, empresa, ubicación y texto.
    """
    headers = {
        "User-Agent": ua.random
    }

    response = await client.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Selectores más robustos para el título
    titulo_tag = soup.select_one("h1, .job-title, .offer-title") or soup.find("h3")
    titulo = titulo_tag.get_text(strip=True).replace("/", "") if titulo_tag else "sin_titulo"

    # Extracción de empresa
    empresa_tag = soup.select_one(".company-name, header a[href*='/empresa/']")
    empresa = empresa_tag.get_text(strip=True) if empresa_tag else "N/A"

    # Extracción de ubicación
    ubicacion_tag = soup.select_one(".location, .job-location, span:has(i.fa-map-marker)")
    ubicacion = ubicacion_tag.get_text(strip=True) if ubicacion_tag else "N/A"

    # Extracción de tipo de trabajo (Presencial/Remoto)
    tipo_tag = soup.select_one(".job-type, .modality")
    tipo = tipo_tag.get_text(strip=True) if tipo_tag else "N/A"

    # Contenido de la oferta
    cuerpos = soup.select(".content-single.content-offer, .description, .offer-content, #job-description")
    texto = ""
    for c in cuerpos:
        texto += c.get_text(strip=True)

    # Si no se encontró texto con los nuevos selectores, intentar con el anterior
    if not texto:
        cuerpos = soup.select(".content-single.content-offer")
        for c in cuerpos:
            texto += c.get_text(strip=True)

    archivo = carpeta_destino / f"{sanitize_filename(titulo)}.txt"
    archivo.write_text(texto, encoding="utf-8")

    return {
        "Nombre": titulo,
        "Empresa": empresa,
        "Ubicacion": ubicacion,
        "Tipo": tipo,
        "Texto": texto
    }


async def obtener_info_oferta(semaphore, client, url, fecha_hoy, lista_datos, carpeta_destino, datos_previos=None):
    """
    Extrae la información de una oferta de manera asíncrona.
    Si la oferta ya fue descargada anteriormente (existe en datos_previos), 
    reutiliza la información en lugar de hacer la petición HTTP.
    """    
    async with semaphore:
        try:
            # Verificar si ya tenemos esta URL en datos_previos
            if datos_previos and url in datos_previos:
                logger.info(f"Reutilizando datos previos para: {url}")
                prev = datos_previos[url]
                
                # Re-crear el archivo .txt para que la carpeta actual esté completa
                titulo = str(prev.get("Nombre", "sin_titulo"))
                texto = str(prev.get("oferta", ""))
                
                archivo = carpeta_destino / f"{sanitize_filename(titulo)}.txt"
                archivo.write_text(texto, encoding="utf-8")

                lista_datos.append({
                    "Fecha": fecha_hoy,
                    "Nombre": prev.get("Nombre", "N/A"),
                    "Empresa": prev.get("Empresa", "N/A"),
                    "Ubicacion": prev.get("Ubicacion", "N/A"),
                    "Tipo": prev.get("Tipo", "N/A"),
                    "Pageweb": url,
                    "oferta": texto
                })
                return

            # Si no es previa, descargar normalmente
            logger.info(f"Procesando: {url}")
            datos = await bajar_datos_oferta(client, url, carpeta_destino)

            lista_datos.append({
                "Fecha": fecha_hoy,
                "Nombre": datos["Nombre"],
                "Empresa": datos["Empresa"],
                "Ubicacion": datos["Ubicacion"],
                "Tipo": datos["Tipo"],
                "Pageweb": url,
                "oferta": datos["Texto"]
            })
        except Exception as e:
            logger.error(f"Error al procesar la oferta {url}: {e}")


async def scrapear_pagina(page, context, fecha_hoy, lista_datos, carpeta_destino, datos_previos=None):
    """
    Extrae todas las URLs de la página actual y las procesa concurrentemente.
    """    
    ofertas_locators = page.locator(".card-job")
    urls_a_procesar = []

    count = await ofertas_locators.count()
    logger.info(f"Detectando {count} ofertas en la página...")
    
    for i in range(count):
        oferta = ofertas_locators.nth(i)
        await centrar_pantalla(oferta)
        
        enlace = oferta.locator("a").first
        url = await enlace.get_attribute("href")
        
        if url:
            if url.startswith("/"):
                url = "https://firstjob.me" + url
            
            if url not in urls_a_procesar:
                urls_a_procesar.append(url)

    logger.info(f"Total de ofertas encontradas: {len(urls_a_procesar)}. Procesando concurrentemente...")

    # Semáforo para limitar peticiones simultáneas
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        tareas = [
            obtener_info_oferta(semaphore, client, url, fecha_hoy, lista_datos, carpeta_destino, datos_previos)
            for url in urls_a_procesar
        ]
        await asyncio.gather(*tareas)


async def ir_siguiente_pagina(page) -> bool:
    """
    Intenta navegar a la siguiente página del paginador.
    """    
    paginacion = page.locator(".pagination")
    siguiente = paginacion.locator('xpath=//a[@rel="next"]')

    if await siguiente.count() > 0:
        await siguiente.click()
        await page.wait_for_load_state("domcontentloaded")
        return True

    return False


def guardar_excel(lista_datos, output_path):
    try:
        df = pd.DataFrame(lista_datos)
        df.to_excel(output_path, index=False)
        logger.info(f"Excel guardado exitosamente en {output_path}")
    except Exception as e:
        logger.error(f"Error al guardar Excel: {e}")
