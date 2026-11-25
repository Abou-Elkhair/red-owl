"""Run with python3 server.py. Local inquiries stay outside the public asset tree."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs, unquote
from email.parser import BytesParser
from email.policy import default
import mimetypes, re, sqlite3
from src.views import render

ROOT = Path(__file__).resolve().parent
class Site(SimpleHTTPRequestHandler):
    def reply(self, status, data, kind='text/html; charset=utf-8'):
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        if self.command != 'HEAD': self.wfile.write(data)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        url = urlsplit(self.path)
        path = unquote(url.path)
        if path == '/':
            self.send_response(302); self.send_header('Location','/ar/'); self.end_headers(); return
        if path.startswith('/assets/'):
            target = (ROOT / path.lstrip('/')).resolve()
            if ROOT/'assets' in target.parents and target.is_file():
                self.reply(200, target.read_bytes(), mimetypes.guess_type(target)[0] or 'application/octet-stream')
                return
        lang, _, route = path.strip('/').partition('/')
        if lang in ('en','ar'):
            try: html = render(lang,route,parse_qs(url.query))
            except KeyError: self.send_error(404); return
            self.reply(200,html.encode()); return
        self.send_error(404)

    def do_POST(self):
        if self.path != '/api/inquiry': self.send_error(404); return
        if self.headers.get('Origin') not in (None, 'http://'+self.headers.get('Host','')): self.send_error(403); return
        try: length = int(self.headers.get('Content-Length','0'))
        except ValueError: self.send_error(400); return
        if not 0 < length <= 5*1024*1024+65536: self.send_error(413); return
        mime=self.headers.get('Content-Type','')
        if not mime.startswith('multipart/form-data;'): self.send_error(415); return
        message=BytesParser(policy=default).parsebytes(('Content-Type: '+mime+'\r\n\r\n').encode()+self.rfile.read(length))
        fields={}; attachment=None
        for part in message.iter_parts():
            name=part.get_param('name',header='content-disposition')
            raw=part.get_payload(decode=True) or b''
            if name=='attachment':
                if raw and (len(raw)>5*1024*1024 or not raw.startswith(b'%PDF-')): self.send_error(400,'Invalid PDF'); return
                attachment=raw or None
            elif name in ('name','company','email','message','type','lang'):
                fields[name]=raw.decode('utf-8',errors='replace').strip()
        if any(not fields.get(k) or len(fields[k])>limit for k,limit in [('name',200),('company',200),('email',200),('message',5000)]) or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',fields['email']) or fields.get('type') not in ('project','tender','quality'): self.send_error(400,'Invalid inquiry'); return
        directory=ROOT/'local-data'; directory.mkdir(exist_ok=True)
        with sqlite3.connect(directory/'inquiries.sqlite3') as db:
            db.execute('CREATE TABLE IF NOT EXISTS inquiries (created TEXT DEFAULT CURRENT_TIMESTAMP, name TEXT, company TEXT, email TEXT, message TEXT, kind TEXT, attachment BLOB)')
            db.execute('INSERT INTO inquiries(name,company,email,message,kind,attachment) VALUES(?,?,?,?,?,?)',tuple(fields[k] for k in ('name','company','email','message','type'))+(attachment,))
        lang = 'en' if fields.get('lang')=='en' else 'ar'
        self.send_response(303); self.send_header('Location',f'/{lang}/received'); self.end_headers()
if __name__=='__main__':
    ThreadingHTTPServer(('127.0.0.1',8765),Site).serve_forever()
