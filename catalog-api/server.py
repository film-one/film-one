import json, os, urllib.parse, urllib.request
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).parent
CATALOG = ROOT / "catalog.json"
TMDB_KEY = os.getenv("TMDB_API_KEY", "PUT_YOUR_TMDB_API_KEY_HERE")
ADMIN_TOKEN = os.getenv("FILM_ONE_ADMIN_TOKEN", "CHANGE_ME")
BASE = "https://api.themoviedb.org/3"
IMG = "https://image.tmdb.org/t/p/w500"

def tmdb(path, params):
    params = dict(params); params["api_key"] = TMDB_KEY; params.setdefault("language", "ru-RU")
    u = BASE + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(u, headers={"User-Agent":"film.one/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r: return json.loads(r.read().decode("utf-8"))

def load():
    try: return json.loads(CATALOG.read_text("utf-8"))
    except: return {"version":1,"items":[]}

def save(data):
    CATALOG.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw): super().__init__(*a,directory=str(ROOT),**kw)
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Cache-Control","no-store"); super().end_headers()
    def send_json(self,obj,code=200):
        b=json.dumps(obj,ensure_ascii=False).encode(); self.send_response(code); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        p=urllib.parse.urlparse(self.path); q=urllib.parse.parse_qs(p.query)
        if p.path=="/api/search":
            if q.get("token",[""])[0]!=ADMIN_TOKEN: return self.send_json({"error":"unauthorized"},401)
            if TMDB_KEY.startswith("PUT_"): return self.send_json({"error":"TMDB_API_KEY is not configured"},500)
            try:
                x=tmdb("/search/multi",{"query":q.get("q",[""])[0],"include_adult":"false"})
                out=[]
                for r in x.get("results",[]):
                    typ="series" if r.get("media_type")=="tv" else "movie"
                    title=r.get("title") or r.get("name") or ""
                    date=r.get("release_date") or r.get("first_air_date") or ""
                    out.append({"id":f"tmdb-{r.get('id')}","tmdb_id":r.get("id"),"title":title,"year":date[:4],"genre":"","rating":r.get("vote_average",0),"type":typ,"poster":(IMG+r["poster_path"] if r.get("poster_path") else ""),"description":r.get("overview","")})
                return self.send_json({"results":out})
            except Exception as e: return self.send_json({"error":str(e)},500)
        return super().do_GET()
    def do_POST(self):
        p=urllib.parse.urlparse(self.path); q=urllib.parse.parse_qs(p.query)
        if p.path!="/api/add": return self.send_json({"error":"not found"},404)
        if q.get("token",[""])[0]!=ADMIN_TOKEN: return self.send_json({"error":"unauthorized"},401)
        try:
            n=int(self.headers.get("Content-Length","0")); obj=json.loads(self.rfile.read(n)); data=load(); items=data.setdefault("items",[])
            if any(str(x.get("id"))==str(obj.get("id")) for x in items): return self.send_json({"ok":True,"message":"already exists"})
            items.append(obj); save(data); return self.send_json({"ok":True,"item":obj})
        except Exception as e: return self.send_json({"error":str(e)},500)

if __name__=="__main__":
    print("film.one catalog API: http://0.0.0.0:8080")
    print("Set TMDB_API_KEY and FILM_ONE_ADMIN_TOKEN before starting.")
    ThreadingHTTPServer(("0.0.0.0",8080),Handler).serve_forever()
