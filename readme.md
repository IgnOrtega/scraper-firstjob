# FirstJob Scraper

Scraper automatizado desarrollado con **Playwright (Python)** para extraer ofertas laborales desde firstjob.

El scraper:

- Recorre todas las páginas disponibles
- Abre cada oferta en una nueva pestaña
- Descarga el contenido completo en archivos `.txt`
- Genera un resumen de todas las ofertas en formato Excel (`.xlsx`)
---

## 📦 Estructura del Proyecto
firstjob_scraper/  
│  
├── main.py # Punto de entrada del programa  
├── config.py # Configuración global  
├── browser.py # Inicialización y cierre de navegador  
├── scraper.py # Lógica principal de scraping  
└── utils.py # Funciones auxiliares  

---

## ⚙️ Requisitos

- Python 3.12.10
- playwright==1.58.0
- Pandas==3.0.1
- Numpy==2.4.2
- openpyxl==3.1.5

Instalación de dependencias:

```bash
pip install numpy==2.4.2 pandas==3.0.1 playwright==1.58.0 openpyxl==3.1.5
playwright install
```
o utilizando el archivo ```requirements.txt``` con el comando: 
pip install -r requirements.txt

## ⚙️ Input
Argumentos necesarios:
- dir → Argumento que indica en donde serán alojados los archivos.
- headless → Argumento que indica si activa el modo headless, por defecto el valor es `true`.

## 🚀 Cómo Ejecutar
Desde la raíz del proyecto puedes ejecutar por ejemplo:
```bash
python "main.py" --dir "C:\Users\nombre_usuario\Desktop\datos" --headless false
```
El scraper:
- Abre Chromium según el argumento.
- Recorre todas las páginas.
- Descarga cada oferta en ```/data/first_job/raw_data/.../```
- Genera el archivo: ```/data/first_job/summary_data/.../summary_data.xlsx```

Columna	Descripción  
- Nombre: Título de la oferta
- Fecha: Fecha de ejecución
- Pageweb: URL de la oferta

## 📁 Output
Archivos generados:
- data/first_job/raw_data/.../*.txt → Contenido completo de cada oferta
- data/first_job/summary_data/.../summary_data.xlsx → Resumen con columnas

Columnas Descripción Excel:
- Nombre: Título de la oferta
- Fecha: Fecha de ejecución
- Pageweb: URL de la oferta

## 🧠 Arquitectura
El proyecto sigue principios de separación de responsabilidades:
- config.py → Variables globales y configuración
- browser.py → Ciclo de vida del navegador
- scraper.py → Lógica de extracción
- utils.py → Funciones reutilizables
- main.py → Orquestación