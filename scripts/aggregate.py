#!/usr/bin/env python3
"""Publishable aggregate counts only. Never exports messages, memories, or user IDs."""
import argparse, collections, datetime, gzip, importlib.util, json, pathlib
p=argparse.ArgumentParser();p.add_argument('--raw',type=pathlib.Path,default=pathlib.Path.home()/'scratch/AI_Swarm/ai-village/raw');p.add_argument('--output',type=pathlib.Path,default=pathlib.Path.home()/'scratch/AI_Swarm/ai-village/public-summary.json');a=p.parse_args()
spec=importlib.util.spec_from_file_location('dataset',pathlib.Path(__file__).with_name('dataset.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
sessions={};agents={}
with gzip.open(a.raw/'computer_use_sessions.jsonl.gz','rt') as f:
 for line in f:
  r=json.loads(line);sessions[r['id']]=r['agent_id']
with gzip.open(a.raw/'agents.jsonl.gz','rt') as f:
 for line in f:
  r=json.loads(line);agents[r['id']]={'name':r['name'],'model':r.get('model_string',''),'participating':bool(r.get('is_participating'))}
result={'version':2,'source':'aidigestorg/ai-village','built_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'revision':json.loads((a.raw/'snapshot.json').read_text())['revision'],'agents':agents,'tables':{},'scope':'Counts computed from every JSONL record. No source text or images are included.'}
for path in sorted(a.raw.glob('*.jsonl.gz')):
 name=path.name[:-9];print('Aggregating',name,flush=True);groups=collections.Counter();fields=collections.Counter();rows=0;redacted=0
 with gzip.open(path,'rt') as f:
  for line in f:
   if not line.strip():continue
   row=json.loads(line);n=m.normalized(row,sessions);agent=n['agent'] if n['agent'] in agents else ''
   # The schema's controlled categories only; do not expose arbitrary action strings.
   kind=n['kind']
   if len(kind)>80 or not all(c.isalnum() or c in '_- ' for c in kind):kind='other'
   groups[(n['date'][:10],agent,kind)]+=1;fields.update(row.keys());rows+=1;redacted+=row.get('screenshot_is_redacted') is True
 dates=collections.Counter();counts=collections.Counter();kinds=collections.Counter()
 for (day,agent,kind),count in groups.items():
  if day:dates[day]+=count
  if agent:counts[agent]+=count
  if kind:kinds[kind]+=count
 result['tables'][name]={'count':rows,'dates':dict(sorted(dates.items())),'agents':dict(counts),'kinds':dict(kinds),'fields':dict(fields),'redacted_screenshots':redacted,'groups':[[d,ag,k,c] for (d,ag,k),c in sorted(groups.items())]}
 print(name,rows,'records;',len(groups),'groups',flush=True)
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')));print('Public aggregate data ready:',a.output,flush=True)
