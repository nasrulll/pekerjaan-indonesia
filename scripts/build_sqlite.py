#!/usr/bin/env python3
"""Atomically build a read-only-friendly SQLite snapshot from validated Git CSV."""
import argparse
import json
import os
import sqlite3
import tempfile
from pathlib import Path
from validate import ROOT, read_csv, check


SCHEMA = '''
PRAGMA foreign_keys = ON;
CREATE TABLE sectors(
    sector_id TEXT PRIMARY KEY, sector_name TEXT NOT NULL UNIQUE,
    sector_type TEXT NOT NULL, official_kbli_code TEXT
);
CREATE TABLE data_sources(
    source_id TEXT PRIMARY KEY, title TEXT NOT NULL, publisher TEXT NOT NULL,
    edition TEXT, uri TEXT, kind TEXT NOT NULL, license_note TEXT
);
CREATE TABLE occupations(
    occupation_id TEXT PRIMARY KEY, preferred_name_id TEXT NOT NULL,
    alternative_names TEXT NOT NULL DEFAULT '',
    sector_id TEXT NOT NULL REFERENCES sectors(sector_id), description_id TEXT,
    source_id TEXT NOT NULL REFERENCES data_sources(source_id),
    record_status TEXT NOT NULL CHECK(record_status IN ('draft','reviewed','published','archived')),
    last_reviewed TEXT, UNIQUE(preferred_name_id, sector_id)
);
CREATE TABLE occupation_aliases(
    alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
    occupation_id TEXT NOT NULL REFERENCES occupations(occupation_id) ON DELETE CASCADE,
    alternative_name_id TEXT NOT NULL,
    UNIQUE(occupation_id, alternative_name_id)
);
CREATE TABLE kbji_mappings(
    occupation_id TEXT NOT NULL REFERENCES occupations(occupation_id),
    kbji_edition TEXT NOT NULL, kbji_code TEXT NOT NULL, kbji_label_id TEXT NOT NULL,
    source_id TEXT NOT NULL REFERENCES data_sources(source_id),
    verified_by TEXT NOT NULL, verified_at TEXT NOT NULL,
    PRIMARY KEY(occupation_id,kbji_edition,kbji_code)
);
CREATE TABLE employment_contexts(
    context_code TEXT PRIMARY KEY,label_id TEXT NOT NULL,dimension TEXT NOT NULL
);
CREATE TABLE job_titles(
    title_id TEXT PRIMARY KEY,title_name_id TEXT NOT NULL,
    occupation_id TEXT NOT NULL REFERENCES occupations(occupation_id),
    seniority_level TEXT, context_code TEXT REFERENCES employment_contexts(context_code),notes TEXT
);
CREATE INDEX ix_occupation_sector ON occupations(sector_id);
CREATE INDEX ix_occupation_name ON occupations(preferred_name_id);
CREATE INDEX ix_kbji_mapping_code ON kbji_mappings(kbji_edition,kbji_code);
'''

TABLES = (
    ('sectors', 'data/reference/sectors.csv'),
    ('data_sources', 'data/sources.csv'),
    ('occupations', 'data/occupations.csv'),
    ('employment_contexts', 'data/reference/employment_contexts.csv'),
    ('job_titles', 'data/job_titles.csv'),
    ('kbji_mappings', 'data/kbji_mappings.csv'),
    ('jabatan_nasional','data/jabatan_nasional.csv'),
    ('wilayah_administratif','data/wilayah_administratif.csv'),
    ('pemetaan_jabatan_kbji','data/pemetaan_jabatan_kbji.csv'),
    ('kompetensi_jabatan','data/kompetensi_jabatan.csv'),
    ('upah_minimum','data/upah_minimum.csv'),
    ('statistik_upah','data/statistik_upah.csv'),
    ('kelas_gaji','data/kelas_gaji.csv'),
    ('pemetaan_internasional','data/pemetaan_internasional.csv'),
)

# Identifiers are fixed; never interpolate unexpected CSV headers as SQL.
from catalog_tables import COLUMNS


def build(db_path: Path, root=ROOT):
    errors, stats = check(root)
    if errors:
        raise ValueError('Dataset invalid:\n' + '\n'.join(errors))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix='.nor-id-', suffix='.sqlite3',
                                         dir=db_path.parent, delete=False) as handle:
            temporary = Path(handle.name)
        con = sqlite3.connect(temporary)
        try:
            con.executescript(SCHEMA)
            con.executescript((root/"schema/sqlite_tambahan.sql").read_text(encoding="utf-8"))
            for table, filename in TABLES:
                rows = read_csv(root / filename)
                if not rows:
                    continue
                cols = COLUMNS[table]
                if set(rows[0]) != set(cols):
                    raise ValueError(f"Unexpected CSV columns for {table}")
                placeholders = ','.join('?' for _ in cols)
                con.executemany(f'INSERT INTO {table} ({",".join(cols)}) VALUES ({placeholders})',
                                [tuple(r[c] if table in ('sectors','data_sources','occupations','employment_contexts','job_titles','kbji_mappings') or r[c] != '' else None for c in cols) for r in rows])
            aliases = [(r['occupation_id'], alias.strip())
                       for r in read_csv(root / 'data/occupations.csv')
                       for alias in r['alternative_names'].split('|') if alias.strip()]
            con.executemany('''INSERT INTO occupation_aliases
                (occupation_id,alternative_name_id) VALUES (?,?)''', aliases)
            # FTS5 is an optional optimization; LIKE search works without it.
            try:
                con.executescript('''
                    CREATE VIRTUAL TABLE occupations_fts USING fts5(
                        preferred_name_id,alternative_names,content=occupations,content_rowid=rowid);
                    INSERT INTO occupations_fts(occupations_fts) VALUES('rebuild');
                ''')
            except sqlite3.OperationalError:
                pass
            if con.execute('PRAGMA foreign_key_check').fetchall():
                raise ValueError('SQLite foreign key validation failed')
            con.commit()
        finally:
            con.close()
        os.replace(temporary, db_path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT/'dist/pekerjaan-indonesia.sqlite3')
    args = parser.parse_args()
    stats = build(args.output)
    print(json.dumps({'database': str(args.output), **stats}, ensure_ascii=False))


if __name__ == '__main__':
    main()
