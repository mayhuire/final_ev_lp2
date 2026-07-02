# Detección de Desinformación mediante Web Scraping

## Integrantes
- Jeremi angel, Mayhuire Calle (usuario en GitHub : mayhuire)
- Juan Carlos, Tapia Casa (usuario en GitHub : 20221418-crypto)
- Bisitte Milagros, Becerra Jesus (usuario en GitHub : Bisitte20)
- Andy Weber, Potosino Apaza (usuario en GitHub : skinsz20)

## Planteamiento y Justificación del Problema

### El problema:
El internet y las redes sociales propagan información de forma masiva y rápida, lo que ha generado un aumento drástico de noticias falsas (fake news), en especial sobre la salud. Esto afecta negativamente la toma de decisiones de las personas y daña la confianza en fuentes fiables.
### La oportunidad:
Existe la necesidad de crear herramientas automáticas que recopilen y analicen datos de plataformas de verificación.  El enfoque del proyecto: Usar técnicas de extracción de datos (web scraping) para fusionar información de dos plataformas clave:  
#### Snopes: Un sitio dedicado a desmentir mitos y verificar rumores.
#### Media Bias Fact Check (MBFC): Un portal que evalúa el sesgo político y la confiabilidad factual de los medios.

## Estructura del proyecto

```
data/
│── fact_checks.csv
│── sources.csv
│── report.csv

integration/
│── integrate.py: Carga ambos archivos y usa la librería tldextract para limpiar y estandarizar los dominios (quitando https:// o www.). Luego, mediante la función merge de Pandas, une los datos por dominio.

scrapers/
│── snopes_scraper.py: Extrae las últimas verificaciones de Snopes. Utiliza las estructuras JSON-LD (ClaimReview) ocultas en el HTML para capturar la afirmación (claim), el veredicto (rating), la fecha, la categoría y el dominio de origen. Guarda todo en fact_checks.csv.
│── mbfc_scraper.py: Extrae de MBFC el dominio del medio, su orientación política (bias) y su nivel de veracidad (factual reporting). Limpia duplicados y guarda en sources.csv.
```

## Archivos generados
- `fact_checks.csv`: verificaciones obtenidas desde Snopes.
- `sources.csv`: información de confiabilidad de los medios obtenida desde MBFC.
- `report.csv`: resultado de la integración y análisis de los datos.

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
## Resultados esperados
### Los datos:
En la prueba ejecutada se lograron extraer exitosamente 20 verificaciones de Snopes y 36 fuentes de MBFC.
### El resultado:
Se generó el archivo report.csv con los 20 registros cruzados.
### Comportamiento del sistema:
Si un dominio de Snopes no existía en la base de datos de MBFC, el sistema dejó esos campos vacíos de forma correcta (un Left Join en Pandas).
### Análisis de la captura:
(Aquí puedes apuntar a las imágenes adjuntas en tu informe). Se observa cómo el dataset vincula reclamos como fotos falsas o desinformación electoral con sus respectivos veredictos (Fake, True, Mixture, Incorrect Attribution) y sus dominios limpios (ufc.com, facebook.com, etc.).

## Reflexión Ética
Este punto es muy importante en proyectos de scraping. Explica los pilares de responsabilidad que siguieron.
### Fines académicos y no comerciales:
No hay intención de lucro.
### Privacidad:
Solo se recopilaron metadatos públicos de las noticias (afirmación, veredicto, fecha). No se extrajeron comentarios, nombres ni datos privados de usuarios.
### Respeto a los servidores:
Se programaron pausas (delays) entre las peticiones para no saturar ni realizar descargas masivas que afectaran el rendimiento de Snopes o MBFC.

## Reflexión sobre el uso de LLMs (Modelos de Inteligencia Artificial)
### Soporte inicial:
Se utilizaron herramientas de IA (como ChatGPT/Gemini) para crear los primeros borradores de los scrapers y estructurar la documentación.
### El factor humano:
Sin embargo, la IA no lo hace todo. El equipo tuvo que modificar manualmente los selectores HTML reales que fallaban, corregir la lógica de integración y limpiar los dominios.

## Conclusiones
Se demostró que el web scraping es una técnica poderosa para centralizar datos de múltiples fuentes en un solo lugar.  La integración en Python fue exitosa gracias a la normalización de dominios web.  El equipo reforzó habilidades prácticas de programación en Python, uso de librerías de extracción (requests, BeautifulSoup), procesamiento de datos (Pandas, tldextract) y control de versiones.
