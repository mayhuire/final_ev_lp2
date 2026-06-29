import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from pathlib import Path
from fake_useragent import UserAgent

# Configuración básica
BASE_URL = "https://www.snopes.com"

# Generador de identidades (User-Agents) automáticas para burlar la seguridad
ua = UserAgent()

# Ruta de la carpeta y archivo CSV de salida
DATA_DIR = Path(r"C:\Nueva carpeta\Juan\Trabajo Lp2\Nueva carpeta (2)")
DATA_DIR.mkdir(exist_ok=True)
archivo_salida = DATA_DIR / "fact_checks.csv"

def obtener_enlaces_articulos(ruta_seccion, paginas=1):
    """
    Entra a una sección del listado, simula un navegador humano y
    extrae todas las URLs válidas de los artículos.
    """
    enlaces = []
    headers = {
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
        "Referer": "https://www.google.com/"
    }
    
    for num_pag in range(1, paginas + 1):
        url = f"{BASE_URL}{ruta_seccion}page/{num_pag}/" if num_pag > 1 else f"{BASE_URL}{ruta_seccion}"
        print(f"Explorando listado: {url}")
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            
            if resp.status_code == 403:
                print("⚠️ Alerta: El servidor sospecha de nosotros. Cambiando de identidad...")
                headers["User-Agent"] = ua.random
                time.sleep(5)
                continue
                
            if resp.status_code != 200:
                print(f"Error {resp.status_code} al cargar {url}")
                continue
                
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Buscamos de forma masiva todos los links de la página
            links_encontrados = soup.find_all("a", href=True)
            for link in links_encontrados:
                href = link["href"]
                # Filtramos para quedarnos solo con enlaces de artículos reales de fact-check
                if "/fact-check/" in href and not "/page/" in href and len(href) > 13:
                    if href.startswith("/"):
                        enlaces.append(href)
                    elif href.startswith(BASE_URL):
                        enlaces.append(href.replace(BASE_URL, ""))
                        
            time.sleep(random.uniform(3, 5)) # Pausa prudente entre páginas
        except Exception as e:
            print(f"Error al obtener listado página {num_pag}: {e}")
            
    # Quitamos duplicados manteniendo el orden original
    enlaces = list(dict.fromkeys(enlaces))
    print(f"-> Enlaces totales encontrados en {ruta_seccion}: {len(enlaces)}")
    return enlaces


def extraer_detalle_articulo(url_relativa):
    """
    Visita la URL de UN artículo específico y extrae de forma segura:
    claim, rating, date, category, origin_domain y la url original.
    """
    url_completa = BASE_URL + url_relativa if url_relativa.startswith("/") else url_relativa
    print(f"  [Analizando] -> {url_completa}")
    
    headers = {
        "User-Agent": ua.random,
        "Referer": BASE_URL + "/"
    }
    
    try:
        resp = requests.get(url_completa, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"  ❌ Error {resp.status_code} al entrar al artículo.")
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"  ❌ Error de conexión en {url_completa}: {e}")
        return None

    # Diccionario donde guardaremos los campos requeridos
    datos = {"url": url_completa}

    # 1. --- CLAIM (La afirmación que se investiga) ---
    claim_tag = soup.select_one("div.claim-content p, div.claim-text, .claim-content")
    datos["claim"] = claim_tag.text.strip() if claim_tag else "N/A"

    # 2. --- RATING (El veredicto: Verdadero, Falso, etc.) ---
    rating_tag = soup.select_one("span.rating-name, title, h1")
    # Nota: Si no encuentra la etiqueta exacta del veredicto, muchas veces el rating viene en el título
    datos["rating"] = rating_tag.text.strip() if rating_tag else "N/A"

    # 3. --- DATE (Fecha de publicación) ---
    date_tag = soup.select_one("time.entry-date, [datetime], span.date")
    if date_tag and date_tag.has_attr('datetime'):
        datos["date"] = date_tag['datetime']
    elif date_tag:
        datos["date"] = date_tag.text.strip()
    else:
        datos["date"] = "N/A"

    # 4. --- CATEGORY (Categorías / Etiquetas) ---
    tags = soup.select("span.tags a, a.category, li.breadcrumb-item a, .concept-tags a")
    datos["category"] = ", ".join(tag.text.strip() for tag in tags) if tags else "N/A"

    # 5. --- ORIGIN_DOMAIN (De dónde salió el rumor / Fuentes externas) ---
    origin_tag = soup.select_one("a.external-link, p.source a, div.sources a")
    datos["origin_domain"] = origin_tag.get("href", "N/A") if origin_tag else "N/A"

    # Pausa humana aleatoria para evitar que bloqueen la IP a mitad del proceso
    time.sleep(random.uniform(2, 4))
    return datos


def main():
    print("=== INICIANDO SCRAPER DE DETALLES ===")
    
    # Secciones/Links que vas a escanear (puedes añadir o quitar rutas aquí)
    secciones_a_rastrear = [
        "/fact-check/"
    ]
    
    resultados_totales = []
    
    for seccion in secciones_a_rastrear:
        print(f"\n--- Fase 1: Recolectando enlaces de la sección {seccion} ---")
        # Cambia paginas=1 por 2 o más si necesitas recolectar más artículos de golpe
        enlaces = obtener_enlaces_articulos(ruta_seccion=seccion, paginas=1) 
        
        if not enlaces:
            print(f"No se encontraron enlaces en {seccion}. Pasando a la siguiente...")
            continue
            
        print(f"\n--- Fase 2: Visitando cada artículo uno por uno ({len(enlaces)} en total) ---")
        for i, enlace in enumerate(enlaces):
            print(f"Progreso: {i+1}/{len(enlaces)}")
            
            # Ejecutamos la función que extrae los 5 campos que te piden
            datos_articulo = extraer_detalle_articulo(enlace)
            
            if datos_articulo:
                resultados_totales.append(datos_articulo)

    # Fase 3: Guardar los resultados recopilados en el archivo CSV
    if resultados_totales:
        df = pd.DataFrame(resultados_totales)
        # Reordenamos las columnas para asegurarnos de que cumpla con el orden de tu entrega
        columnas_ordenadas = ["claim", "rating", "date", "category", "origin_domain", "url"]
        df = df.reindex(columns=columnas_ordenadas)
        
        # utf-8-sig permite que Excel abra el CSV reconociendo perfectamente las tildes y caracteres especiales
        df.to_csv(archivo_salida, index=False, encoding="utf-8-sig")
        print(f"\n🎉 ¡Proceso Terminado! Guardados {len(df)} artículos con todos sus detalles en:\n--> {archivo_salida}")
    else:
        print("\n❌ No se pudo extraer información detallada de ningún artículo.")


if __name__ == "__main__":
    main()