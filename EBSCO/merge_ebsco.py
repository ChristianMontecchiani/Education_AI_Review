#!/usr/bin/env python3
from pathlib import Path
import argparse
import sys
import re

def read_csv_try(path):
    import pandas as pd
    for enc in ("utf-8", "latin1", "cp1252"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return None

def main():
    parser = argparse.ArgumentParser(description='Merge EBSCO metadata CSV files')
    parser.add_argument('--results-dir', '-r', help='EBSCO results directory', default=None)
    parser.add_argument('--pattern', '-p', help='Filename glob pattern', default='EBSCO-Metadata*.csv')
    parser.add_argument('--out', '-o', help='Output csv file', default=None)
    parser.add_argument('--dedup', action='store_true', help='Drop exact duplicate rows')
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    results_dir = Path(args.results_dir) if args.results_dir else base / 'results'
    out_file = Path(args.out) if args.out else results_dir / 'result.csv'

    if not results_dir.exists():
        print(f'Results directory not found: {results_dir}', file=sys.stderr)
        sys.exit(1)

    files = sorted(results_dir.glob(args.pattern))
    if not files:
        print(f'No files matching {args.pattern} in {results_dir}', file=sys.stderr)
        sys.exit(1)

    import pandas as pd
    dfs = []
    for f in files:
        print(f'Reading {f}')
        df = read_csv_try(f)
        if df is None:
            print(f'  Failed to read {f}, skipping', file=sys.stderr)
            continue
        df['__source_file'] = f.name
        dfs.append(df)

    if not dfs:
        print('No readable CSVs found.', file=sys.stderr)
        sys.exit(1)

    combined = pd.concat(dfs, ignore_index=True, sort=False)
    combined.rename(columns={"publicationDate": "published"}, inplace=True)

    # Normalize `published` column formats:  YYYYMMDD -> YYYY-MM-DD
    if 'published' in combined.columns:
        def _fmt_pub(x):
            import pandas as _pd
            if _pd.isna(x):
                return x
            s = str(x).strip()
            m = re.match(r'^(\d{4})(\d{2})(\d{2})$', s)
            if m:
                return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
            m2 = re.match(r'^(\d{4})(\d{2})$', s)
            if m2:
                return f"{m2.group(1)}-{m2.group(2)}-01"
            m3 = re.match(r'^(\d{4})$', s)
            if m3:
                return f"{m3.group(1)}-01-01"
            return s

        combined['published'] = combined['published'].apply(_fmt_pub)


    before = len(combined)
    if args.dedup:
        combined = combined.drop_duplicates()
    after = len(combined)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(out_file, index=False)

    print(f'Wrote {len(combined)} rows to {out_file} (from {len(files)} files, {before-after} duplicates removed)')

if __name__ == '__main__':
    main()
