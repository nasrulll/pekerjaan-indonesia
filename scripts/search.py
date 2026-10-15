#!/usr/bin/env python3
"""Local CLI query for professions, names and sectors."""
import argparse
import json
import sqlite3
from pathlib import Path
from build_sqlite import ROOT


def search(db_path:Path,query:str='',sector:str='',limit:int=30):
    con=sqlite3.connect(db_path)
    con.row_factory=sqlite3.Row
    try:
        sql='''SELECT o.occupation_id, o.preferred_name_id, s.sector_name, o.record_status,
                      GROUP_CONCAT(k.kbji_code, '; ') AS kbji_verified_codes
               FROM occupations o
               JOIN sectors s ON s.sector_id=o.sector_id
               LEFT JOIN kbji_mappings k ON k.occupation_id=o.occupation_id
               WHERE (LOWER(o.preferred_name_id) LIKE LOWER(?) OR LOWER(o.alternative_names) LIKE LOWER(?))
               AND (LOWER(s.sector_name) LIKE LOWER(?) OR LOWER(s.sector_id) LIKE LOWER(?))
               GROUP BY o.occupation_id,o.preferred_name_id,s.sector_name,o.record_status
               ORDER BY o.preferred_name_id COLLATE NOCASE LIMIT ?'''
        return [dict(r) for r in con.execute(sql,(f'%{query}%',f'%{query}%',f'%{sector}%',f'%{sector}%',limit))]
    finally:con.close()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('query',nargs='?',default='')
    p.add_argument('--sector',default='')
    p.add_argument('--limit',type=int,default=30)
    p.add_argument('--db',type=Path,default=ROOT/'dist/pekerjaan-indonesia.sqlite3')
    args=p.parse_args()
    if not args.db.exists():p.error('SQLite database missing. Run python scripts/build_sqlite.py first.')
    if not (1 <= args.limit <= 1000):p.error('--limit must be between 1 and 1000')
    print(json.dumps(search(args.db,args.query,args.sector,args.limit),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
