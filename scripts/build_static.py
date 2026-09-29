#!/usr/bin/env python3
"""Build only the approved public assets, with content-specific cache keys."""
from pathlib import Path
import hashlib,shutil
root=Path(__file__).resolve().parent.parent
out=root/'public';out.mkdir(exist_ok=True);(out/'data').mkdir(exist_ok=True)
script=(root/'app.js').read_text()
for name in ['summary.json','reviewed-records.json']:
    source=root/'data'/name
    shutil.copy2(source,out/'data'/name)
    digest=hashlib.sha256(source.read_bytes()).hexdigest()[:12]
    script=script.replace("'data/"+name+"'", "'data/"+name+'?v='+digest+"'")
(out/'app.js').write_text(script)
shutil.copy2(root/'style.css',out/'style.css')
html=(root/'index.html').read_text()
for name in ['app.js','style.css']:
    digest=hashlib.sha256((out/name).read_bytes()).hexdigest()[:12]
    html=html.replace('"'+name+'"','"'+name+'?v='+digest+'"')
(out/'index.html').write_text(html)
print('Prepared approved public files with content-specific cache keys.')
