import json, os, time, pathlib, requests
from datetime import datetime, timezone

KEY=os.environ["TMDB_API_KEY"]
TARGET=int(os.getenv("TARGET_COUNT","50000"))
MAX_PAGES=int(os.getenv("MAX_PAGES_PER_FEED","500"))
PAGE_SIZE=40
BASE="https://api.themoviedb.org/3"
IMG="https://image.tmdb.org/t/p/"
ROOT=pathlib.Path("catalog")

session=requests.Session();session.headers.update({"Authorization":f"Bearer {KEY}","accept":"application/json"})
feeds=[
 ("new_movies","Новые фильмы","movie","/movie/now_playing",{"region":"RU"}),
 ("popular_movies","Популярные фильмы","movie","/movie/popular",{}),
 ("top_movies","Лучшие фильмы","movie","/movie/top_rated",{}),
 ("upcoming_movies","Предстоящие фильмы","movie","/movie/upcoming",{"region":"RU"}),
 ("popular_tv","Популярные сериалы","tv","/tv/popular",{}),
 ("top_tv","Лучшие сериалы","tv","/tv/top_rated",{}),
 ("airing_tv","Выходят сегодня","tv","/tv/airing_today",{"timezone":"Europe/Moscow"}),
 ("onair_tv","Сейчас в эфире","tv","/tv/on_the_air",{}),
]

def get(path,params):
    p=dict(params);p.update(language="ru-RU",include_adult="false",page=p.get("page",1))
    for attempt in range(6):
        r=session.get(BASE+path,params=p,timeout=30)
        if r.status_code==429:
            time.sleep(min(10,2**attempt));continue
        r.raise_for_status();return r.json()
    raise RuntimeError("TMDB rate limit")

def item(x,typ):
    date=x.get("release_date") or x.get("first_air_date") or ""
    title=x.get("title") or x.get("name") or ""
    original=x.get("original_title") or x.get("original_name") or ""
    return {"tmdb_id":x.get("id"),"type":typ,"title":title,"original_title":original,"year":date[:4],"rating":x.get("vote_average",0),"vote_count":x.get("vote_count",0),"overview":x.get("overview","") or "","genre":", ".join(genre_names.get(i,str(i)) for i in x.get("genre_ids",[])),"genre_ids":x.get("genre_ids",[]),"poster":IMG+"w500"+x["poster_path"] if x.get("poster_path") else "","backdrop":IMG+"w1280"+x["backdrop_path"] if x.get("backdrop_path") else "","video_url":"","sources":[],"audio":[],"subtitles":[]}

items={};section_items={s[0]:[] for s in feeds};
# Preserve existing catalog metadata such as video sources across imports.
if ROOT.exists():
    for fp in ROOT.glob("*/page-*.json"):
        try:
            old=json.loads(fp.read_text(encoding="utf-8"))
            for m in old.get("items",[]):
                k=f"{m.get('type','movie')}:{m.get('tmdb_id',m.get('id'))}"
                if k not in items: items[k]=m
        except Exception: pass
genre_names={28:"Боевик",12:"Приключения",16:"Мультфильм",35:"Комедия",80:"Криминал",99:"Документальный",18:"Драма",10751:"Семейный",14:"Фэнтези",36:"История",27:"Ужасы",10402:"Музыка",9648:"Детектив",10749:"Мелодрама",878:"Фантастика",53:"Триллер",10752:"Военный",37:"Вестерн"}
for sid,title,typ,path,params in feeds:
    seen_section=set()
    for page in range(1,MAX_PAGES+1):
        data=get(path,{**params,"page":page});results=data.get("results",[])
        if not results:break
        for x in results:
            if x.get("media_type") in ("person",):continue
            m=item(x,typ);key=f"{typ}:{m['tmdb_id']}"
            if key not in items: items[key]=m
            else:
                old=items[key]
                for keep in ("video_url","sources","audio","subtitles"):
                    if old.get(keep) and not m.get(keep): m[keep]=old.get(keep)
                items[key]=m
            if key not in seen_section:
                section_items[sid].append(m); seen_section.add(key)
        print(f"{sid}: page {page}, unique={len(items)}")
        if len(items)>=TARGET:break
        if page>=data.get("total_pages",page) or page>=500:break
        time.sleep(0.04)
    if len(items)>=TARGET:break

# compact pages by section. Each section is independently paginated, while deduplication is global by TMDB id.
for p in ROOT.rglob("*"):
    if p.is_file():p.unlink()
for sid,title,typ,path,params in feeds:
    arr=section_items[sid]
    d=ROOT/sid;d.mkdir(parents=True,exist_ok=True)
    pages=(len(arr)+PAGE_SIZE-1)//PAGE_SIZE
    for n in range(pages):
        with open(d/f"page-{n+1}.json","w",encoding="utf-8") as f:json.dump({"page":n+1,"pages":pages,"items":arr[n*PAGE_SIZE:(n+1)*PAGE_SIZE]},f,ensure_ascii=False,separators=(",",":"))

sections=[]
for sid,title,typ,path,params in feeds:
    arr=section_items[sid];pages=(len(arr)+PAGE_SIZE-1)//PAGE_SIZE
    sections.append({"id":sid,"title":title,"type":typ,"pages":pages,"path_pattern":f"{sid}/page-{{page}}.json"})
# Common genres are stable; names are localized labels used by the UI.
genres=[(28,"Боевик"),(12,"Приключения"),(16,"Мультфильм"),(35,"Комедия"),(80,"Криминал"),(99,"Документальный"),(18,"Драма"),(10751,"Семейный"),(14,"Фэнтези"),(36,"История"),(27,"Ужасы"),(10402,"Музыка"),(9648,"Детектив"),(10749,"Мелодрама"),(878,"Фантастика"),(53,"Триллер"),(10752,"Военный"),(37,"Вестерн")]
index={"version":2,"updated_at":datetime.now(timezone.utc).isoformat(),"total":len(items),"page_size":PAGE_SIZE,"sections":sections,"genres":[{"id":i,"name":n} for i,n in genres]}
(ROOT/"index.json").write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding="utf-8")
# Small static search shards: one shard per first character. This keeps search remote, fast and APK-independent.
search_root=ROOT/"search"; search_root.mkdir(parents=True,exist_ok=True)
search_map={}
for m in items.values():
    for value in (m.get("title",""),m.get("original_title","")):
        key=value.strip().casefold()[:1]
        if key: search_map.setdefault(key,[]).append({k:m.get(k,"") for k in ("tmdb_id","type","title","original_title","year","rating","poster","backdrop","overview","genre","video_url","sources","audio","subtitles")})
for key,arr in search_map.items():
    (search_root/(key+".json")).write_text(json.dumps({"items":arr},ensure_ascii=False,separators=(",",":")),encoding="utf-8")
# Keep legacy root catalog.json small and compatible.
legacy=list(items.values())[:200]
pathlib.Path("catalog.json").write_text(json.dumps(legacy,ensure_ascii=False,indent=2),encoding="utf-8")
print(f"DONE: {len(items)} unique TMDB titles")
