# scrapers/mbfc_scraper.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from urllib.parse import urljoin

BASE = "https://mediabiasfactcheck.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def get_source_links():
    url = BASE + "/category/fake-news/"
    resp = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    # Buscar enlaces a los medios (h2.entry-title a)
    for a in soup.select("h2.entry-title a"):
        href = a.get("href")
        if href:
            links.append(href)
    return links[:15]  # primeros 15 medios

def extract_source_detail(link):
    resp = requests.get(link, headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")
    # domain: enlace externo del medio
    domain = ""
    source_link = soup.select_one("a[href*='external']")  # ajustar
    if source_link:
        domain = source_link.get("href")
    # bias y factual reporting suelen estar en una tabla o en spans
    bias = ""
    factual = ""
    bias_tag = soup.find("span", text="Bias:")
    if bias_tag:
        bias = bias_tag.find_next("span").text.strip()
    factual_tag = soup.find("span", text="Factual Reporting:")
    if factual_tag:
        factual = factual_tag.find_next("span").text.strip()
    return {
        "domain": domain,
        "bias": bias,
        "factual_reporting": factual
    }

def main():
    all_sources = []
    links = get_source_links()
    for i, link in enumerate(links):
        print(f"Raspando fuente {i+1}: {link}")
        try:
            data = extract_source_detail(link)
            all_sources.append(data)
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(random.uniform(1, 3))
    df = pd.DataFrame(all_sources)
    df.to_csv("../data/sources.csv", index=False)
    print(f"Guardados {len(df)} registros.")

if __name__ == "__main__":
    main()