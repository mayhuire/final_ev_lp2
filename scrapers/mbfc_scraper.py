# ==========================================
# Scraper de Media Bias Fact Check (MBFC)
# Obtiene información sobre el sesgo político
# y el nivel de factualidad de distintos medios
# para su posterior integración con los fact-checks.
# ==========================================
# scrapers/mbfc_scraper.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from pathlib import Path
from urllib.parse import urljoin
import re
import tldextract

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def find_source_links(page_url):
    """Encuentra enlaces a fichas de fuentes reales."""
    resp = requests.get(page_url, headers=HEADERS)
    if resp.status_code != 200:
        return []
    
    soup = BeautifulSoup(resp.text, "html.parser")
    links = set()
    
    keywords = ["bias-and-credibility", "bias-and-reliability", "-bias-", "-news-"]
    
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(page_url, href)
        if "mediabiasfactcheck.com" in full_url:
            if any(kw in full_url for kw in keywords):
                links.add(full_url)
            else:
                text = a.get_text().strip()
                if text and len(text) > 3 and not any(x in full_url for x in ["category", "page", "about", "2026", "2025"]):
                    path = full_url.split("/")[-2] if full_url.endswith("/") else full_url.split("/")[-1]
                    if path and not path.isdigit() and len(path) > 3:
                        links.add(full_url)
    
    return list(links)

def clean_domain(url):
    """Limpia una URL para quedarse solo con el dominio principal."""
    if not url:
        return ""
    # Quitar protocolo y www
    url = re.sub(r'https?://(www\.)?', '', url)
    # Quitar path, query, fragment
    url = url.split('/')[0]
    return url.lower()

def extract_source_detail(source_url):
    """Extrae domain, bias y factual_reporting de una ficha."""
    resp = requests.get(source_url, headers=HEADERS)
    if resp.status_code != 200:
        return {"domain": "", "bias": "", "factual_reporting": ""}
    
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # DOMINIO
    domain = ""
    social = ["facebook", "twitter", "instagram", "youtube", "linkedin", "reddit", "tiktok", 
              "snapchat", "pinterest", "wikipedia", "whois", "donorbox", "pressprogress", "poynter"]
    
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text().strip().lower()
        if ("source" in text or "website" in text) and "http" in href:
            if "mediabiasfactcheck" not in href:
                domain = href
                break
    
    if not domain:
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href and "http" in href and "mediabiasfactcheck" not in href:
                if not any(s in href for s in social):
                    domain = href
                    break
    
    domain = clean_domain(domain)
    
        # BIAS - buscar valor real en el texto
    bias = ""
    text = soup.get_text()
    if "Bias:" in text:
        idx = text.find("Bias:") + 5
        bias = text[idx:].strip().split("\n")[0].strip()
        # Limpiar
        bias = bias.split("How we rate")[0].strip()
        bias = re.sub(r'\s*\(.*?\)', '', bias).strip()
        # Si aún es muy largo, buscar palabras clave
        if len(bias) > 30:
            for word in ["Left Center", "Right Center", "Left", "Right", "Center", 
                        "Conspiracy", "Questionable", "Satire", "Pro-Science", 
                        "Pseudoscience", "Fake News", "Extreme Left", "Extreme Right"]:
                if word.lower() in bias.lower():
                    bias = word
                    break
            else:
                bias = bias[:30]  # Truncar si no coincide
    
    # FACTUAL REPORTING
    factual = ""
    fact_section = soup.find(string=re.compile(r"Factual Reporting:", re.IGNORECASE))
    if fact_section:
        parent = fact_section.parent
        if parent:
            full_text = parent.get_text()
            if "Factual Reporting:" in full_text:
                parts = full_text.split("Factual Reporting:")[-1].strip()
                factual = parts.split("\n")[0].strip()
                if len(factual) > 30:
                    for word in ["HIGH", "MOSTLY FACTUAL", "MIXED", "LOW", "VERY LOW"]:
                        if word.lower() in factual.lower():
                            factual = word
                            break
    
    # Limpiar bias y factual de números entre paréntesis
    bias = re.sub(r'\s*\(.*?\)', '', bias).strip()
    factual = re.sub(r'\s*\(.*?\)', '', factual).strip()
    
    return {
        "domain": domain,
        "bias": bias,
        "factual_reporting": factual
    }

def main():
    start_urls = [
        "https://mediabiasfactcheck.com/left/",
        "https://mediabiasfactcheck.com/right/",
        "https://mediabiasfactcheck.com/center/",
        "https://mediabiasfactcheck.com/conspiracy/",
        "https://mediabiasfactcheck.com/fake-news/",
        "https://mediabiasfactcheck.com/pro-science/",
    ]
    
    all_links = []
    for url in start_urls:
        links = find_source_links(url)
        all_links.extend(links)
    
    all_links = list(set(all_links))[:40]  # 40 máximo
    
    all_sources = []
    for i, url in enumerate(all_links):
        print(f"\n[{i+1}/{len(all_links)}] {url}")
        try:
            data = extract_source_detail(url)
            if data["domain"]:
                all_sources.append(data)
                print(f"  ✅ {data['domain']} | Bias: {data['bias']} | Factual: {data['factual_reporting']}")
            else:
                print(f"  ⚠️ Sin dominio")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        time.sleep(random.uniform(1, 2))
    
    if all_sources:
        df = pd.DataFrame(all_sources)
        df = df.drop_duplicates(subset=["domain"])
        df = df[df["domain"] != ""]
        df.to_csv(DATA_DIR / "sources.csv", index=False, encoding="utf-8")
        print(f"\n🎉 ¡Listo! {len(df)} fuentes guardadas en data/sources.csv")
        print("📋 Muestra:")
        print(df.to_string())
    else:
        print("\n❌ No se encontraron fuentes.")
        
# Punto de inicio del programa.
if __name__ == "__main__":
    main()
