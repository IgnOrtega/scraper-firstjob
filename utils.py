import re
import logging
import shutil
from datetime import datetime, timedelta

import pandas as pd
from pathlib import Path


def setup_logger(name: str = "firstjob_scraper", log_file: str = "scraper.log", level=logging.INFO):
    """
    Configura y devuelve un logger.
    """
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    handler = logging.FileHandler(log_file, encoding='utf-8')
    handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        logger.addHandler(handler)
        logger.addHandler(console_handler)

    return logger


logger = setup_logger()


def clave_oferta(url: str) -> str:
    """
    Clave de deduplicación de una oferta: el id numérico de su URL
    (p. ej. 'https://firstjob.me/oferta/54238/practicas-...' -> '54238').
    Si no hay id, se usa la URL normalizada completa.
    """
    limpia = url.split('?')[0].rstrip('/')
    m = re.search(r"/oferta/(\d+)", limpia)
    return m.group(1) if m else limpia


def cargar_historial(master_path: Path, dias: int = 30):
    """
    Carga el Excel maestro, descarta filas con más de `dias` días y devuelve:
      (filas, ids_vistos)
    - filas: lista de dicts con las ofertas históricas (conservan su fecha original).
    - ids_vistos: set de claves de oferta (ver clave_oferta), para que el
      scraper no vuelva a procesar esas ofertas.
    """
    if not master_path.exists():
        return [], set()

    try:
        df = pd.read_excel(master_path)
    except Exception as e:
        logger.error(f"Error al cargar el historial {master_path}: {e}")
        return [], set()

    if df.empty or "Pageweb" not in df.columns:
        return [], set()

    if "Fecha" in df.columns:
        fechas = pd.to_datetime(df["Fecha"], errors="coerce")
        limite = pd.Timestamp.today().normalize() - pd.Timedelta(days=dias)
        df = df[fechas >= limite].copy()
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce").dt.strftime("%Y-%m-%d")

    filas = df.to_dict("records")
    ids_vistos = set()
    for fila in filas:
        url = fila.get("Pageweb")
        if isinstance(url, str):
            ids_vistos.add(clave_oferta(url))

    logger.info(f"Historial cargado: {len(filas)} ofertas de los últimos {dias} días.")
    return filas, ids_vistos


def limpiar_raw_antiguo(raw_base: Path, dias: int = 30) -> None:
    """
    Elimina del disco las carpetas raw_data/YYYY-MM-DD con más de `dias` días.
    """
    if not raw_base.exists():
        return
    limite = datetime.now() - timedelta(days=dias)
    for carpeta in raw_base.iterdir():
        if not carpeta.is_dir():
            continue
        try:
            fecha_carpeta = datetime.strptime(carpeta.name, "%Y-%m-%d")
        except ValueError:
            continue
        if fecha_carpeta < limite:
            try:
                shutil.rmtree(carpeta)
                logger.info(f"Eliminada carpeta antigua de raw_data: {carpeta.name}")
            except Exception as e:
                logger.error(f"Error al eliminar carpeta {carpeta}: {e}")


def sanitize_filename(filename: str) -> str:
    """
    Limpia un string para que pueda ser usado como nombre de archivo.
    """
    return re.sub(r'[\\/:*?"<>|]', '_', filename)
