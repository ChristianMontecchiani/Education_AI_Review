import requests
import csv
import time

BASE_URL = "https://api.elsevier.com/content/search/scopus"
API_KEY = ""


def search_scopus(query, total_results=3000, batch_size=25):
    all_papers = []
    start = 0

    headers = {
        "X-ELS-APIKey": API_KEY,
        "Accept": "application/json"
    }

    while start < total_results:
        print(f"Fetching results {start} to {start + batch_size}")

        params = {
            "query": query,
            "count": batch_size,
            "start": start
        }

        try:
            response = requests.get(BASE_URL, headers=headers, params=params, timeout=60)
            response.raise_for_status()

            data = response.json()
            items = data.get("search-results", {}).get("entry", [])

            if not items:
                print("No more results.")
                break

            papers = parse_scopus(items)
            all_papers.extend(papers)

            start += batch_size
            time.sleep(1)

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            break

    return all_papers


def parse_scopus(items):
    papers = []

    for item in items:
        try:
            title = item.get("dc:title", "")
            abstract = item.get("dc:description", "")  # spesso vuoto senza accesso istituzionale
            authors = item.get("dc:creator", "")
            published = item.get("prism:coverDate", "")
            journal = item.get("prism:publicationName", "")
            doi = item.get("prism:doi", "")
            link = item.get("prism:url", "")

            papers.append({
                "title": title,
                "summary": abstract,
                "published": published,
                "authors": authors,
                "journal": journal,
                "doi": doi,
                "link": link
            })

        except Exception as e:
            print(f"Skipping entry: {e}")

    return papers


def save_to_csv(papers, filename="scopus_results.csv"):
    if not papers:
        print("No papers to save.")
        return

    keys = papers[0].keys()

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(papers)


if __name__ == "__main__":
    
    query = (
       'TITLE ( ( "artificial intelligence education tool*" OR chatbot* OR "intelligent tutoring system*" OR "personal tutor*" OR "intelligent agent*" OR "expert system*" ) AND ( literacy OR education OR "K-12" OR school* OR teach* ) )'
    )


    papers = search_scopus(
        query,
        total_results=3000,   # attenzione ai limiti API
        batch_size=25         # Scopus tipicamente max 25
    )

    print(f"Retrieved {len(papers)} papers")
    save_to_csv(papers)

    print("Done.")  