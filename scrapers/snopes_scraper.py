# scrapers/snopes_scraper.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

BASE = "https://www.snopes.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def get_article_links():
    """Obtiene enlaces a fact‑checks reales (filtra paginación y otras páginas no válidas)."""
    url = BASE + "/fact-check/"
    resp = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")
    links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/fact-check/" in href:
            full = urljoin(url, href)
            # Excluir la propia página de listado, paginación, etc.
            if full == url or full.endswith("/fact-check/"):
                continue
            if "pagenum=" in full:
                continue
            links.add(full)

    links = list(links)[:20]
    print(f"🔗 {len(links)} enlaces encontrados.")
    return links

def extract_detail(link):
    """Extrae datos usando el JSON-LD (ClaimReview) de la página. Muy robusto."""
    resp = requests.get(link, headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")

    # Buscar todos los scripts de tipo application/ld+json
    claim = ""
    rating = ""
    date = ""
    category = ""
    origin_domain = ""

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            # A veces es una lista de objetos
            if isinstance(data, list):
                for item in data:
                    if item.get("@type") == "ClaimReview":
                        data = item
                        break
            # Si encontramos ClaimReview
            if data.get("@type") == "ClaimReview":
                # CLAIM
                claim = data.get("claimReviewed", "")
                # RATING
                review_rating = data.get("reviewRating", {})
                if isinstance(review_rating, dict):
                    rating = review_rating.get("alternateName", "")
                # DATE
                date = data.get("datePublished", "")
                # CATEGORY: a veces en "itemReviewed" o "about"
                item_reviewed = data.get("itemReviewed", {})
                if isinstance(item_reviewed, dict):
                    # Intentar obtener categoría
                    about = item_reviewed.get("about", "")
                    if about:
                        category = about
                    # DOMINIO DE ORIGEN: la URL de la afirmación original suele estar en "appearance" o "url"
                    appearance = item_reviewed.get("appearance", None)
                    if appearance is None:
                        # A veces el "url" es el enlace a la fuente original
                        appearance = item_reviewed.get("url", "")
                    if isinstance(appearance, list):
                        # Tomamos la primera URL de apariencia
                        appearance = appearance[0].get("url", "") if appearance else ""
                    if isinstance(appearance, dict):
                        appearance = appearance.get("url", "")
                    if isinstance(appearance, str) and appearance.startswith("http"):
                        parsed = urlparse(appearance)
                        origin_domain = parsed.netloc.replace("www.", "")
                    else:
                        origin_domain = appearance  # por si ya es un dominio
                break  # Usamos el primer ClaimReview encontrado
        except (json.JSONDecodeError, AttributeError):
            continue

    # Si el JSON-LD no dio rating, intentar con HTML (fallback)
    if not rating:
        rating_tag = soup.select_one("span.rating-name, span.rating")
        if rating_tag:
            rating = rating_tag.get_text(strip=True)

    # Si no hay claim, usar el título de la página
    if not claim:
        title_tag = soup.select_one("h1.entry-title, h1.title")
        if title_tag:
            claim = title_tag.get_text(strip=True)

    # Si no hay fecha, probar con <time>
    if not date:
        time_tag = soup.select_one("time.entry-date")
        if time_tag:
            date = time_tag.get("datetime", time_tag.get_text(strip=True))

    # Si no hay dominio, buscar enlace externo en el HTML como último recurso
    # FALLBACK 1: enlace con clase 'external-link'
    if not origin_domain:
        ext_link = soup.select_one("a.external-link, a[rel*='external']")
        if ext_link:
            parsed = urlparse(ext_link.get("href", ""))
            origin_domain = parsed.netloc.replace("www.", "")

    # FALLBACK 2 (nuevo): recorrer TODOS los párrafos del documento,
    # quedándonos con el primer dominio que no sea un servicio de archivado o newsletter.
    if not origin_domain:
        # Lista de dominios que NO son la fuente original del rumor
        skip_domains = [
            "l.join1440.com", "join1440.com", "feedburner.com", "mailchi.mp",
            "snopes.com", "perma.cc", "archive.is", "web.archive.org",
            "facebook.com", "twitter.com", "instagram.com"  # redes sociales pueden ser fuente, las dejamos fuera del skip si quieres capturarlas; pero como a veces el primer enlace es Instagram, mejor NO las pongas en skip a menos que quieras excluirlas explícitamente.
            # Para el caso de redes sociales, es mejor capturarlas porque son la fuente. Así que comentamos las redes sociales para que sí se capturen.
        ]
        # Nota: si quieres que Instagram sea capturado, no lo incluyas en skip.
        # Dejamos skip solo para sitios claramente no fuente.
        skip_domains = ["l.join1440.com", "join1440.com", "feedburner.com", "mailchi.mp",
                        "snopes.com", "perma.cc", "archive.is", "web.archive.org"]

        for p in soup.find_all("p"):
            a_tag = p.find("a", href=True)
            if a_tag:
                href = a_tag["href"]
                parsed_domain = urlparse(href).netloc.replace("www.", "").lower()
                if parsed_domain and parsed_domain not in skip_domains:
                    origin_domain = parsed_domain
                    break

    # FALLBACK 3: si aún no hay dominio, tomar el primer enlace de toda la página
    if not origin_domain:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            parsed_domain = urlparse(href).netloc.replace("www.", "").lower()
            if parsed_domain and parsed_domain not in skip_domains:
                origin_domain = parsed_domain
                break
    return {
        "claim": claim,
        "rating": rating,
        "date": date,
        "category": category,
        "origin_domain": origin_domain
    }

def main():
    links = get_article_links()
    all_data = []

    for i, link in enumerate(links):
        print(f"[{i+1}/{len(links)}] {link}")
        try:
            data = extract_detail(link)
            if data["claim"]:   # al menos el claim
                all_data.append(data)
                print(f"  ✅ {data['claim'][:60]}... | Rating: {data['rating']} | Dominio: {data['origin_domain']}")
            else:
                print("  ⚠️ No se encontró claim (ni siquiera en JSON-LD)")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        time.sleep(random.uniform(1, 2))

    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv(DATA_DIR / "fact_checks.csv", index=False, encoding="utf-8")
        print(f"\n🎉 {len(df)} fact-checks guardados en data/fact_checks.csv")
    else:
        print("\n❌ No se extrajeron fact-checks. Avisa a Jeremi para revisar manualmente un artículo.")

if __name__ == "__main__":
    main()
