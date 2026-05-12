import requests
import csv
import time

BASE_URL = "https://api.openalex.org/works"


def search_openalex(query, total_results=1000, batch_size=100):
    all_papers = []

    for page in range(1, total_results // batch_size + 2):
        print(f"Fetching page {page}")

        params = {
            "search": query,
            "per-page": batch_size,
            "page": page
        }

        try:
            response = requests.get(BASE_URL, params=params, timeout=60)
            response.raise_for_status()

            data = response.json()
            items = data.get("results", [])

            if not items:
                print("No more results.")
                break

            papers = parse_openalex(items)
            all_papers.extend(papers)

            time.sleep(1)

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            break

    return all_papers


def parse_openalex(items):
    papers = []

    for item in items:
        try:
            title = item.get("title", "")
            abstract = item.get("abstract_inverted_index", "")

            # convert abstract inverted index → text
            abstract_text = ""
            if abstract:
                words = []
                for word, positions in abstract.items():
                    for pos in positions:
                        words.append((pos, word))
                words.sort()
                abstract_text = " ".join([w for _, w in words])

            authors = []
            for auth in item.get("authorships", []):
                name = auth.get("author", {}).get("display_name", "")
                authors.append(name)

            published = item.get("publication_year", "")
            link = item.get("id", "")

            papers.append({
                "title": title,
                "summary": abstract_text,
                "published": published,
                "authors": ", ".join(authors),
                "link": link
            })

        except Exception as e:
            print(f"Skipping entry: {e}")

    return papers


def save_to_csv(papers, filename="openalex_results.csv"):
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
        '"artificial intelligence" OR "intelligent support" OR "AI" OR "chatbot" '
        'OR "intelligent tutoring system" OR "personal tutor" OR "intelligent agent" '
        'OR "expert system" OR "AI tools" OR "AI literacy" '
        'AND "K-12" OR school OR education OR teaching'
    )

    papers = search_openalex(
        query,
        total_results=10000,
        batch_size=100
    )

    print(f"Retrieved {len(papers)} papers")
    save_to_csv(papers)

    print("Done.")