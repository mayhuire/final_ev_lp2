# scrapers/snopes_scraper.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

BASE = "https://www.snopes.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def get_article_links():
    url = BASE + "/fact-check/"
    resp = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")
    # Selector típico: los artículos están en <a> dentro de un <article>
    links = []
    for article in soup.select("article a.title"):  # AJUSTAR según inspección
        href = article.get("href")
        if href:
            links.append(href)
    # Solo tomamos los primeros 10 para no saturar
    return links[:10]

def extract_detail(link):
    resp = requests.get(link, headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")
    # claim
    claim = soup.select_one("div.claim")
    claim_text = claim.text.strip() if claim else ""
    # rating
    rating = soup.select_one("span.rating-name")
    rating_text = rating.text.strip() if rating else ""
    # date
    date = soup.select_one("time.entry-date")
    date_text = date.get("datetime") if date else ""
    # origin domain (suele ser un enlace con clase "external-link")
    origin = soup.select_one("a.external-link")
    origin_url = origin.get("href") if origin else ""
    # category (tags)
    category = ""
    tags = soup.select("span.tags a")
    if tags:
        category = ", ".join(tag.text for tag in tags)
    return {
        "claim": claim_text,
        "rating": rating_text,
        "date": date_text,
        "category": category,
        "origin_domain": origin_url
    }

def main():
    all_data = []
    links = get_article_links()
    for i, link in enumerate(links):
        print(f"Raspando {i+1}/{len(links)}: {link}")
        try:
            data = extract_detail(link)
            all_data.append(data)
        except Exception as e:
            print(f"Error en {link}: {e}")
        time.sleep(random.uniform(1, 3))  # Pausa educada
    df = pd.DataFrame(all_data)
    df.to_csv("../data/fact_checks.csv", index=False)
    print(f"Guardados {len(df)} registros.")

if __name__ == "__main__":
    main()