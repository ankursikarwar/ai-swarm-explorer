#!/usr/bin/env python3
"""Read-only loopback server for the GitHub Pages explorer, reached over SSH."""
import argparse, datetime, http.server, json, pathlib, re, tarfile, urllib.parse, zoneinfo
p=argparse.ArgumentParser();p.add_argument('--data',type=pathlib.Path,default=pathlib.Path.home()/'scratch/AI_Swarm/ai-village/explorer-data');p.add_argument('--raw',type=pathlib.Path,default=pathlib.Path.home()/'scratch/AI_Swarm/ai-village/raw');p.add_argument('--port',type=int,default=8866);a=p.parse_args()
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(a.data),**kwargs)
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
print('Serving prepared data on 127.0.0.1:'+str(a.port)+' only',flush=True)
http.server.ThreadingHTTPServer(('127.0.0.1',a.port),Handler).serve_forever()
