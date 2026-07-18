import argparse
import math
import random
import time
from pathlib import Path

from config import BASE_URL, FECHA_HOY
from scraper import (
    crear_session,
    obtener_soup,
    parsear_listado,
    procesar_oferta,
    guardar_excel
)
from utils import logger, clave_oferta, cargar_historial, limpiar_raw_antiguo

# Las ofertas (filas del Excel y carpetas raw_data) se conservan este tiempo
DIAS_RETENCION = 30

# Guardar el Excel maestro cada N páginas para no perder avance si el proceso cae
GUARDAR_CADA_PAGINAS = 5


def main(DATA_DIR, MAX_PAGES=None, DELAY_EXPECTED=3.0):
    # Definición de rutas
    BASE_DIR = Path(DATA_DIR) / "first_job"
    RAW_DATA_DIR = BASE_DIR / "raw_data" / FECHA_HOY
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    MASTER_XLSX = BASE_DIR / "summary_data.xlsx"

    # Limpiar carpetas de raw_data con más de DIAS_RETENCION días
    limpiar_raw_antiguo(BASE_DIR / "raw_data", dias=DIAS_RETENCION)

    # Si MAX_PAGES es None o 0, recorremos todas (infinito)
    if not MAX_PAGES or MAX_PAGES <= 0:
        logger.info("Configurado para recorrer TODAS las páginas disponibles.")
        MAX_PAGES = float('inf')
    else:
        logger.info(f"Configurado para recorrer un máximo de {MAX_PAGES} páginas.")

    logger.info(f"Retraso configurado (Esperanza): {DELAY_EXPECTED}s con Varianza del 5%.")

    # Cargar historial: las filas previas se conservan (con su fecha original) y
    # sus ids se marcan como vistos para no volver a descargarlas.
    lista_datos, ids_vistos = cargar_historial(MASTER_XLSX, dias=DIAS_RETENCION)
    ofertas_previas = len(lista_datos)

    try:
        logger.info(f"Iniciando scraping en {BASE_URL}")
        session = crear_session()

        url_actual = BASE_URL
        pagina = 1

        while url_actual and pagina <= MAX_PAGES:
            logger.info(f"Procesando página {pagina}: {url_actual}")
            soup = obtener_soup(session, url_actual)
            if soup is None:
                break

            urls_ofertas, next_url = parsear_listado(soup)
            if not urls_ofertas:
                logger.warning("No se detectaron ofertas en la página. Finalizando...")
                break

            nuevas = 0
            omitidas = 0
            for url in urls_ofertas:
                if clave_oferta(url) in ids_vistos:
                    omitidas += 1
                    continue
                ids_vistos.add(clave_oferta(url))

                if procesar_oferta(session, url, FECHA_HOY, lista_datos, RAW_DATA_DIR):
                    nuevas += 1
                # Pausa corta entre ofertas para no saturar el sitio
                time.sleep(random.uniform(0.3, 0.8))

            logger.info(f"Página procesada: {nuevas} ofertas nuevas, {omitidas} ya conocidas.")

            # Guardado incremental del Excel maestro
            if pagina % GUARDAR_CADA_PAGINAS == 0 and len(lista_datos) > ofertas_previas:
                guardar_excel(lista_datos, MASTER_XLSX)

            if not next_url:
                logger.info("No hay más páginas. Finalizando...")
                break

            url_actual = next_url
            pagina += 1

            # CÁLCULO DE RETRASO CON DISTRIBUCIÓN UNIFORME
            # Varianza = 0.05 * Esperanza. Ancho del intervalo (b-a) = sqrt(0.6 * Esperanza)
            mu = DELAY_EXPECTED
            ancho = math.sqrt(0.6 * mu) if mu > 0 else 0
            a = mu - (ancho / 2)
            b = mu + (ancho / 2)

            retraso = random.uniform(max(0.1, a), max(0.1, b))
            logger.info(f"Esperando {retraso:.2f} segundos antes de la siguiente página...")
            time.sleep(retraso)

    except Exception as e:
        logger.error(f"Error crítico durante la ejecución: {e}", exc_info=True)
    finally:
        # Guardar dentro del finally: así no se pierde lo scrapeado si el
        # proceso se interrumpe (Ctrl+C) o falla a mitad de camino.
        if lista_datos:
            guardar_excel(lista_datos, MASTER_XLSX)
            nuevas_total = len(lista_datos) - ofertas_previas
            logger.info(f"Scraping finalizado. {nuevas_total} ofertas nuevas hoy, {len(lista_datos)} en total (últimos {DIAS_RETENCION} días).")
            logger.info(f"Datos guardados en {MASTER_XLSX}")
        else:
            logger.warning("No se encontraron datos para guardar.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper de FirstJob con requests (sin navegador).")
    parser.add_argument("--dir", type=str, default="data", help="Directorio raíz para los datos.")
    parser.add_argument(
        "--pages",
        "-p",
        type=int,
        default=None,
        help="Cantidad máxima de páginas a recorrer (0 o vacío = todas)."
    )
    parser.add_argument(
        "--delay",
        "-d",
        type=float,
        default=3.0,
        help="Tiempo esperado (Esperanza) de retraso entre páginas."
    )

    args = parser.parse_args()
    try:
        main(args.dir, args.pages, args.delay)
    except KeyboardInterrupt:
        logger.info("Proceso interrumpido por el usuario.")
# python "main.py" --dir "data" --pages 2 --delay 1.5
# python "main.py" --dir "data" --delay 2
