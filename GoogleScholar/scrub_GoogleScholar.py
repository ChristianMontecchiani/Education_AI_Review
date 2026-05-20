import requests
import csv
import time

API_KEY = ""
BASE_URL = "https://serpapi.com/search.json"


def search_google_scholar(query, total_results=100, batch_size=10):
    all_papers = []

    for start in range(0, total_results, batch_size):
        print(f"Fetching results {start} to {start + batch_size}")

        params = {
            "engine": "google_scholar",
            "q": query,
            "api_key": API_KEY,
            "start": start
        }

        try:
            response = requests.get(BASE_URL, params=params, timeout=60)
            response.raise_for_status()

            data = response.json()
            results = data.get("organic_results", [])

            if not results:
                print("No more results.")
                break

            papers = parse_scholar(results)
            all_papers.extend(papers)

            time.sleep(1)

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            break

    return all_papers


def parse_scholar(results):
    papers = []

    for item in results:
        try:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            link = item.get("link", "")

            publication_info = item.get("publication_info", {})
            authors = ", ".join([a.get("name", "") for a in publication_info.get("authors", [])])

            year = publication_info.get("summary", "")

            papers.append({
                "title": title,
                "summary": snippet,
                "published": year,
                "authors": authors,
                "link": link
            })

        except Exception as e:
            print(f"Skipping entry: {e}")

    return papers


def save_to_csv(papers, filename="scholar_results.csv"):
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
    ("artificial intelligence" OR "intelligent support" OR "AI" OR "ML" OR "chatbot*" OR "machine learning" OR "intelligent tutoring system*" OR "personal tutor*" OR "intelligent agent*" OR "expert system*" OR "AI tools" OR "AI literacy" OR "AI * education") \
    )  \
    AND (\
    ("K-12" OR "primary school*" OR "middle school*" OR "elementary school*" OR "education" OR "teach*") \
    ) \
    \
    AND ( \
   ("learn*" OR "student*")\
    )'
    )

    papers = search_google_scholar(
        query,
        total_results=3000,
        batch_size=30
    )

    print(f"Retrieved {len(papers)} papers")
    save_to_csv(papers)

    print("Done.")