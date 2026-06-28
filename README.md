# Detección de Desinformación mediante Web Scraping

## Descripción

Este proyecto tiene como objetivo recopilar información de verificaciones de hechos (fact-checks) y de la confiabilidad de diferentes medios de comunicación mediante técnicas de web scraping.

Los datos obtenidos son integrados para analizar la relación entre noticias falsas y la credibilidad de las fuentes donde fueron publicadas.

## Estructura del proyecto

```
data/
│── fact_checks.csv
│── sources.csv
│── report.csv

integration/
│── integrate.py

scrapers/
│── snopes_scraper.py
│── mbfc_scraper.py
```

## Requisitos

Instalar las siguientes librerías:

```bash
pip install pandas requests beautifulsoup4 tldextract
```

## Ejecución

1. Ejecutar el scraper de Snopes:

```bash
python scrapers/snopes_scraper.py
```

2. Ejecutar el scraper de Media Bias Fact Check:

```bash
python scrapers/mbfc_scraper.py
```

3. Ejecutar la integración de datos:

```bash
python integration/integrate.py
```

## Archivos generados
- `fact_checks.csv`: verificaciones obtenidas desde Snopes.
- `sources.csv`: información de confiabilidad de los medios obtenida desde MBFC.
- `report.csv`: resultado de la integración y análisis de los datos.

## Integrantes
- Jeremi
- Juan
- Bisitte
- Andy
