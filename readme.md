# FirstJob Scraper 🚀

Scraper automatizado desarrollado con **Python** y **Requests** para extraer ofertas laborales desde **firstjob.me** (prácticas, trainees y primeros empleos).

Aunque el sitio muestra las ofertas con "scroll infinito", por detrás consume páginas normales (`?page=1,2,3...`) que el servidor entrega completas — por eso no se necesita navegador ni JavaScript.

---

## ✨ Características Principales

- **Sin navegador:** Peticiones HTTP simples con `requests` + parseo con BeautifulSoup. Rápido, liviano y apto para GitHub Actions.
- **Paginación automática:** Sigue el enlace `rel="next"` del listado hasta agotar las páginas.
- **Gestión de Datos:**
  - Guarda la descripción completa de cada oferta en archivos `.txt` individuales.
  - Genera un Excel maestro con historial rodante de 30 días.
- **Detección de Duplicados:** Las ofertas ya vistas (por id) no se vuelven a descargar.
- **Análisis por Puntaje:** Cada oferta se puntúa según keywords de perfil data/automatización y se marcan flags (remoto, híbrido, inglés, part-time, práctica, trainee).
- **Ejecución Automática:** Workflow de GitHub Actions que corre el scraper a diario y commitea los resultados en `data/`.

---

## 🛠️ Requisitos

- **Python:** 3.12+
- **Dependencias:** Listadas en `requirements.txt` (Requests, BeautifulSoup4, Pandas, openpyxl, etc.)

---

## 🚀 Instalación y Configuración

1. **Clonar el repositorio o descargar los archivos.**
2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Uso (Línea de Comandos)

El script se ejecuta desde `main.py` y acepta los siguientes argumentos:

| Argumento | Descripción | Por Defecto |
| :--- | :--- | :--- |
| `--dir` | Directorio raíz donde se guardarán los resultados. | `data` |
| `--pages` | Cantidad máxima de páginas a recorrer (0 para todas; 20 ofertas por página). | `0` (Todas) |
| `--delay` | Tiempo promedio de espera (segundos) entre páginas. | `3.0` |

### Ejemplo de ejecución:
```bash
python main.py --dir data --pages 5 --delay 2.5
```

---

## 📁 Estructura del Proyecto

```text
firstjob_scraper/
├── main.py              # Punto de entrada y orquestación del flujo.
├── scraper.py           # Descarga y parseo de listado y ofertas.
├── processor_utils.py   # Análisis por puntaje/keywords y flags de modalidad.
├── config.py            # Configuración global (URL del listado, fecha).
├── utils.py             # Funciones auxiliares (logs, historial, limpieza).
├── requirements.txt     # Librerías necesarias.
└── readme.md            # Documentación del proyecto.
```

---

## 📊 Salida de Datos (Output)

Los archivos se organizan automáticamente en la carpeta indicada en `--dir` (en GitHub Actions: `data/` en la raíz del repo):

1. **Raw Data (`/first_job/raw_data/YYYY-MM-DD/*.txt`):**
   - Un archivo por cada oferta, nombrado como `titulo_sanitizado_idOferta.txt`.
   - Contiene la descripción completa de la vacante.
2. **Summary Data (`/first_job/summary_data.xlsx`):**
   - Excel maestro consolidado (historial rodante de 30 días) con columnas: `Fecha`, `Nombre`, `Empresa`, `Ubicacion`, `Tipo`, `Pageweb`, `puntaje_data`, `keyword`, `ingles`, `remoto`, `hibrido`, `presencial`, `part_time`, `practica`, `trainee`, `automatizacion`, `oferta`.

Las carpetas de `raw_data` y las filas del Excel con más de 30 días se eliminan automáticamente en cada corrida.

---

## 🧠 Arquitectura Técnica

El scraper sigue este ciclo de vida:
1. **Inicio:** Limpia datos antiguos y carga el historial del Excel maestro (ids ya vistos).
2. **Listado:** Descarga cada página del listado y extrae las URLs de las cards (`.card-job`).
3. **Extracción:** Descarga cada oferta nueva, la analiza por puntaje y guarda su `.txt` (pausa corta entre ofertas).
4. **Paginación:** Sigue el enlace `rel="next"` con un retraso aleatorio entre páginas.
5. **Cierre:** Consolida historial + ofertas nuevas en el Excel maestro (también se guarda incrementalmente cada 5 páginas).

---

## ⚠️ Notas Legales
Este proyecto tiene fines educativos. El uso de herramientas de web scraping debe respetar los términos y condiciones del sitio web (`firstjob.me/robots.txt`) y la legislación vigente sobre protección de datos.
