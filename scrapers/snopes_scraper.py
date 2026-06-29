import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from pathlib import Path
from fake_useragent import UserAgent

# Configuración básica compartida
BASE_URL = "https://www.snopes.com"
ua = UserAgent()

# Usamos la misma lógica de carpetas que tu compañera para que los datos caigan al mismo sitio
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
archivo_salida = DATA_DIR / "fact_checks.csv"

def obtener_enlaces_articulos(paginas=2):
    """
    Entra a la página de listado de fact-checks y extrae los enlaces de forma segura.
    Mantiene la firma original de 'paginas' para no romper compatibilidad.
    """
    enlaces = []
    headers = {
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
        "Referer": "https://www.google.com/"
    }
    
    # Por defecto rastreamos la sección principal de fact-check
    ruta_seccion = "/fact-check/"
    
    for num_pag in range(1, paginas + 1):
        url = f"{BASE_URL}{ruta_seccion}page/{num_pag}/" if num_pag > 1 else f"{BASE_URL}{ruta_seccion}"
        print(f"Explorando listado Snopes: {url}")
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            
            if resp.status_code == 403:
                print("⚠️ Snopes detectó tráfico automatizado. Cambiando agente...")
                headers["User-Agent"] = ua.random
                time.sleep(4)
                continue
                
            if resp.status_code != 200:
                continue
                
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Filtro de links adaptativo contra bloqueos de diseño
            links_encontrados = soup.find_all("a", href=True)
            for link in links_encontrados:
                href = link["href"]
                if "/fact-check/" in href and not "/page/" in href and len(href) > 13:
                    if href.startswith("/"):
                        enlaces.append(href)
                    elif href.startswith(BASE_URL):
                        enlaces.append(href.replace(BASE_URL, ""))
                        
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            print(f"Error al obtener listado Snopes página {num_pag}: {e}")
            
    enlaces = list(dict.fromkeys(enlaces))
    print(f"Enlaces Snopes encontrados: {len(enlaces)}")
    return enlaces


def extraer_detalle_articulo(url_relativa):
    """
    Visita el artículo de Snopes y extrae exactamente los 5 campos solicitados:
    claim, rating, date, category, origin_domain (y agrega url para control).
    """
    url_completa = BASE_URL + url_relativa if url_relativa.startswith("/") else url_relativa
    print(f"  Extrayendo Snopes: {url_completa}")
    
    headers = {"User-Agent": ua.random, "Referer": BASE_URL + "/"}
    try:
        resp = requests.get(url_completa, headers=headers, timeout=15)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"  Error al cargar {url_completa}: {e}")
        return None

    datos = {"url": url_completa}

    # 1. --- claim ---
    claim_tag = soup.select_one("div.claim-content p, div.claim-text, .claim-content")
    datos["claim"] = claim_tag.text.strip() if claim_tag else "N/A"

    # 2. --- rating ---
    rating_tag = soup.select_one("span.rating-name, title, h1")
    datos["rating"] = rating_tag.text.strip() if rating_tag else "N/A"

    # 3. --- date ---
    date_tag = soup.select_one("time.entry-date, [datetime], span.date")
    if date_tag and date_tag.has_attr('datetime'):
        datos["date"] = date_tag['datetime']
    elif date_tag:
        datos["date"] = date_tag.text.strip()
    else:
        datos["date"] = "N/A"

    # 4. --- category ---
    tags = soup.select("span.tags a, a.category, li.breadcrumb-item a, .concept-tags a")
    datos["category"] = ", ".join(tag.text.strip() for tag in tags) if tags else "N/A"

    # 5. --- origin_domain ---
    origin_tag = soup.select_one("a.external-link, p.source a, div.sources a")
    datos["origin_domain"] = origin_tag.get("href", "N/A") if origin_tag else "N/A"

    time.sleep(random.uniform(1, 3))
    return datos


def main():
    print("=== SNOPES SCRAPER INDEPENDIENTE ===")
    enlaces = obtener_enlaces_articulos(paginas=2)

    resultados = []
    for i, enlace in enumerate(enlaces):
        print(f"Procesando {i+1}/{len(enlaces)}")
        datos = extraer_detalle_articulo(enlace)
        if datos:
            resultados.append(datos)

    if resultados:
        df = pd.DataFrame(resultados)
        columnas_ordenadas = ["claim", "rating", "date", "category", "origin_domain", "url"]
        df = df.reindex(columns=columnas_ordenadas)
        df.to_csv(archivo_salida, index=False, encoding="utf-8-sig")
        print(f"\n🎉 ¡Guardados {len(df)} registros en {archivo_salida}!")
    else:
        print("\n❌ No se pudo extraer información de Snopes.")


if __name__ == "__main__":
    main()
