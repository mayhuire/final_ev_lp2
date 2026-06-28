# integration/integrate.py
import pandas as pd
import tldextract
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent          # ruta absoluta de integration/
DATA_DIR = (SCRIPT_DIR.parent / "data").resolve()     # ruta absoluta de data/

FACT_CHECKS_FILE = DATA_DIR / "fact_checks.csv"
SOURCES_FILE = DATA_DIR / "sources.csv"
OUTPUT_FILE = DATA_DIR / "report.csv"

def load_data():
    try:
        facts = pd.read_csv(FACT_CHECKS_FILE)
        sources = pd.read_csv(SOURCES_FILE)
        print(f"Cargados {len(facts)} fact-checks y {len(sources)} fuentes.")
        return facts, sources
    except FileNotFoundError as e:
        print(f"Error: {e}. Asegúrate de ejecutar primero los scrapers.")
        exit(1)

def normalize_domain(url_or_domain):
    if pd.isna(url_or_domain) or url_or_domain == "":
        return None
    ext = tldextract.extract(str(url_or_domain))
    if ext.suffix:
        return f"{ext.domain}.{ext.suffix}".lower()
    else:
        return str(url_or_domain).lower().strip().replace("www.", "")

def main():
    facts, sources = load_data()
    facts["origin_domain_clean"] = facts["origin_domain"].apply(normalize_domain)
    sources["domain_clean"] = sources["domain"].apply(normalize_domain)

    merged = pd.merge(facts, sources, left_on="origin_domain_clean",
                      right_on="domain_clean", how="left", suffixes=("", "_mbfc"))
    merged.drop(columns=["domain_clean"], inplace=True, errors="ignore")

    # Métrica principal
    false_ratings = ["False", "Mostly False"]
    low_cred = ["LOW", "VERY LOW"]
    is_false = merged["rating"].str.upper().isin([r.upper() for r in false_ratings])
    has_domain = merged["origin_domain_clean"].notna()
    is_low = merged["factual_reporting"].str.upper().isin([l.upper() for l in low_cred])

    total_false_with_domain = (is_false & has_domain).sum()
    false_low_cred = (is_false & has_domain & is_low).sum()
    if total_false_with_domain > 0:
        pct = (false_low_cred / total_false_with_domain) * 100
        print(f"\n{false_low_cred} de {total_false_with_domain} bulos falsos "
              f"provienen de fuentes de baja credibilidad ({pct:.1f}%).")
    else:
        print("No se encontraron fact-checks falsos con dominio.")
    
    merged.to_csv(OUTPUT_FILE, index=False)
    print(f"Reporte guardado en {OUTPUT_FILE}")

if __name__ == "__main__":
    main()