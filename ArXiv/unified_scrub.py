import requests
import csv
import time
import re
from difflib import SequenceMatcher

# -----------------------------
# CONFIG
# -----------------------------
CROSSREF_URL = "https://api.crossref.org/works"
OPENALEX_URL = "https://api.openalex.org/works"
SEMANTIC_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

BATCH_SIZE = 100
TOTAL_RESULTS = 500


# -----------------------------
# UTILS
# -----------------------------
def normalize_title(title):
    if not title:
        return ""
    title = title.lower()
    title = re.sub(r'\W+', ' ', title)
    return title.strip()


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


# -----------------------------
# CROSSREF
# -----------------------------
def fetch_crossref(query):
    papers = []

    for offset in range(0, TOTAL_RESULTS, BATCH_SIZE):
        print(f"[Crossref] {offset}")

        params = {
            "query.title": query,
            "rows": BATCH_SIZE,
            "offset": offset
        }

        r = requests.get(CROSSREF_URL, params=params, timeout=60)
        r.raise_for_status()

        items = r.json().get("message", {}).get("items", [])

        if not items:
            break

        for item in items:
            title = item.get("title", [""])[0]
            doi = item.get("DOI", "")
            url = item.get("URL", "")

            authors = [
                f"{a.get('given','')} {a.get('family','')}"
                for a in item.get("author", [])
            ]

            papers.append({
                "title": title,
                "doi": doi.lower(),
                "authors": ", ".join(authors),
                "year": extract_year(item),
                "source": "crossref",
                "link": url,
                "citations": None
            })

        time.sleep(1)

    return papers


def extract_year(item):
    for key in ["published-print", "published-online", "created"]:
        if key in item:
            parts = item[key].get("date-parts", [[]])
            if parts and parts[0]:
                return parts[0][0]
    return ""


# -----------------------------
# OPENALEX
# -----------------------------
def fetch_openalex(query):
    papers = []
    BATCH_SIZE = 20
    for page in range(1, TOTAL_RESULTS // BATCH_SIZE + 2):
        print(f"[OpenAlex] page {page}")

        params = {
            "search": query,
            "per-page": BATCH_SIZE,
            "page": page
        }

        r = requests.get(OPENALEX_URL, params=params, timeout=60)
        
        r.raise_for_status()

        items = r.json().get("results", [])

        if not items:
            break

        for item in items:
            title = item.get("title", "")
            doi = (item.get("doi") or "").replace("https://doi.org/", "")

            authors = [
                a.get("author", {}).get("display_name", "")
                for a in item.get("authorships", [])
            ]

            papers.append({
                "title": title,
                "doi": doi.lower(),
                "authors": ", ".join(authors),
                "year": item.get("publication_year", ""),
                "source": "openalex",
                "link": item.get("id", ""),
                "citations": item.get("cited_by_count", 0)
            })

        time.sleep(5)

    return papers


# -----------------------------
# SEMANTIC SCHOLAR
# -----------------------------
def fetch_semantic_scholar(query):
    papers = []

    offset = 0

    while offset < TOTAL_RESULTS:
        print(f"[SemanticScholar] {offset}")

        params = {
            "query": query,
            "limit": BATCH_SIZE,
            "offset": offset,
            "fields": "title,authors,year,externalIds,url,citationCount"
        }

        r = requests.get(SEMANTIC_URL, params=params, timeout=60)
        r.raise_for_status()

        items = r.json().get("data", [])

        if not items:
            break

        for item in items:
            doi = ""
            if "externalIds" in item and item["externalIds"]:
                doi = item["externalIds"].get("DOI", "")

            authors = [
                a.get("name", "")
                for a in item.get("authors", [])
            ]

            papers.append({
                "title": item.get("title", ""),
                "doi": doi.lower(),
                "authors": ", ".join(authors),
                "year": item.get("year", ""),
                "source": "semantic_scholar",
                "link": item.get("url", ""),
                "citations": item.get("citationCount", 0)
            })

        offset += BATCH_SIZE
        time.sleep(1)

    return papers


# -----------------------------
# DEDUPLICATION
# -----------------------------
def deduplicate(papers):
    unique = []
    seen_doi = set()

    for p in papers:
        title_norm = normalize_title(p["title"])

        # DOI match
        if p["doi"] and p["doi"] in seen_doi:
            continue

        duplicate = False

        for u in unique:
            sim = similar(title_norm, normalize_title(u["title"]))
            if sim > 0.9:
                duplicate = True
                break

        if not duplicate:
            unique.append(p)
            if p["doi"]:
                seen_doi.add(p["doi"])

    return unique


# -----------------------------
# SAVE
# -----------------------------
def save_csv(papers, filename="CrossRef_results.csv"):
    if not papers:
        return

    keys = papers[0].keys()

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(papers)


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":

    query = '( \
    "artificial intelligence" OR "intelligent support" OR "AI" OR "ML" OR "chatbot*" OR "machine learning" OR "intelligent tutoring system*" OR "personal tutor*" OR "intelligent agent*" OR "expert system*" OR "AI tools" OR "AI literacy" OR "AI * education" \
    )  \
    AND (\
    "K-12" OR "primary school*" OR "middle school*" OR "elementary school*" OR "education" OR "teach*" \
    ) \
    \
    AND ( \
    "learn*" OR "student*"\
    )'


    print("Fetching Crossref...")
    crossref_papers = fetch_crossref(query)

    query = '( \
    ("artificial intelligence" OR "intelligent support" OR "AI" OR "ML" OR chatbot OR "machine learning" OR intelligent tutoring system OR personal tutor OR intelligent agent OR expert system OR "AI tools" OR "AI literacy" OR education) \
    )  \
    AND (\
    ("K-12" OR primary school OR middle school OR elementary school OR education OR teach) \
    ) \
    \
    AND ( \
    (learn OR student)\
    )'

    query ='(\
    ("artificial intelligence" OR "intelligent support" OR "AI" OR "chatbot*" OR "intelligent agent*" OR "expert system*" OR "AI tools" OR "AI literacy" OR "AI in education"\
    ) \
    AND (\
    ("K-12" OR "primary school*" OR "middle school*" OR "elementary school*" OR "education" OR "teach*" OR "tool*" OR "tutor*") \
    ) \
    AND (\
    ("learn*" OR "student*")\
    )'

    print("Fetching OpenAlex...")
    #openalex_papers = fetch_openalex(query)

    #print("Fetching Semantic Scholar...")
    #semantic_papers = fetch_semantic_scholar(query)

    all_papers = crossref_papers # openalex_papers #+ semantic_papers

    print(f"Total before dedup: {len(all_papers)}")

    deduped = deduplicate(all_papers)

    print(f"Total after dedup: {len(deduped)}")

    save_csv(deduped)

    print("Done.")  