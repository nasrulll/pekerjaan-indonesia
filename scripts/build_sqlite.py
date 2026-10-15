#!/usr/bin/env python3
"""Build a searchable local SQLite catalog; requires Python standard library only."""
import argparse
import json
import sqlite3
from pathlib import Path
from validate import ROOT, read_csv, check


def build(db_path:Path,root=ROOT):
    errors,stats=check(root)
    if errors: raise ValueError('Dataset invalid:\n'+'\n'.join(errors))
    db_path.parent.mkdir(parents=True,exist_ok=True)
    if db_path.exists(): db_path.unlink()
    con=sqlite3.connect(db_path)
    try:
        con.execute('PRAGMA foreign_keys = ON')
        con.executescript('''
        CREATE TABLE sectors(sector_id TEXT PRIMARY KEY, sector_name TEXT NOT NULL, sector_type TEXT NOT NULL, official_kbli_code TEXT);
        CREATE TABLE sources(source_id TEXT PRIMARY KEY, title TEXT NOT NULL, publisher TEXT NOT NULL, edition TEXT, uri TEXT, kind TEXT NOT NULL, license_note TEXT);
        CREATE TABLE occupations(occupation_id TEXT PRIMARY KEY, preferred_name_id TEXT NOT NULL UNIQUE, alternative_names TEXT, sector_id TEXT NOT NULL REFERENCES sectors(sector_id), description_id TEXT, source_id TEXT NOT NULL REFERENCES sources(source_id), record_status TEXT NOT NULL, last_reviewed TEXT);
        CREATE TABLE kbji_mappings(occupation_id TEXT NOT NULL REFERENCES occupations(occupation_id), kbji_edition TEXT NOT NULL, kbji_code TEXT NOT NULL, kbji_label_id TEXT NOT NULL, source_id TEXT NOT NULL REFERENCES sources(source_id), verified_by TEXT NOT NULL, verified_at TEXT NOT NULL, PRIMARY KEY(occupation_id,kbji_edition,kbji_code));
        CREATE TABLE employment_contexts(context_code TEXT PRIMARY KEY,label_id TEXT NOT NULL,dimension TEXT NOT NULL);
        CREATE TABLE job_titles(title_id TEXT PRIMARY KEY,title_name_id TEXT NOT NULL,occupation_id TEXT NOT NULL REFERENCES occupations(occupation_id),seniority_level TEXT,context_code TEXT REFERENCES employment_contexts(context_code),notes TEXT);
        CREATE INDEX ix_occupation_sector ON occupations(sector_id);
        CREATE INDEX ix_kbji_mapping_code ON kbji_mappings(kbji_edition,kbji_code);
        ''')
        tables=[
          ('sectors',root/'data/reference/sectors.csv'),
          ('sources',root/'data/sources.csv'),
          ('occupations',root/'data/occupations.csv'),
          ('employment_contexts',root/'data/reference/employment_contexts.csv'),
          ('job_titles',root/'data/job_titles.csv'),
          ('kbji_mappings',root/'data/kbji_mappings.csv'),
        ]
        for table,file in tables:
            rows=read_csv(file)
            if not rows: continue
            cols=list(rows[0])
            placeholders=','.join('?' for _ in cols)
            con.executemany(f'INSERT INTO {table} ({",".join(cols)}) VALUES ({placeholders})',[[r[c] for c in cols] for r in rows])
        # FTS is optional in some SQLite builds; fallback to LIKE in search.py.
        try:
            con.executescript('''
            CREATE VIRTUAL TABLE occupations_fts USING fts5(preferred_name_id,alternative_names,content=occupations,content_rowid=rowid);
            INSERT INTO occupations_fts(occupations_fts) VALUES('rebuild');
            ''')
        except sqlite3.OperationalError:
            pass
        con.commit()
    finally:
        con.close()
    return stats


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,default=ROOT/'dist/pekerjaan-indonesia.sqlite3')
    args=p.parse_args()
    stats=build(args.output)
    print(json.dumps({'database':str(args.output),**stats},ensure_ascii=False))

if __name__=='__main__':main()
