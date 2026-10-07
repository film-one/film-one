package com.film.one;

import android.content.Context;
import org.json.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;

public final class CatalogRepository {
    public interface Callback<T> { void onResult(T value); }
    public static final class Section {
        public final String id, title, type, pattern;
        public final int pages;
        Section(String id,String title,String type,String pattern,int pages){this.id=id;this.title=title;this.type=type;this.pattern=pattern;this.pages=pages;}
    }
    private final ExecutorService executor=Executors.newFixedThreadPool(3);
    private final Map<String,List<MainActivity.Movie>> pageCache=new HashMap<>();
    private final String indexUrl;
    private final String apiBaseUrl;
    private JSONObject index;
    public CatalogRepository(Context c,String indexUrl,String apiBaseUrl){this.indexUrl=indexUrl;this.apiBaseUrl=trim(apiBaseUrl);}
    private String trim(String s){if(s==null)return "";return s.endsWith("/")?s.substring(0,s.length()-1):s;}
    private String read(String u)throws Exception{HttpURLConnection c=(HttpURLConnection)new URL(u).openConnection();c.setConnectTimeout(12000);c.setReadTimeout(20000);c.setRequestProperty("Accept","application/json");int code=c.getResponseCode();InputStream in=code>=200&&code<300?c.getInputStream():c.getErrorStream();String s=readStream(in);c.disconnect();if(code<200||code>=300)throw new IOException("HTTP "+code);return s;}
    private String readStream(InputStream in)throws Exception{if(in==null)return "";ByteArrayOutputStream o=new ByteArrayOutputStream();byte[]b=new byte[8192];int n;while((n=in.read(b))!=-1)o.write(b,0,n);return o.toString("UTF-8");}
    public void loadIndex(Callback<JSONObject> cb){executor.execute(()->{try{JSONObject x=new JSONObject(read(indexUrl));index=x;cb.onResult(x);}catch(Exception e){cb.onResult(null);}});}
    public List<Section> sections(){List<Section> out=new ArrayList<>();if(index==null)return out;JSONArray a=index.optJSONArray("sections");if(a==null)return out;for(int i=0;i<a.length();i++){JSONObject x=a.optJSONObject(i);if(x!=null)out.add(new Section(x.optString("id"),x.optString("title"),x.optString("type"),x.optString("path_pattern"),x.optInt("pages",1)));}return out;}
    public List<String> genres(){List<String>g=new ArrayList<>();if(index!=null){JSONArray a=index.optJSONArray("genres");if(a!=null)for(int i=0;i<a.length();i++){JSONObject x=a.optJSONObject(i);if(x!=null)g.add(x.optString("name"));}}return g;}
    public void loadSection(Section s,int page,Callback<List<MainActivity.Movie>> cb){String key=s.id+":"+page;synchronized(pageCache){if(pageCache.containsKey(key)){cb.onResult(pageCache.get(key));return;}}executor.execute(()->{try{String path=s.pattern.replace("{page}",String.valueOf(page));String u=resolve(indexUrl,path);JSONArray a=new JSONObject(read(u)).optJSONArray("items");List<MainActivity.Movie> list=parse(a);synchronized(pageCache){pageCache.put(key,list);}cb.onResult(list);}catch(Exception e){cb.onResult(Collections.emptyList());}});}
    private List<MainActivity.Movie> parse(JSONArray a)throws Exception{List<MainActivity.Movie>list=new ArrayList<>();if(a!=null)for(int i=0;i<a.length();i++)list.add(MainActivity.Movie.fromJson(a.getJSONObject(i)));return list;}
    private String resolve(String base,String rel){try{URL b=new URL(base);return new URL(b,rel).toString();}catch(Exception e){return rel;}}
    public void search(String q,Callback<List<MainActivity.Movie>> cb){
        executor.execute(()->{
            try{
                if(apiBaseUrl.isEmpty()){
                    String key=q.trim().toLowerCase(Locale.ROOT); if(key.isEmpty()){cb.onResult(Collections.emptyList());return;}
                    String u=resolve(indexUrl,"search/"+URLEncoder.encode(key.substring(0,1),"UTF-8")+".json");
                    JSONArray a=new JSONObject(read(u)).optJSONArray("items"); List<MainActivity.Movie> all=parse(a),out=new ArrayList<>();
                    for(MainActivity.Movie m:all){String t=(m.title+" "+m.originalTitle).toLowerCase(Locale.ROOT);if(t.contains(key))out.add(m);if(out.size()>=100)break;} cb.onResult(out);return;
                }
                String u=apiBaseUrl+"/api/search?q="+URLEncoder.encode(q,"UTF-8");JSONArray a=new JSONObject(read(u)).optJSONArray("results");cb.onResult(parse(a));
            }catch(Exception e){cb.onResult(Collections.emptyList());}
        });
    }
    public String apiBase(){return apiBaseUrl;}
    public void close(){executor.shutdownNow();}
}
