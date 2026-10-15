#!/usr/bin/env python3
"""Validate core catalog and any explicitly verified KBJI crosswalks."""
import argparse
import csv
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ID_RE = re.compile(r'^ID-OCC-\d{6}$')
SECTOR_RE = re.compile(r'^SEC-\d{3}$')
CODE_RE = re.compile(r'^\d{1,8}$')  # String: preserve leading zero; confirm actual code length with source edition.


def read_csv(file):
    with file.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def nfc(value):
    return unicodedata.normalize('NFKC', value.strip()).casefold()


def check(root=ROOT):
    errors=[]
    data=root/'data'
    try:
        occ=read_csv(data/'occupations.csv')
        sectors=read_csv(data/'reference/sectors.csv')
        sources=read_csv(data/'sources.csv')
        mappings=read_csv(data/'kbji_mappings.csv')
        groups=read_csv(data/'reference/kbji_major_groups.csv')
        contexts=read_csv(data/'reference/employment_contexts.csv')
        titles=read_csv(data/'job_titles.csv')
    except (OSError, UnicodeError, csv.Error) as exc:
        return [f'Cannot load data: {exc}'], {}
    sector_ids={x['sector_id'] for x in sectors}
    source_ids={x['source_id'] for x in sources}
    context_ids={x['context_code'] for x in contexts}
    ids=set(); names=set(); mappings_seen=set()
    if len(sector_ids)!=len(sectors): errors.append('Duplicate sector_id')
    if len(source_ids)!=len(sources): errors.append('Duplicate source_id')
    if len(context_ids)!=len(contexts): errors.append('Duplicate employment context')
    if {str(x['major_group_code']) for x in groups} != set('0123456789'):
        errors.append('Reference KBJI major groups must have 0 through 9')
    for i,row in enumerate(occ,2):
        jobid=row['occupation_id'].strip()
        name=row['preferred_name_id'].strip()
        if not ID_RE.fullmatch(jobid): errors.append(f'occupations:{i}: invalid id {jobid!r}')
        if jobid in ids: errors.append(f'occupations:{i}: duplicate id {jobid}')
        ids.add(jobid)
        if not name: errors.append(f'occupations:{i}: missing name')
        if nfc(name) in names: errors.append(f'occupations:{i}: duplicate canonical name {name}')
        names.add(nfc(name))
        if row['sector_id'] not in sector_ids: errors.append(f'occupations:{i}: unknown sector')
        if row['source_id'] not in source_ids: errors.append(f'occupations:{i}: unknown source')
        if row['record_status'] not in ('draft','reviewed','published','archived'):
            errors.append(f'occupations:{i}: unknown record status')
        if row['last_reviewed']:
            try: date.fromisoformat(row['last_reviewed'])
            except ValueError: errors.append(f'occupations:{i}: invalid last_reviewed date')
    for i,row in enumerate(mappings,2):
        key=(row['occupation_id'],row['kbji_edition'],row['kbji_code'])
        if key in mappings_seen: errors.append(f'kbji_mappings:{i}: duplicate mapping')
        mappings_seen.add(key)
        if row['occupation_id'] not in ids: errors.append(f'kbji_mappings:{i}: missing occupation')
        if not CODE_RE.fullmatch(row['kbji_code']): errors.append(f'kbji_mappings:{i}: nonnumeric KBJI code')
        if not row['kbji_edition']: errors.append(f'kbji_mappings:{i}: edition required')
        if not row['kbji_label_id']: errors.append(f'kbji_mappings:{i}: source label required')
        if row['source_id'] not in source_ids: errors.append(f'kbji_mappings:{i}: unregistered source')
        if not row['verified_by']: errors.append(f'kbji_mappings:{i}: verification author required')
        try: date.fromisoformat(row['verified_at'])
        except ValueError: errors.append(f'kbji_mappings:{i}: verified_at must be YYYY-MM-DD')
    title_ids=set()
    for i,row in enumerate(titles,2):
        if not row['title_id'] or row['title_id'] in title_ids: errors.append(f'job_titles:{i}: duplicate or missing id')
        title_ids.add(row['title_id'])
        if row['occupation_id'] not in ids: errors.append(f'job_titles:{i}: unknown occupation')
        if row['context_code'] and row['context_code'] not in context_ids: errors.append(f'job_titles:{i}: unknown context')
    from validasi_pengembangan import validasi
    tambahan, statistik_tambahan = validasi(root, read_csv)
    errors.extend(tambahan)
    stats={'occupations':len(occ),'sectors':len(sectors),'major_groups':len(groups),'kbji_mappings':len(mappings),'job_titles':len(titles)}
    stats.update(statistik_tambahan)
    return errors, stats


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,default=ROOT)
    args=p.parse_args()
    errors,stats=check(args.root)
    if errors:
        print('VALIDATION FAILED:')
        for e in errors: print(' -',e)
        return 1
    print('VALIDATION OK:',', '.join(f'{key}={val}' for key,val in stats.items()))
    return 0


if __name__=='__main__':
    sys.exit(main())
