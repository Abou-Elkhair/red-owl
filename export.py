"""Generate the offline preview. Run after editing Python page templates."""
import os, re, json
from pathlib import Path
from urllib.parse import urlsplit
from src.views import render, nav
from src.content import projects, services
ROOT=Path(__file__).resolve().parent
def destination(lang,route):
    return ROOT / lang / (route.strip('/') or 'index') 
def write_page(file, lang, route):
    file.parent.mkdir(parents=True,exist_ok=True)
    html=render(lang,route,{})
    def local(match):
        attr,address=match.groups()
        url=urlsplit(address)
        if url.path.startswith('/assets/'): target=ROOT/url.path[1:]
        elif url.path.startswith(('/ar/','/en/')):
            _,locale,*parts=url.path.split('/')
            target=destination(locale,'/'.join(parts)).with_suffix('.html')
        else:return match.group()
        return f'{attr}="{os.path.relpath(target,file.parent)}'+('?' + url.query if url.query else '')+'"'
    html=re.sub(r'(src|href|poster|data-photo|data-link)="(/[^"]*)"',local,html)
    if route=='contact':
        html=html.replace('action="/api/inquiry"','data-offline="true"')
        names={k:p['name'][lang=='ar'] for k,p in projects.items()}
        html=html.replace('</form>','<script id="project-names" type="application/json">'+json.dumps(names,ensure_ascii=False)+'</script><p id="draft-message" role="status"></p></form>')
        html=html.replace('Local preview · submissions are saved on this device.','Open a draft in your email app, then send it to Red Owl.').replace('نسخة محلية · يُحفظ الطلب على هذا الجهاز.','يفتح الطلب كمسودة في بريدك لإرسالها إلى ريد أول.').replace('Save inquiry','Prepare email').replace('حفظ الطلب','تجهيز البريد')
        html=re.sub(r'<label>[^<]*(?:optional PDF|PDF اختياري)[^<]*<input type="file"[^>]*></label>','',html)
    file.write_text(html,encoding='utf8')
if __name__=='__main__':
    paths=['',*nav,*['projects/'+k for k in projects],*['services/'+k for k in services]]
    for lang in ['en','ar']:
        for route in paths:write_page(destination(lang,route).with_suffix('.html'),lang,route)
    write_page(ROOT/'index.html','ar','')
