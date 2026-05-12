import requests
import xml.etree.ElementTree as ET
import csv
import time
from datetime import datetime


BASE_URL = "https://export.arxiv.org/api/query"
HEADERS = {"User-Agent": "arxiv-python-client/1.0"}


def search_arxiv_paginated(query, total_results=1000, batch_size=100):
    all_papers = []

    for start in range(0, total_results, batch_size):
        print(f"Fetching results {start} - {start + batch_size}")

        params = {
            "search_query": query,
            "start": start,
            "max_results": batch_size
        }

        try:
            response = requests.get(
                BASE_URL,
                params=params,
                headers=HEADERS,
                timeout=60
            )
            response.raise_for_status()

            papers = parse_arxiv_response(response.text)

            if not papers:
                print("No more results found.")
                break

            all_papers.extend(papers)

            # Rate limiting (fondamentale)
            time.sleep(3)

        except requests.exceptions.RequestException as e:
            print(f"Request failed at start={start}: {e}")
            break

    return all_papers


def parse_arxiv_response(xml_data):
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_data)

    papers = []

    for entry in root.findall("atom:entry", ns):
        try:
            title = entry.find("atom:title", ns).text.strip()
            summary = entry.find("atom:summary", ns).text.strip()
            published = entry.find("atom:published", ns).text

            authors = [
                author.find("atom:name", ns).text
                for author in entry.findall("atom:author", ns)
            ]

            link = entry.find("atom:id", ns).text

            papers.append({
                "title": title,
                "summary": summary,
                "published": published,
                "authors": ", ".join(authors),
                "link": link
            })

        except Exception as e:
            print(f"Skipping malformed entry: {e}")
            continue

    return papers


def save_to_csv(papers, filename="arxiv_results.csv"):
    if not papers:
        print("No papers to save.")
        return

    keys = papers[0].keys()

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(papers)


if __name__ == "__main__":
    query = '( \
    ti: ("artificial intelligence" OR "intelligent support" OR "AI" OR "ML" OR "chatbot*" OR "machine learning" OR "intelligent tutoring system*" OR "personal tutor*" OR "intelligent agent*" OR "expert system*" OR "AI tools" OR "AI literacy" OR "AI * education") \
    )  \
    AND (\
    ti:("K-12" OR "primary school*" OR "middle school*" OR "elementary school*" OR "education" OR "teach*") \
    ) \
    \
    AND ( \
    abs: ("learn*" OR "student*")\
    )'

    print(f"Searching arXiv for: {query}")

  
    papers = search_arxiv_paginated(
        query,
        total_results=5000,   # aumenta gradualmente
        batch_size=100        # safe
    )

    print(f"Retrieved {len(papers)} papers")
    save_to_csv(papers)

    print("Done.")