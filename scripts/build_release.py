#!/usr/bin/env python3
"""Create reproducible local multi-format release assets and checksums."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

from validate import ROOT, check, read_csv
from build_sqlite import build
from export_json import export


def create_release(root: Path = ROOT, output: Path | None = None) -> dict:
    if output is None:
        output = root / 'dist'
    problems, stats = check(root)
    if problems:
        raise ValueError('\n'.join(problems))
    output.mkdir(parents=True, exist_ok=True)
    sqlite = output/'pekerjaan-indonesia.sqlite3'
    json_file = output/'occupations.json'
    csv_file = output/'occupations.csv'
    build(sqlite, root)
    export(root, json_file)
    sectors = {r['sector_id']: r['sector_name']
               for r in read_csv(root/'data/reference/sectors.csv')}
    with csv_file.open('w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(('occupation_id', 'name', 'aliases', 'sector_id', 'sector_name',
                         'record_status', 'source_id'))
        for r in sorted(read_csv(root/'data/occupations.csv'),
                        key=lambda item: item['occupation_id']):
            writer.writerow((r['occupation_id'], r['preferred_name_id'],
                             r['alternative_names'], r['sector_id'],
                             sectors[r['sector_id']], r['record_status'], r['source_id']))
    manifest = {
        'version': '0.2.0',
        'catalog_status': 'curated_draft_not_official',
        'counts': stats,
        'files': {
            f.name: {'sha256': hashlib.sha256(f.read_bytes()).hexdigest(),
                     'size_bytes': f.stat().st_size}
            for f in (sqlite, json_file, csv_file)
        },
        'source_of_truth': 'Git CSV',
    }
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n',
                                         encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    print(json.dumps(create_release(output=args.output), indent=2))
