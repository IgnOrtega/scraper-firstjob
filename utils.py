import re
import argparse
import logging
import asyncio
import pandas as pd
from pathlib import Path
from functools import wraps

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

def async_retry(max_retries: int = 3, delay: float = 1.0):
    """
    Decorador para reintentar funciones asíncronas.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Intento {attempt}/{max_retries} fallido para {func.__name__}: {e}")
                    if attempt < max_retries:
                        await asyncio.sleep(delay * attempt)
            logger.error(f"Todos los intentos fallaron para {func.__name__}")
            raise last_exception
        return wrapper
    return decorator

def obtener_datos_previos(summary_base_dir: Path) -> dict:
    """
    Busca el archivo summary_data.xlsx más reciente y devuelve un diccionario {url: datos}.
    """
    if not summary_base_dir.exists():
        return {}

    # Listar carpetas de fechas y ordenarlas
    carpetas_fechas = sorted([d for d in summary_base_dir.iterdir() if d.is_dir()])
    
    if not carpetas_fechas:
        return {}

    # Empezamos por la más reciente
    for carpeta in reversed(carpetas_fechas):
        archivo_excel = carpeta / "summary_data.xlsx"
        if archivo_excel.exists():
            try:
                logger.info(f"Cargando datos previos desde {archivo_excel}")
                df = pd.read_excel(archivo_excel)
                # Convertir a diccionario usando 'Pageweb' como clave
                return df.set_index('Pageweb').to_dict('index')
            except Exception as e:
                logger.error(f"Error al cargar el archivo previo {archivo_excel}: {e}")
    
    return {}

def str2bool(value):
    if isinstance(value, bool):
        return value
    if value.lower() in ("true", "1", "yes"):
        return True
    if value.lower() in ("false", "0", "no"):
        return False
    raise argparse.ArgumentTypeError("Booleano esperado.")

def sanitize_filename(filename: str) -> str:
    """
    Limpia un string para que pueda ser usado como nombre de archivo.
    """
    return re.sub(r'[\\/:*?"<>|]', '_', filename)


async def centrar_pantalla(element) -> None:
    """
    Centra un elemento dentro del viewport usando JavaScript (asíncrono).
    """
    await element.evaluate("""
        (el) => {
            el.scrollIntoView({
                behavior: 'auto',
                block: 'center',
                inline: 'center'
            });
        }
    """)
