#!/usr/bin/env python3
from pathlib import Path
import re
import csv

BASE_DIR = Path(__file__).resolve().parent
TXT = BASE_DIR / "results" / "acm.txt"
OUT = BASE_DIR / "results" / "acm.csv"

def parse_line(line: str) -> dict:
    doi_match = re.search(r'https?://doi\.org/\S+', line)
    doi = doi_match.group(0) if doi_match else ""

    year_match = re.search(r"\b(19|20)\d{2}\b", line)
    year = year_match.group(0) if year_match else ""

    authors = ""
    title = ""
    venue = ""
    pages = ""

    if year:
        parts = line.split(year, 1)
        authors = parts[0].strip().rstrip('. ')
        rest = parts[1].strip()
        # title is typically before the first ". In " (e.g. "Title. In Proceedings...")
        m = re.search(r"\.\s*In\s", rest)
        if m:
            title = rest[:m.start()].strip().lstrip('. ').rstrip()
            venue = rest[m.end():].strip()
        else:
            # fallback: up to DOI or end
            if doi:
                title = rest.split(doi)[0].strip().strip('. ')
            else:
                title = rest.strip().strip('. ')

    page_match = re.search(r"(\d{1,4}[–-]\d{1,4})", line)
    if page_match:
        pages = page_match.group(1)

    if venue:
        venue = re.sub(r'https?://doi\.org/\S+', '', venue)
        venue = re.sub(r"\b\d{1,4}[–-]\d{1,4}\b", '', venue)
        venue = venue.strip().strip('.,')

    return {
        'authors': authors,
        'year': year,
        'title': title,
        'venue': venue,
        'pages': pages,
        'doi': doi,
        'raw': line,
    }

def main():
    text = TXT.read_text(encoding='utf-8') if TXT.exists() else ''
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    rows = [parse_line(l) for l in lines]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ['authors', 'year', 'title', 'venue', 'pages', 'doi', 'raw']
    with OUT.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f'Wrote {len(rows)} records to {OUT}')

if __name__ == '__main__':
    main()
