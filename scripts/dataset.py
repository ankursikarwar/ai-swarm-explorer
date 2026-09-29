#!/usr/bin/env python3
"""Standard-library download and bounded-memory preparation of AI Village."""
import argparse, collections, datetime, getpass, gzip, hashlib, json, os, pathlib, re, urllib.request, urllib.parse, concurrent.futures
REPO='aidigestorg/ai-village'
class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new=super().redirect_request(req,fp,code,msg,headers,newurl)
        if new and urllib.parse.urlparse(newurl).netloc != urllib.parse.urlparse(req.full_url).netloc:
            new.remove_header('Authorization')
        return new
OPENER=urllib.request.build_opener(SafeRedirect())
def token_path():
    return pathlib.Path(os.environ.get('HF_TOKEN_PATH',os.path.join(os.environ.get('HF_HOME',os.path.expanduser('~/.cache/huggingface')),'token')))
def token():
    p=token_path(); return os.environ.get('HF_TOKEN') or (p.read_text().strip() if p.exists() else '')
def request(url, auth=True):
    return OPENER.open(urllib.request.Request(url,headers={'Authorization':'Bearer '+token()} if auth and token() else {}),timeout=120)
def dump(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')))
def login():
    t=getpass.getpass('Hugging Face read token (hidden): ').strip()
    os.environ['HF_TOKEN']=t
    with request('https://huggingface.co/datasets/'+REPO+'/resolve/main/agents.jsonl.gz') as r: r.read(1)
    p=token_path();p.parent.mkdir(parents=True,exist_ok=True); fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'w') as f:f.write(t)
    os.chmod(p,0o600);print('Login saved; dataset access verified.')
def download(root,images,workers=4):
    if not token():raise SystemExit('Sign in first: python3 scripts/dataset.py login')
    root.mkdir(parents=True,exist_ok=True)
    with request('https://huggingface.co/api/datasets/'+REPO) as r: meta=json.load(r)
    sha=meta['sha'];url='https://huggingface.co/api/datasets/'+REPO+'/tree/'+sha+'?recursive=true&limit=1000'
    files=[]
    while url:
        with request(url) as r:
            files.extend(x for x in json.load(r) if x['type']=='file')
            match=re.search(r'<([^>]+)>; rel="next"',r.headers.get('Link',''));url=match.group(1) if match else None
    dump(root/'snapshot.json',{'repo':REPO,'revision':sha,'files':files,'screenshots_requested':images})
    def fetch_file(item):
        name=item['path']
        if name.endswith('.tar') and not images:return
        rel=pathlib.PurePosixPath(name)
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe repository path')
        target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
        # Size alone is not enough to reuse a file from another snapshot.
        marker=target.with_name(target.name+'.revision')
        if target.exists() and target.stat().st_size==item.get('size') and marker.exists() and marker.read_text()==sha:return
        print('Downloading',name,flush=True)
        part=target.with_name(target.name+'.part')
        with request('https://huggingface.co/datasets/'+REPO+'/resolve/'+sha+'/'+urllib.parse.quote(name)) as r,part.open('wb') as f:
            while True:
                data=r.read(1024*1024)
                if not data:break
                f.write(data)
        if item.get('size') is not None and part.stat().st_size!=item['size']:raise ValueError('Incomplete download: '+name)
        part.replace(target);marker.write_text(sha)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for _ in pool.map(fetch_file,files):pass
    print('Download complete:',root)
def normalized(row, sessions=None):
    d=row.get('data') or {}
    if isinstance(d,str):
        try:d=json.loads(d)
        except ValueError:d={}
    if not isinstance(d,dict):d={}
    date=str(row.get('created_at') or row.get('timestamp') or row.get('start_time') or row.get('started_at') or '')
    return {'id':str(row.get('id','')),'date':date,'agent':str(row.get('agent_id') or row.get('agent_speaker_id') or d.get('agentId') or d.get('speakerId') or d.get('agent_id') or row.get('speaker_id') or (sessions or {}).get(row.get('session_id'), '') or ''),'kind':str(d.get('actionType') or row.get('action_type') or (row.get('agent_action') or {}).get('action','') or row.get('message_type') or row.get('speaker_type') or row.get('type') or row.get('role') or ''),'raw':row}
def prepare(root,out):
    out.mkdir(parents=True,exist_ok=True)
    if (out/'manifest.json').exists():raise SystemExit('Output already prepared. Choose a new output directory for a new snapshot.')
    manifest={'version':1,'source':REPO,'built_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tables':{},'agents':{},'revision':None}
    if (root/'snapshot.json').exists():manifest['revision']=json.loads((root/'snapshot.json').read_text())['revision']
    sessions={}
    session_file=root/'computer_use_sessions.jsonl.gz'
    if session_file.exists():
        with gzip.open(session_file,'rt') as f:
            for line in f:
                r=json.loads(line);sessions[r['id']]=r['agent_id']
    for path in sorted(root.glob('*.jsonl.gz')):
        name=path.name[:-9];print('Preparing',name,flush=True)
        chunks=[];batch=[];batch_size=0;count=0;dates=collections.Counter();agents=collections.Counter();kinds=collections.Counter();fields=collections.Counter()
        def flush():
            nonlocal batch,batch_size
            if not batch:return
            rel=name+'/'+str(len(chunks)).zfill(6)+'.json.gz'
            target=out/rel;target.parent.mkdir(parents=True,exist_ok=True)
            with gzip.open(target,'wt',compresslevel=1) as f:f.write(json.dumps(batch,ensure_ascii=False,separators=(',',':')))
            day_values=[r['date'][:10] for r in batch if r['date']]
            chunks.append({'path':rel,'count':len(batch),'from':min(day_values) if day_values else '', 'to':max(day_values) if day_values else '', 'agents':sorted(set(r['agent'] for r in batch)), 'kinds':sorted(set(r['kind'] for r in batch))});batch=[];batch_size=0
        with gzip.open(path,'rt') as f:
            for line in f:
                if not line.strip():continue
                row=json.loads(line);n=normalized(row,sessions);batch.append(n);batch_size+=len(line);count+=1;fields.update(row.keys())
                if n['date']:dates[n['date'][:10]]+=1
                if n['agent']:agents[n['agent']]+=1
                if n['kind']:kinds[n['kind']]+=1
                if name=='agents':manifest['agents'][str(row.get('id',''))]=str(row.get('name') or row.get('display_name') or row.get('id'))
                if len(batch)>=500 or batch_size>=2_000_000:flush()
        flush();manifest['tables'][name]={'count':count,'chunks':chunks,'dates':dict(sorted(dates.items())),'agents':dict(agents),'kinds':dict(kinds),'fields':dict(fields)}
    if not manifest['tables']:raise SystemExit('No .jsonl.gz tables found; download the dataset first.')
    dump(out/'manifest.json',manifest);print('Prepared',sum(t['count'] for t in manifest['tables'].values()),'records in',out)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['login','download','prepare']);p.add_argument('--raw',type=pathlib.Path,default=pathlib.Path.home()/'scratch/AI_Swarm/ai-village/raw');p.add_argument('--output',type=pathlib.Path,default=pathlib.Path.home()/'scratch/AI_Swarm/ai-village/explorer-data');p.add_argument('--with-images',action='store_true');p.add_argument('--workers',type=int,choices=range(1,9),default=4);a=p.parse_args()
    if a.action=='login':login()
    elif a.action=='download':download(a.raw,a.with_images,a.workers)
    else:prepare(a.raw,a.output)
