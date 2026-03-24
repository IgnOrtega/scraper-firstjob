import os
from datetime import datetime
import pandas as pd
import argparse
import asyncio
from pathlib import Path
from config import BASE_URL, FECHA_HOY
from browser import iniciar_browser, cerrar_browser
from scraper import (
    scrapear_pagina,
    ir_siguiente_pagina,
    guardar_excel
)
from utils import str2bool, logger
from utils import str2bool, logger, obtener_datos_previos


async def main(DATA_DIR, HEADLESS_BOOL):
    RAW_DATA_DIR = Path(f"{DATA_DIR}/first_job/raw_data/{FECHA_HOY}")
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    SUMMARY_BASE_DIR = Path(f"{DATA_DIR}/first_job/summary_data")
    SUMMARY_DATA_DIR = SUMMARY_BASE_DIR / FECHA_HOY
    SUMMARY_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Cargar datos de ejecuciones anteriores para evitar descargas innecesarias
    datos_previos = obtener_datos_previos(SUMMARY_BASE_DIR)
    if datos_previos:
        logger.info(f"Se encontraron {len(datos_previos)} ofertas previas para omitir descarga.")

    lista_datos = []

    playwright, browser, context, page = await iniciar_browser(HEADLESS_BOOL)

    try:
        logger.info(f"Iniciando scraping en {BASE_URL}")
        await page.goto(BASE_URL)
        cartel_publicidad = page.locator("#notification_modal_link")

        # Esperar un poco a que aparezca el modal si existe
        await asyncio.sleep(2)
        if await cartel_publicidad.is_visible():
            logger.info("Cerrando publicidad...")
            await page.get_by_role("button", name="Close").click()

        pagina = 1
        while True:
            logger.info(f"Scrapeando página {pagina}...")

            await scrapear_pagina(
                page,
                context,
                FECHA_HOY,
                lista_datos,
                RAW_DATA_DIR,
                datos_previos
            )

            if not await ir_siguiente_pagina(page):
                logger.info("No hay más páginas. Finalizando...")
                break

            pagina += 1
            # Pequeña pausa entre páginas para no ser detectado
            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"Error durante la ejecución: {e}", exc_info=True)
    finally:
        await cerrar_browser(playwright, browser)


    if lista_datos:
        output_file = Path(SUMMARY_DATA_DIR) / "summary_data.xlsx"
        guardar_excel(lista_datos, output_file)
        logger.info(f"Descarga finalizada. Datos guardados en {output_file}")
    else:
        logger.warning("No se encontraron datos para guardar.")

    
    
    
    



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper automatizado mejorado con Playwright y Concurrencia.")
    parser.add_argument("--dir", type=str, required=True, help="Directorio de alojamiento de archivos descargados.")

    parser.add_argument(
            "--headless",
            type=str2bool,
            default=False,
            help="Activa o desactiva headless."
        )
    args = parser.parse_args()
    
    asyncio.run(main(args.dir, args.headless))
# python "main.py" "C:\Users\Nach\Desktop\datos\first_job" "false"