#!/usr/bin/env python3
"""Export the curated catalog and verified mappings to an API-friendly JSON array."""
import argparse
import json
from collections import defaultdict
from pathlib import Path
from validate import ROOT, check, read_csv


def export(root:Path=ROOT, output=None):
    problems,stats=check(root)
    if problems:raise ValueError('\n'.join(problems))
    sectors={r['sector_id']:r for r in read_csv(root/'data/reference/sectors.csv')}
    mappings=defaultdict(list)
    for r in read_csv(root/'data/kbji_mappings.csv'):
        mappings[r['occupation_id']].append({key:r[key] for key in ('kbji_code','kbji_edition','kbji_label_id','source_id','verified_by','verified_at')})
    result=[]
    for r in read_csv(root/'data/occupations.csv'):
        result.append({
           'id':r['occupation_id'],'name':r['preferred_name_id'],
           'aliases':[x.strip() for x in r['alternative_names'].split('|') if x.strip()],
           'sector':{'id':r['sector_id'],'name':sectors[r['sector_id']]['sector_name']},
           'description':r['description_id'] or None,
           'status':r['record_status'], 'source_id':r['source_id'],
           'kbji_mappings':mappings[r['occupation_id']],
        })
    target=output or root/'dist/occupations.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return len(result),target

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path)
    a=p.parse_args();count,path=export(output=a.output)
    print(f'Exported {count} occupations to {path}')
