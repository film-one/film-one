# film.one Catalog API

Սա ֆիլմերի/սերիալների կատալոգի փոքր API-ն է։ Այն օգտագործում է TMDB-ը **միայն մետատվյալների** համար՝ անուն, նկարագրություն, տարի, rating, poster և այլն։ Ֆիլմերի ամբողջական տեսանյութերը TMDB-ից չեն տրամադրվում։

## 1. Կարգավորում

Ստեղծիր TMDB API key և environment-ում դիր.

```bash
export TMDB_API_KEY="YOUR_TMDB_KEY"
export FILM_ONE_ADMIN_TOKEN="YOUR_LONG_RANDOM_TOKEN"
```

## 2. Գործարկել

```bash
python3 server.py
```

API-ն կլինի `http://SERVER:8080/`։ Production-ում օգտագործիր HTTPS reverse proxy (օր. Nginx/Caddy)։

## 3. Android-ում

`app/src/main/assets/config.json`-ում `catalog_url`-ը դիր `https://YOUR-DOMAIN/catalog.json`։

Admin-ը հավելվածի `Настройки → Админ-панель` բաժնում որոնում է ֆիլմը, ընտրում արդյունքը և ավելացնում կատալոգ։ Admin token-ը պետք է նույնը լինի server-ի `FILM_ONE_ADMIN_TOKEN`-ի հետ։

### Կարևոր

Admin endpoint-ը առանց authentication չթողնես։ Token-ը փոխիր իրական երկար random արժեքով և API-ն բացիր HTTPS-ով։
