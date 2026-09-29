#!/usr/bin/env python3
"""Read-only loopback server for the GitHub Pages explorer, reached over SSH."""
import argparse, datetime, http.server, json, pathlib, re, tarfile, urllib.parse, zoneinfo, socketserver, os, sqlite3
p=argparse.ArgumentParser();p.add_argument('--data',type=pathlib.Path,default=pathlib.Path.home()/'scratch/AI_Swarm/ai-village/explorer-data');p.add_argument('--raw',type=pathlib.Path,default=pathlib.Path.home()/'scratch/AI_Swarm/ai-village/raw');p.add_argument('--socket',type=pathlib.Path,default=pathlib.Path.home()/'Work/AI_Swarm/.run/explorer.sock');a=p.parse_args()
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(a.data),**kwargs)
    def address_string(self):return "ssh-tunnel"
    def end_headers(self):
        origin=self.headers.get('Origin','')
        if origin in ['https://ankursikarwar.github.io','http://127.0.0.1:8765','http://localhost:8765']:
            self.send_header('Access-Control-Allow-Origin',origin)
            self.send_header('Vary','Origin')
            self.send_header('Access-Control-Allow-Private-Network','true')
        self.send_header('Cache-Control','private, no-store');self.send_header('X-Content-Type-Options','nosniff');super().end_headers()
    def do_OPTIONS(self):
        self.send_response(204);self.send_header('Access-Control-Allow-Methods','GET, HEAD, OPTIONS');self.end_headers()
    def list_directory(self,path):self.send_error(403,'Directory listing disabled')
    def do_GET(self):
        url=urllib.parse.urlparse(self.path)
        if url.path=='/query':
            args=urllib.parse.parse_qs(url.query);get=lambda key:args.get(key,[''])[0]
            try:offset=max(0,int(get('offset') or 0))
            except ValueError:self.send_error(400);return
            db=a.data.parent/'explorer.sqlite'
            if not db.exists():self.send_error(503,'Query index is still being prepared');return
            conditions=['table_name = ?'];params=[get('table')]
            for key,col in [('agent','agent'),('kind','kind')]:
                if get(key):conditions.append(col+' = ?');params.append(get(key))
            if get('from'):conditions.append('day >= ?');params.append(get('from'))
            if get('to'):conditions.append("day != '' AND day <= ?");params.append(get('to'))
            if get('query'):conditions.append('instr(lower(record), lower(?)) > 0');params.append(get('query'))
            clause=' AND '.join(conditions)
            try:
                with sqlite3.connect('file:'+str(db)+'?mode=ro',uri=True) as con:
                    total=con.execute('SELECT count(*) FROM records WHERE '+clause,params).fetchone()[0]
                    rows=[json.loads(r[0]) for r in con.execute('SELECT record FROM records WHERE '+clause+' ORDER BY position LIMIT 50 OFFSET ?',params+[offset])]
                payload=json.dumps({'total':total,'rows':rows},ensure_ascii=False).encode()
                self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
            except sqlite3.Error:self.send_error(500,'Could not query dataset index')
            return
        if url.path=='/screenshot':
            args=urllib.parse.parse_qs(url.query);turn=args.get('id',[''])[0];day=args.get('day',[''])[0]
            if not re.fullmatch(r'[a-fA-F0-9-]{36}',turn) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',day):self.send_error(400);return
            path=a.raw/'images/computer-use-turns'/(day+'.tar')
            if not path.is_file():self.send_error(404,'Screenshot archive has not been downloaded');return
            try:
                with tarfile.open(path,'r:') as archive:
                    member=next((m for m in archive if m.name.split('/')[-1]==turn+'.png'),None)
                    if member is None or not member.isfile():self.send_error(404,'Turn has no image in this archive');return
                    if member.size>50*1024*1024:self.send_error(413);return
                    image=archive.extractfile(member).read()
                self.send_response(200);self.send_header('Content-Type','image/png');self.send_header('Content-Length',str(len(image)));self.end_headers();self.wfile.write(image)
            except (OSError,tarfile.TarError):self.send_error(500,'Cannot read screenshot archive')
            return
        path=pathlib.Path(self.translate_path(self.path)).resolve()
        if a.data.resolve() not in path.parents or not (path.name=='manifest.json' or path.name.endswith('.json.gz')):
            self.send_error(403);return
        super().do_GET()
a.socket.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
os.chmod(a.socket.parent,0o700)
if a.socket.exists():raise SystemExit('Socket already exists. Check the existing server before restarting.')
class Server(socketserver.ThreadingUnixStreamServer):
    daemon_threads=True
    allow_reuse_address=False
with Server(str(a.socket),Handler) as server:
    os.chmod(a.socket,0o600)
    print('Serving prepared data through owner-only socket: '+str(a.socket),flush=True)
    try:server.serve_forever()
    finally:a.socket.unlink(missing_ok=True)
