# film.one

Русский Android-клиент каталога фильмов и сериалов с удалённым paginated-каталогом, TMDB metadata import и Media3 player.

## Архитектура

`TMDB API → GitHub Actions → catalog/* → GitHub Pages → Android app`

Приложение не хранит десятки тысяч карточек внутри APK. Оно загружает только нужные страницы каталога и кэширует их в памяти. Поэтому добавление новых записей в каталог не требует новой сборки APK.

### Каталог

Каталог разбит на страницы по 40 записей:

```text
catalog/index.json
catalog/new_movies/page-1.json
catalog/popular_movies/page-1.json
catalog/top_movies/page-1.json
catalog/popular_tv/page-1.json
...
```

Bulk importer использует TMDB pagination и дедупликацию по `type + tmdb_id`. По умолчанию workflow стремится к 50 000 уникальных названий; вручную можно указать до 80 000+ через `target_count`.

### TMDB secret

В repository должен существовать secret `TMDB_API_KEY`. Он используется только GitHub Actions/server-side и никогда не попадает в Android source code.

TMDB используется для metadata/artwork. Полные видеоисточники TMDB не предоставляет; `video_url` и `sources` предназначены только для разрешённых пользователем источников.

### GitHub Pages

Один раз открой:

`Settings → Pages → Build and deployment → Source → GitHub Actions`

После этого workflow `Publish Catalog` публикует `/catalog` по адресу:

`https://film-one.github.io/film-one/index.json`

### Video

Android использует AndroidX Media3 ExoPlayer. Поддержվում են MP4 и HLS/M3U8; subtitle/audio track selection зависит от того, какие tracks предоставляет конкретный source.

### Build APK

GitHub Actions → `Build APK` → `Run workflow`.

APK-ը կհայտնվի workflow-ի Artifacts բաժնում։
