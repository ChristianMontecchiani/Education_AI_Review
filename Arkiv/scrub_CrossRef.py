import requests
import csv
import time

BASE_URL = "https://api.crossref.org/works"
HEADERS = {"User-Agent": "crossref-python-client/1.0"}


def search_crossref_paginated(query, total_results=3000, batch_size=100):
    all_papers = []

    for offset in range(0, total_results, batch_size):
        print(f"Fetching results {offset} - {offset + batch_size}")

        params = {
            "query": query,
            "rows": batch_size,
            "offset": offset,
        }

        try:
            response = requests.get(
                BASE_URL,
                params=params,
                headers=HEADERS,
                timeout=60
            )
            response.raise_for_status()

            data = response.json()
            items = data.get("message", {}).get("items", [])

            papers = parse_crossref_response(items)

            if not papers:
                print("No more results found.")
                break

            all_papers.extend(papers)

            time.sleep(1.5)  # rate limiting

        except requests.exceptions.RequestException as e:
            print(f"Request failed at offset={offset}: {e}")
            break

    return all_papers


def parse_crossref_response(items):
    papers = []

    for item in items:
        try:
            title = item.get("title", [""])[0]
            abstract = item.get("abstract", "")
            published = ""

            # data pubblicazione (Crossref è annidato)
            if "published-print" in item:
                date_parts = item["published-print"].get("date-parts", [[]])
                published = "-".join(map(str, date_parts[0])) if date_parts[0] else ""
            elif "published-online" in item:
                date_parts = item["published-online"].get("date-parts", [[]])
                published = "-".join(map(str, date_parts[0])) if date_parts[0] else ""

            authors = []
            for author in item.get("author", []):
                given = author.get("given", "")
                family = author.get("family", "")
                authors.append(f"{given} {family}".strip())

            link = item.get("URL", "")

            papers.append({
                "title": title,
                "summary": abstract,
                "published": published,
                "authors": ", ".join(authors),
                "link": link
            })

        except Exception as e:
            print(f"Skipping malformed entry: {e}")
            continue

    return papers


def save_to_csv(papers, filename="crossref_results.csv"):
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
    '( \
    title.search: ("artificial intelligence" OR "intelligent support" OR "AI" OR "ML" OR "chatbot*" OR "machine learning" OR "intelligent tutoring system*" OR "personal tutor*" OR "intelligent agent*" OR "expert system*" OR "AI tools" OR "AI literacy" OR "AI * education") \
    )  \
    AND (\
    title.search:("K-12" OR "primary school*" OR "middle school*" OR "elementary school*" OR "education" OR "teach*") \
    ) \
    \
    AND ( \
    title.search: ("learn*" OR "student*")\
    )'
    )

    print(f"Searching Crossref for: {query}")

    papers = search_crossref_paginated(
        query,
        total_results=9000,
        batch_size=100
    )

    print(f"Retrieved {len(papers)} papers")
    save_to_csv(papers)

    print("Done.")