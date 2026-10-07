import json, os, urllib.parse, urllib.request
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT=Path(__file__).parent
CATALOG=ROOT/'catalog.json'
STATIC_CATALOG=ROOT.parent/'catalog'
TMDB_KEY=os.getenv('TMDB_API_KEY','')
ADMIN_TOKEN=os.getenv('FILM_ONE_ADMIN_TOKEN','')
BASE='https://api.themoviedb.org/3';IMG='https://image.tmdb.org/t/p/'

def tmdb(path,params):
    p=dict(params);p.setdefault('language','ru-RU')
    url=BASE+path+'?'+urllib.parse.urlencode(p)
    headers={'User-Agent':'film.one/2.0','Accept':'application/json'}
    if TMDB_KEY: headers['Authorization']='Bearer '+TMDB_KEY
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req,timeout=20) as r:return json.loads(r.read().decode('utf-8'))

def load_legacy():
    try:return json.loads(CATALOG.read_text('utf-8'))
    except:return {'version':1,'items':[]}

def save_legacy(data):CATALOG.write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf-8')

def media_item(x,typ=None):
    typ=typ or x.get('media_type') or ('tv' if x.get('name') else 'movie')
    title=x.get('title') or x.get('name') or ''
    original=x.get('original_title') or x.get('original_name') or ''
    date=x.get('release_date') or x.get('first_air_date') or ''
    return {'id':f'tmdb-{x.get("id")}','tmdb_id':x.get('id'),'type':typ,'title':title,'original_title':original,'year':date[:4],'rating':x.get('vote_average',0),'genre_ids':x.get('genre_ids',[]),'poster':IMG+'w500'+x['poster_path'] if x.get('poster_path') else '','backdrop':IMG+'w1280'+x['backdrop_path'] if x.get('backdrop_path') else '','overview':x.get('overview','') or '','video_url':'','sources':[],'audio':[],'subtitles':[]}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT.parent),**kw)
    def end_headers(self):self.send_header('Access-Control-Allow-Origin','*');self.send_header('Cache-Control','public, max-age=60');super().end_headers()
    def send_json(self,obj,code=200):
        b=json.dumps(obj,ensure_ascii=False).encode();self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
    def do_GET(self):
        p=urllib.parse.urlparse(self.path);q=urllib.parse.parse_qs(p.query)
        if p.path=='/api/search':
            query=q.get('q',[''])[0].strip()
            if not query:return self.send_json({'results':[]})
            if not TMDB_KEY:return self.send_json({'error':'TMDB_API_KEY is not configured'},500)
            try:
                x=tmdb('/search/multi',{'query':query,'include_adult':'false'})
                out=[media_item(r) for r in x.get('results',[]) if r.get('media_type') in ('movie','tv')]
                return self.send_json({'results':out})
            except Exception as e:return self.send_json({'error':str(e)},502)
        if p.path=='/api/title':
            if not TMDB_KEY:return self.send_json({'error':'TMDB_API_KEY is not configured'},500)
            try:
                typ=q.get('type',['movie'])[0];mid=int(q.get('id',['0'])[0]);ns='tv' if typ in ('tv','series') else 'movie'
                data=tmdb(f'/{ns}/{mid}',{'append_to_response':'credits','language':'ru-RU'})
                data['type']=ns;data['poster']=IMG+'w500'+data['poster_path'] if data.get('poster_path') else '';data['backdrop']=IMG+'w1280'+data['backdrop_path'] if data.get('backdrop_path') else ''
                return self.send_json(data)
            except Exception as e:return self.send_json({'error':str(e)},502)
        if p.path=='/api/admin/search':
            if q.get('token',[''])[0]!=ADMIN_TOKEN:return self.send_json({'error':'unauthorized'},401)
            query=q.get('q',[''])[0]
            try:return self.send_json({'results':[media_item(r) for r in tmdb('/search/multi',{'query':query,'include_adult':'false'}).get('results',[]) if r.get('media_type') in ('movie','tv')]})
            except Exception as e:return self.send_json({'error':str(e)},502)
        return super().do_GET()
    def do_POST(self):
        p=urllib.parse.urlparse(self.path);q=urllib.parse.parse_qs(p.query)
        if p.path!='/api/add':return self.send_json({'error':'not found'},404)
        if not ADMIN_TOKEN or q.get('token',[''])[0]!=ADMIN_TOKEN:return self.send_json({'error':'unauthorized'},401)
        try:
            n=int(self.headers.get('Content-Length','0'));obj=json.loads(self.rfile.read(n));data=load_legacy();items=data.setdefault('items',[]);tid=str(obj.get('tmdb_id') or obj.get('id'))
            if any(str(x.get('tmdb_id') or x.get('id'))==tid for x in items):return self.send_json({'ok':True,'message':'already exists'})
            items.append(obj);save_legacy(data);return self.send_json({'ok':True,'item':obj})
        except Exception as e:return self.send_json({'error':str(e)},500)

if __name__=='__main__':
    print('film.one catalog API: http://0.0.0.0:8080')
    ThreadingHTTPServer(('0.0.0.0',8080),Handler).serve_forever()
